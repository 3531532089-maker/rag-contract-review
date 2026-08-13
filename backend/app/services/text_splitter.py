# 文本切片服务
# 将长合同拆成小块，每块保持相对独立，又有上下文重叠

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHUNK_SIZE, CHUNK_OVERLAP


# 中文文本分隔符优先级
# 合同文本有清晰的段落结构，按这个顺序切分
CHINESE_SEPARATORS = [
    "\n\n",    # 空行（段落分隔，优先级最高）
    "\n",      # 换行
    "。",      # 句号（中文句子边界）
    "；",      # 分号
    "，",      # 逗号
    "",        # 兜底：逐字符切
]


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    获取文本切片器。

    为什么用 RecursiveCharacterTextSplitter？
    - 它按优先级依次尝试分隔符：先按空行切，不行再按换行切，不行再按句号切...
    - 这样切出来的块最大程度保持语义完整
    - 比简单按字符数硬切效果好很多
    """
    return RecursiveCharacterTextSplitter(
        separators=CHINESE_SEPARATORS,
        chunk_size=CHUNK_SIZE,        # 由 config.CHUNK_SIZE 决定（当前500）
        chunk_overlap=CHUNK_OVERLAP,  # 由 config.CHUNK_OVERLAP 决定（当前100）
        length_function=len,
        is_separator_regex=False,
    )


def split_contract_text(text: str, contract_id: str) -> list[dict]:
    """
    将合同文本切成小块。

    参数:
        text: 合同全文
        contract_id: 合同ID（用于标记每块属于哪个合同）

    返回:
        [
            {
                "content": "第一条 采购内容...",
                "metadata": {
                    "contract_id": "xxx",
                    "chunk_index": 0,
                    "source": "合同名称"
                }
            },
            ...
        ]
    """
    splitter = get_text_splitter()

    # 执行切片，返回的是 Document 对象列表
    documents = splitter.create_documents(
        texts=[text],
        metadatas=[{"contract_id": contract_id}],
    )

    # 转换为字典格式，方便后续处理
    chunks = []
    for i, doc in enumerate(documents):
        chunks.append({
            "content": doc.page_content,
            "metadata": {
                "contract_id": contract_id,
                "chunk_index": i,
                "char_count": len(doc.page_content),
            },
        })

    return chunks
