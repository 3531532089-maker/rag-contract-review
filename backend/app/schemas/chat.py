# 聊天相关的请求 / 响应结构

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """发送聊天消息的请求格式"""
    contract_id: str               # 要问哪个合同
    question: str                  # 用户的问题
    session_id: Optional[str] = None  # 所属会话（为空则自动新建）


class ChatResponse(BaseModel):
    """AI 问答响应"""
    answer: str
    sources: list[str] = []
    session_id: Optional[str] = None


class ChatSessionOut(BaseModel):
    """会话列表项"""
    id: str
    contract_id: str
    title: Optional[str] = None
    created_at: datetime
    message_count: int = 0


class ChatMessageOut(BaseModel):
    """会话消息"""
    id: str
    role: str
    content: str
    sources: Optional[list[str]] = None
    created_at: datetime


class SessionDetailOut(BaseModel):
    """会话详情（含消息列表）"""
    id: str
    contract_id: str
    title: Optional[str] = None
    created_at: datetime
    messages: list[ChatMessageOut] = []
