# LLM 设置相关的请求 / 响应结构

from typing import Optional
from pydantic import BaseModel


class LlmSettings(BaseModel):
    """可运行时切换的 LLM 配置（仅含可选字段，空则跳过）"""
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None


class LlmSettingsResponse(BaseModel):
    """当前生效配置 + 每项来源（db / env）"""
    llm_model: str
    llm_base_url: str
    llm_temperature: float
    llm_max_tokens: int
    sources: dict[str, str]


class TestLlmRequest(BaseModel):
    """测试连接时可选的临时配置（不落库）"""
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
