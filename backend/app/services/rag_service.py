# RAG 问答服务
# 核心逻辑：检索相关合同段落 → 组装 Prompt → 调用 LLM 生成回答

import asyncio
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from app.services.vector_store import search_similar_chunks
from app.services.llm_service import get_llm


# ===== 问答 Prompt 模板 =====
# 这个模板告诉 LLM："你是合同专家，只能根据给的合同内容回答"
QA_SYSTEM_PROMPT = """你是一位资深的合同审查律师。你的任务是根据提供的合同内容，准确回答用户的问题。

请严格遵守以下规则：
1. 只能根据下面提供的合同内容来回答，不能编造信息
2. 如果合同内容中没有相关信息，请明确说"根据合同内容，未找到相关信息"
3. 回答要具体，引用合同原文中的条款编号和内容
4. 如果发现问题或风险，请明确指出并给出修改建议
5. 使用中文回答，语言专业但易懂"""

QA_USER_PROMPT = """## 合同内容

{context}

## 用户问题

{question}

请根据上述合同内容回答用户的问题。"""


def _build_prompt(history: Optional[list[dict]] = None) -> ChatPromptTemplate:
    """组装 Prompt：把历史对话作为多轮消息插入，最后跟当前问题。

    历史消息用 HumanMessage/AIMessage（静态内容）承载，
    避免历史文本里的 {} 被 LangChain 当成模板变量解析报错。
    """
    messages: list = [("system", QA_SYSTEM_PROMPT)]
    for m in history or []:
        content = m.get("content", "")
        if not content:
            continue
        if m.get("role") == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    messages.append(("human", QA_USER_PROMPT))
    return ChatPromptTemplate.from_messages(messages)


def answer_question(contract_id: str, question: str, history: Optional[list[dict]] = None) -> dict:
    """
    RAG 问答核心方法。

    流程：
        1. 从向量库检索与问题相关的合同段落
        2. 将段落+问题+历史对话组装成 Prompt
        3. 调用 LLM 生成回答
        4. 返回回答 + 引用来源

    参数:
        contract_id: 合同ID
        question: 用户的问题
        history: 历史对话 [{"role":"user"/"assistant","content":"..."}]

    返回:
        {"answer": "AI的回答", "sources": ["原文段落1", "原文段落2", ...]}
    """
    # ===== 第1步：检索相关段落 =====
    chunks = search_similar_chunks(contract_id, question, top_k=4)

    if not chunks:
        return {
            "answer": "未能在合同中找到与您问题相关的内容。请确认合同已正确上传并索引。",
            "sources": [],
        }

    # 拼接上下文（按相关度排序）
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(f"[段落{i+1}] (相关度: {chunk['relevance']})\n{chunk['content']}")

    context = "\n\n---\n\n".join(context_parts)

    # ===== 第2步：组装 Prompt =====
    prompt = _build_prompt(history)

    # ===== 第3步：调用 LLM =====
    llm = get_llm()
    chain = prompt | llm | StrOutputParser()

    try:
        answer = chain.invoke({
            "context": context,
            "question": question,
        })
    except Exception as e:
        error_msg = str(e)
        # API Key 问题
        if "api_key" in error_msg.lower() or "auth" in error_msg.lower():
            return {
                "answer": "⚠️ LLM 未配置或 API Key 无效。请检查 LLM_API_KEY 配置。\n\n"
                          "向量检索功能正常（已找到相关段落），但需要配置大语言模型才能生成回答。",
                "sources": [c["content"][:300] for c in chunks],
            }
        # 超时、网络问题等
        if "timeout" in error_msg.lower() or "connect" in error_msg.lower():
            return {
                "answer": "⚠️ LLM 服务连接超时。请检查网络连接和 LLM_API_BASE 配置是否正确。",
                "sources": [c["content"][:300] for c in chunks],
            }
        # 其他错误也友好返回，不要裸抛 500
        return {
            "answer": f"⚠️ AI 回答生成失败，请稍后重试。\n\n错误信息: {error_msg[:200]}",
            "sources": [c["content"][:300] for c in chunks],
        }

    # ===== 第4步：返回结果 =====
    return {
        "answer": answer,
        "sources": [c["content"][:300] for c in chunks],
    }


async def answer_question_stream(contract_id: str, question: str, history: Optional[list[dict]] = None):
    """
    RAG 问答流式版：检索相关段落 → 组装 Prompt → 逐 token 流式生成。

    与 answer_question 的区别：以 SSE 流式返回，边生成边输出 token，
    先 yield 引用来源（sources），再逐 token yield 内容，最后 yield done。

    yield 事件格式（dict）：
        {"type": "sources", "sources": [...]}   # 引用来源
        {"type": "token", "content": "..."}     # 增量 token
        {"type": "error", "message": "..."}     # 错误信息
        {"type": "done"}                        # 结束标记
    """
    # ===== 第1步：检索（同步，放线程执行避免阻塞事件循环） =====
    chunks = await asyncio.to_thread(
        search_similar_chunks, contract_id, question, 4
    )
    sources = [c["content"][:300] for c in chunks]

    if not chunks:
        yield {
            "type": "token",
            "content": "未能在合同中找到与您问题相关的内容。请确认合同已正确上传并索引。",
        }
        yield {"type": "done"}
        return

    # 拼接上下文（按相关度排序）
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(f"[段落{i+1}] (相关度: {chunk['relevance']})\n{chunk['content']}")
    context = "\n\n---\n\n".join(context_parts)

    # 先返回引用来源
    yield {"type": "sources", "sources": sources}

    # ===== 第2步：组装 Prompt =====
    prompt = _build_prompt(history)

    llm = get_llm()
    chain = prompt | llm | StrOutputParser()

    # ===== 第3步：流式调用 LLM =====
    try:
        async for token in chain.astream({"context": context, "question": question}):
            if token:
                yield {"type": "token", "content": token}
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "auth" in error_msg.lower():
            yield {"type": "error",
                   "message": "LLM 未配置或 API Key 无效，请检查 LLM_API_KEY 配置。"}
        elif "timeout" in error_msg.lower() or "connect" in error_msg.lower():
            yield {"type": "error",
                   "message": "LLM 服务连接超时，请检查网络连接和 LLM_API_BASE 配置。"}
        else:
            yield {"type": "error",
                   "message": f"AI 回答生成失败，请稍后重试。错误信息: {error_msg[:200]}"}
    finally:
        yield {"type": "done"}
