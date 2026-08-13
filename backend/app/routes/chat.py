# AI 问答 API
# 用户对合同提问，RAG 检索 + LLM 回答

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_auth
from app.models.contract import Contract
from app.schemas.contract import ChatRequest, ChatResponse
from app.services.rag_service import answer_question
from app.middleware.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/chat", tags=["AI问答"])


@router.post("", response_model=ChatResponse)
async def chat_with_contract(
    request: ChatRequest,
    req: Request,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """对指定合同进行 AI 问答（限流：每分钟最多 10 次）。"""
    check_rate_limit(req, "chat")

    # 验证合同
    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在，请检查合同ID")

    if not contract.content:
        raise HTTPException(status_code=400, detail="合同内容为空，请重新上传")

    # RAG 问答（线程执行 + 超时保护）
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                answer_question,
                request.contract_id,
                request.question,
            ),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="AI 回答超时，请稍后重试")

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
    )
