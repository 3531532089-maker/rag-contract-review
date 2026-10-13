# AI 问答 API
# 用户对合同提问，RAG 检索 + LLM 回答（支持多轮会话）

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_auth
from app.models.contract import Contract
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import answer_question, answer_question_stream
from app.services.chat_history_service import (
    get_or_create_session,
    get_recent_history,
    save_message,
)
from app.middleware.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/chat", tags=["AI问答"])


def _validate_contract(db: Session, contract_id: str) -> Contract:
    """校验合同存在且有内容。"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在，请检查合同ID")
    if not contract.content:
        raise HTTPException(status_code=400, detail="合同内容为空，请重新上传")
    return contract


@router.post("", response_model=ChatResponse)
async def chat_with_contract(
    request: ChatRequest,
    req: Request,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """对指定合同进行 AI 问答（限流：每分钟最多 10 次）。"""
    check_rate_limit(req, "chat")
    _validate_contract(db, request.contract_id)

    # 会话 + 历史（先落库用户消息，再回答）
    session = get_or_create_session(
        db, request.contract_id, request.session_id, title=request.question
    )
    history = get_recent_history(db, session.id)
    save_message(db, session.id, "user", request.question)
    db.commit()

    # RAG 问答（线程执行 + 超时保护）
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                answer_question,
                request.contract_id,
                request.question,
                history,
            ),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="AI 回答超时，请稍后重试")

    save_message(db, session.id, "assistant", result["answer"], result["sources"])
    db.commit()

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=session.id,
    )


@router.post("/stream")
async def chat_with_contract_stream(
    request: ChatRequest,
    req: Request,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """对指定合同进行 AI 问答（SSE 流式输出，逐 token 推送，支持多轮会话）。"""
    check_rate_limit(req, "chat")
    _validate_contract(db, request.contract_id)

    # 会话 + 历史（先落库用户消息，再流式回答）
    session = get_or_create_session(
        db, request.contract_id, request.session_id, title=request.question
    )
    history = get_recent_history(db, session.id)
    save_message(db, session.id, "user", request.question)
    db.commit()

    # SSE 事件生成器：先推 session_id，再推 sources/token/done，结束后存 assistant 消息
    async def event_generator():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session.id}, ensure_ascii=False)}\n\n"

        full_answer = ""
        sources = []
        async for event in answer_question_stream(
            request.contract_id, request.question, history
        ):
            if event.get("type") == "sources":
                sources = event.get("sources", [])
            elif event.get("type") == "token":
                full_answer += event.get("content", "")
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        # 生成结束后保存 assistant 消息（仅当有内容）
        if full_answer:
            save_message(db, session.id, "assistant", full_answer, sources)
            db.commit()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 告知 Nginx 禁用缓冲，保证流式
        },
    )
