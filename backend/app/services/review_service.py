# 合同风险审查服务

import json
import re
import logging

from app.config import LLM_API_KEY, LLM_API_BASE, LLM_MODEL, REVIEW_MAX_CHARS
from app.services.vector_store import search_similar_chunks
from app.services.rag_service import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger("contract-review.review")

# ===== 审查 Prompt =====
REVIEW_SYSTEM_PROMPT = """你是一位拥有20年经验的资深合同审查律师，精通中国《民法典》《劳动合同法》《公司法》及相关司法解释。

你的任务是：对提供的合同文本进行全面、系统的法律风险审查，并以 JSON 格式输出结果。

## 审查维度
请从以下 ⚠️ 8 个维度 ⚠️ 逐一扫描合同（缺一不可）：

1. **合同主体**：签约方是否明确（名称、统一社会信用代码/身份证号、地址）？是否存在主体资格问题？
2. **核心义务**：双方权利义务是否对等？是否有单方面加重对方义务的条款？
3. **价款与支付**：金额是否明确？支付条件、时间、方式是否清晰？是否存在模糊的调价条款？
4. **履约期限与方式**：期限是否合理？是否存在不合理的单方延期权？
5. **违约责任**：违约金是否过高/过低？违约情形是否覆盖全面？是否存在不平等的单向违约条款？
6. **知识产权与保密**：知识产权归属是否明确？保密义务是否合理？
7. **合同终止与解除**：解除条件是否合法（如《劳动合同法》第37-40条）？是否存在不合理的通知期或违约金？
8. **争议解决**：管辖约定是否对己方有利？是否约定了仲裁或诉讼？

## 输出格式（严格的 JSON）
```json
{{
  "contract_type": "合同类型（如：劳动合同、采购合同、保密协议 等）",
  "risk_score": 65,
  "summary": "3-5句话的总体评价",
  "risks": [
    {{
      "risk_level": "high",
      "clause": "试用期条款",
      "original_text": "合同原文中涉及试用期的具体文字",
      "reason": "违反《劳动合同法》第19条...",
      "suggestion": "将试用期缩短至不超过6个月..."
    }}
  ]
}}
```

## 硬性规则
- `risk_level` 只能是 "high"、"medium"、"low"
- `risk_score` 0-100 的整数
- `original_text` 必须来自合同原文
- **只输出 JSON，不要输出其他文字**"""

REVIEW_USER_PROMPT = """## 合同全文

{full_text}

## 相关条款段落（AI 检索出的关键部分）

{context}

请按指定的 8 个维度完成全面审查，输出 JSON。"""

# 多角度检索查询
RISK_SEARCH_QUERIES = [
    "违约责任 违约金 赔偿",
    "付款方式 支付条件 价款",
    "合同解除 终止条件 通知期",
    "知识产权 保密 竞业限制",
    "争议解决 管辖 仲裁 诉讼",
    "试用期 工资 社保 公积金 加班",
    "权利义务 单方变更 调岗调薪",
    "合同期限 履行方式 交付",
]


def _extract_json(text: str) -> dict:
    """从 LLM 返回中提取 JSON，处理常见格式问题。"""
    # 去 ```json ... ``` 包裹
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        text = match.group(1)

    # 找 JSON 块
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end > start:
        text = text[start:end + 1]

    # 去行尾注释（保留 https://）
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        in_string = False
        for i, ch in enumerate(line):
            if ch == '"' and (i == 0 or line[i-1] != '\\'):
                in_string = not in_string
            if not in_string and i < len(line) - 1 and line[i:i+2] == '//':
                line = line[:i].rstrip()
                break
        cleaned.append(line)
    text = '\n'.join(cleaned)
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)

    return json.loads(text)


def review_contract(contract_id: str, contract_text: str) -> dict:
    """
    一键合同风险审查。多角度 RAG 检索 + LLM 结构化分析。
    """
    # ===== 第1步：多角度检索 =====
    seen_contents = set()
    all_chunks = []

    for query in RISK_SEARCH_QUERIES:
        try:
            chunks = search_similar_chunks(contract_id, query, top_k=2)
            for chunk in chunks:
                key = chunk["content"][:100]
                if key not in seen_contents:
                    seen_contents.add(key)
                    all_chunks.append(chunk)
        except Exception as e:
            logger.warning("检索 '%s' 失败: %s", query, str(e)[:80])

    # 拼接上下文
    if all_chunks:
        context_parts = []
        for i, chunk in enumerate(all_chunks):
            context_parts.append(
                f"[检索块{i+1}] (相关度: {chunk.get('relevance', '?')})\n{chunk['content']}"
            )
        context = "\n\n---\n\n".join(context_parts)
    else:
        context = "（向量检索暂无结果，以合同全文为准）\n" + contract_text[:3000]

    # ===== 第2步：组装 Prompt =====
    # 按配置截断全文（0=不限制）
    full_text = contract_text if REVIEW_MAX_CHARS <= 0 else contract_text[:REVIEW_MAX_CHARS]
    if REVIEW_MAX_CHARS > 0 and len(contract_text) > REVIEW_MAX_CHARS:
        logger.info("合同文本被截断: %d → %d 字符", len(contract_text), REVIEW_MAX_CHARS)

    prompt = ChatPromptTemplate.from_messages([
        ("system", REVIEW_SYSTEM_PROMPT),
        ("user", REVIEW_USER_PROMPT),
    ])

    # 使用统一的 LLM 单例（审查需要更长的 max_tokens）
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_API_BASE,
        temperature=0.2,
        max_tokens=4000,
    )

    chain = prompt | llm | StrOutputParser()

    # ===== 第3步：调用 LLM（含重试） =====
    MAX_RETRIES = 2
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            raw_response = chain.invoke({
                "full_text": full_text,
                "context": context,
            })
            break
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                logger.warning("LLM 调用失败 (第%d次), 重试中...", attempt + 1)
            else:
                logger.error("LLM 调用最终失败: %s", str(e)[:200])
                return {
                    "contract_id": contract_id,
                    "contract_type": "审查失败",
                    "risk_score": 0,
                    "summary": f"AI 审查服务暂时不可用: {str(e)[:200]}",
                    "risks": [],
                    "_raw_response": "",
                }

    # ===== 第4步：解析 JSON =====
    try:
        result = _extract_json(raw_response)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("JSON 解析失败: %s", str(e)[:100])
        result = {
            "contract_type": "解析失败",
            "risk_score": 0,
            "summary": f"JSON 解析失败: {str(e)}\n\n原始输出(前500字):\n{raw_response[:500]}",
            "risks": [],
        }

    # ===== 第5步：规范化 =====
    contract_type = result.get("contract_type", "未知")
    risk_score = float(result.get("risk_score", 0))
    risk_score = max(0.0, min(100.0, risk_score))
    summary = result.get("summary", "")
    risks = result.get("risks", [])

    for risk in risks:
        risk.setdefault("risk_level", "medium")
        risk.setdefault("clause", "")
        risk.setdefault("original_text", "")
        risk.setdefault("reason", "")
        risk.setdefault("suggestion", "")
        if risk["risk_level"] not in ("high", "medium", "low"):
            risk["risk_level"] = "medium"

    return {
        "contract_id": contract_id,
        "contract_type": contract_type,
        "risk_score": risk_score,
        "summary": summary,
        "risks": risks,
        "_raw_response": raw_response,
    }
