# 会话管理 API —— 多轮对话的会话列表 / 详情 / 删除

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_auth
from app.schemas.chat import ChatSessionOut, ChatMessageOut, SessionDetailOut
from app.services.chat_history_service import (
    list_sessions,
    get_session,
    get_session_messages,
    count_messages,
    delete_session,
)

router = APIRouter(prefix="/api/chat/sessions", tags=["AI问答"])


@router.get("", response_model=list[ChatSessionOut])
async def list_contract_sessions(
    contract_id: str,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """某合同的会话列表（按时间倒序）。"""
    sessions = list_sessions(db, contract_id)
    return [
        ChatSessionOut(
            id=s.id,
            contract_id=s.contract_id,
            title=s.title,
            created_at=s.created_at,
            message_count=count_messages(db, s.id),
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetailOut)
async def get_session_detail(
    session_id: str,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """会话详情（含全部消息），用于恢复历史。"""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = get_session_messages(db, session_id)
    return SessionDetailOut(
        id=session.id,
        contract_id=session.contract_id,
        title=session.title,
        created_at=session.created_at,
        messages=[
            ChatMessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/{session_id}")
async def delete_contract_session(
    session_id: str,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """删除会话（级联删除消息）。"""
    if not delete_session(db, session_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    db.commit()
    return {"message": "会话已删除", "session_id": session_id}
