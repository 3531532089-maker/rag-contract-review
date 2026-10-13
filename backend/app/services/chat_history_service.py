# 会话与消息持久化 —— 多轮对话历史

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.chat import ChatSession, ChatMessage

HISTORY_LIMIT = 8  # 注入 prompt 的历史消息条数上限


def get_or_create_session(
    db: Session,
    contract_id: str,
    session_id: Optional[str] = None,
    title: Optional[str] = None,
) -> ChatSession:
    """获取会话；session_id 为空或不属于该合同时新建。"""
    if session_id:
        existing = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.contract_id == contract_id)
            .first()
        )
        if existing:
            return existing
    session = ChatSession(
        id=str(uuid.uuid4()),
        contract_id=contract_id,
        title=(title[:50] if title else None),
    )
    db.add(session)
    return session


def list_sessions(db: Session, contract_id: str) -> list[ChatSession]:
    """某合同的会话列表（按时间倒序）。"""
    return (
        db.query(ChatSession)
        .filter(ChatSession.contract_id == contract_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )


def get_session(db: Session, session_id: str) -> Optional[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def get_session_messages(db: Session, session_id: str) -> list[ChatMessage]:
    """会话的全部消息（按时间正序）。"""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def count_messages(db: Session, session_id: str) -> int:
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()


def get_recent_history(db: Session, session_id: str, limit: int = HISTORY_LIMIT) -> list[dict]:
    """最近的对话历史，供注入 prompt（只保留有内容的 user/assistant）。"""
    messages = get_session_messages(db, session_id)
    history = [
        {"role": m.role, "content": m.content}
        for m in messages
        if m.role in ("user", "assistant") and m.content
    ]
    return history[-limit:]


def save_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    sources: Optional[list[str]] = None,
) -> ChatMessage:
    """保存一条消息。"""
    msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=role,
        content=content,
        sources=sources,
    )
    db.add(msg)
    return msg


def delete_session(db: Session, session_id: str) -> bool:
    """删除会话及其全部消息（级联）。"""
    session = get_session(db, session_id)
    if not session:
        return False
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    return True
