# ChromaDB 向量数据库服务
# 开发环境：本地文件存储（PersistentClient）
# 生产环境：可切换为 ChromaDB Server 模式（HTTP 客户端）
#
# 切换方式：
#   在 .env 中设置 CHROMA_SERVER_HOST=http://chromadb:8000
#   然后启动 ChromaDB Server: chroma run --path /data/chroma --host 0.0.0.0

import os
import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from app.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

logger = logging.getLogger("contract-review.vector")


# 全局客户端（单例）
_chroma_client = None
_embedding_fn = None

# HuggingFace 镜像
_HF_MIRROR = os.environ.get("HF_ENDPOINT", "")
if _HF_MIRROR:
    os.environ.setdefault("HF_ENDPOINT", _HF_MIRROR)
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")


def get_embedding_function():
    """获取中文 Embedding 模型（单例，首次加载后缓存）"""
    global _embedding_fn
    if _embedding_fn is None:
        logger.info("正在加载 Embedding 模型: shibing624/text2vec-base-chinese")
        if _HF_MIRROR:
            logger.info("使用 HuggingFace 镜像: %s", _HF_MIRROR)
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="shibing624/text2vec-base-chinese",
        )
        logger.info("Embedding 模型加载完成")
    return _embedding_fn


def get_chroma_client():
    """
    获取 ChromaDB 客户端。

    - 开发环境（默认）：本地 PersistentClient
    - 生产环境：设置 CHROMA_SERVER_HOST 切换为 HttpClient
    """
    global _chroma_client
    if _chroma_client is None:
        server_host = os.getenv("CHROMA_SERVER_HOST", "")
        if server_host:
            # ===== 生产模式：连接独立 ChromaDB Server =====
            logger.info("ChromaDB 服务器模式: %s", server_host)
            _chroma_client = chromadb.HttpClient(
                host=server_host,
                port=int(os.getenv("CHROMA_SERVER_PORT", "8001")),
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            # ===== 开发模式：本地文件 =====
            _chroma_client = chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False),
            )
    return _chroma_client


def get_or_create_collection():
    """获取或创建向量集合"""
    client = get_chroma_client()
    ef = get_embedding_function()

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=ef,
        metadata={"description": "合同文本块向量存储（中文模型）"},
    )
    return collection


def add_contract_to_vector_store(contract_id: str, text: str) -> int:
    """将合同文本切片后存入向量数据库。返回存入的文本块数量。"""
    from app.services.text_splitter import split_contract_text

    chunks = split_contract_text(text, contract_id)

    if not chunks:
        return 0

    ids = [f"{contract_id}_{i}" for i in range(len(chunks))]
    contents = [c["content"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    collection = get_or_create_collection()
    collection.add(ids=ids, documents=contents, metadatas=metadatas)

    return len(chunks)


def search_similar_chunks(contract_id: str, query: str, top_k: int = 5) -> list[dict]:
    """根据用户问题检索合同中最相关的文本块。"""
    collection = get_or_create_collection()

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"contract_id": contract_id},
        include=["documents", "distances"],
    )

    chunks = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            distance = results["distances"][0][i] if results["distances"] else 0
            relevance = 1 / (1 + distance)
            chunks.append({
                "content": doc,
                "relevance": round(relevance, 4),
            })

    return chunks


def delete_contract_vectors(contract_id: str):
    """删除指定合同的所有向量"""
    collection = get_or_create_collection()
    try:
        collection.delete(where={"contract_id": contract_id})
    except Exception:
        pass
