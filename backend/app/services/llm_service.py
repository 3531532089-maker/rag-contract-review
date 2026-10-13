# 统一 LLM 工厂 —— 消除各服务各自 new ChatOpenAI 的重复

import logging

from langchain_openai import ChatOpenAI

from app.config import LLM_API_KEY
from app.services.setting_service import get_effective_llm_config

logger = logging.getLogger("contract-review.llm")

# 全局 LLM 单例（设置变更后通过 reset_llm_cache 重建）
_llm = None


def build_llm(model: str, base_url: str, temperature: float = 0.3, max_tokens: int = 2000):
    """按给定参数构建 ChatOpenAI（兼容任意 OpenAI 接口服务）。"""
    return ChatOpenAI(
        model=model,
        api_key=LLM_API_KEY,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _build_from_config():
    cfg = get_effective_llm_config()
    return build_llm(
        model=cfg["llm_model"],
        base_url=cfg["llm_base_url"],
        temperature=float(cfg["llm_temperature"]),
        max_tokens=int(cfg["llm_max_tokens"]),
    )


def get_llm():
    """获取统一 LLM 单例（聊天用）。温度/长度取当前生效配置。"""
    global _llm
    if _llm is None:
        _llm = _build_from_config()
    return _llm


def reset_llm_cache():
    """清空单例缓存，下次调用按最新配置重建。"""
    global _llm
    _llm = None
