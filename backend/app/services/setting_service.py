# LLM 设置服务 —— DB KV 覆盖优先，缺省回落 .env

import logging
from typing import Optional

from app.config import LLM_API_BASE, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from app.database.session import SessionLocal
from app.models.setting import Setting

logger = logging.getLogger("contract-review.settings")

# 可在后台运行时切换的 LLM 配置 key
LLM_SETTING_KEYS = ["llm_model", "llm_base_url", "llm_temperature", "llm_max_tokens"]

# 默认值（来自 .env / config.py）
_DEFAULTS = {
    "llm_model": LLM_MODEL,
    "llm_base_url": LLM_API_BASE,
    "llm_temperature": str(LLM_TEMPERATURE),
    "llm_max_tokens": str(LLM_MAX_TOKENS),
}

# 内存缓存：None 表示未加载；加载后为 {key: value}
_cache: Optional[dict] = None


def _load_db_overrides() -> dict:
    """从 settings 表读取 DB 覆盖值。"""
    db = SessionLocal()
    try:
        rows = db.query(Setting).filter(Setting.key.in_(LLM_SETTING_KEYS)).all()
        return {row.key: row.value for row in rows if row.value is not None}
    finally:
        db.close()


def invalidate_cache():
    """设置变更后清缓存，并让 llm_service 重建单例。"""
    global _cache
    _cache = None
    try:
        from app.services import llm_service
        llm_service.reset_llm_cache()
    except Exception:
        pass


def get_effective_llm_config() -> dict:
    """当前生效的 LLM 配置（DB 覆盖优先，否则 .env 默认）。"""
    global _cache
    if _cache is None:
        merged = dict(_DEFAULTS)
        for key, value in _load_db_overrides().items():
            merged[key] = value
        _cache = merged
    return _cache


def get_source_map() -> dict:
    """每个 key 的来源：db 或 env（供管理页展示）。"""
    db_overrides = _load_db_overrides()
    return {key: ("db" if key in db_overrides else "env") for key in LLM_SETTING_KEYS}


def update_settings(db, data: dict) -> dict:
    """upsert 给定 key，写库并失效缓存，返回新配置。"""
    for key in LLM_SETTING_KEYS:
        if key in data and data[key] is not None:
            value = str(data[key]).strip()
            if value == "":
                continue
            row = db.query(Setting).filter(Setting.key == key).first()
            if row:
                row.value = value
            else:
                db.add(Setting(key=key, value=value))
    db.commit()
    invalidate_cache()
    return get_effective_llm_config()


def reset_settings(db) -> dict:
    """删除所有 LLM DB 覆盖，回到 .env 默认。"""
    db.query(Setting).filter(Setting.key.in_(LLM_SETTING_KEYS)).delete()
    db.commit()
    invalidate_cache()
    return get_effective_llm_config()
