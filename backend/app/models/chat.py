# 聊天会话与消息模型 —— 多轮对话持久化

import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, Text, DateTime, JSON

from app.database.session import Base


class ChatSession(Base):
    """聊天会话表：一次针对某个合同的多轮对话"""

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=True)  # 用第一个问题当标题
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    def __repr__(self):
        return f"<ChatSession {self.id} ({self.title})>"


class ChatMessage(Base):
    """聊天消息表：一条对话（用户提问 / AI 回答）"""

    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" / "assistant"
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # assistant 引用的合同原文片段
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    def __repr__(self):
        return f"<ChatMessage {self.role} [{self.session_id[:8]}]>"
