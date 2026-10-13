# 管理后台 —— LLM 运行时配置

import time
import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_auth
from app.middleware.rate_limit import check_rate_limit
from app.schemas.setting import LlmSettings, LlmSettingsResponse, TestLlmRequest
from app.services import setting_service
from app.services.llm_service import build_llm

logger = logging.getLogger("contract-review.settings")

router = APIRouter(prefix="/api/admin/settings", tags=["管理后台"])


def _response() -> LlmSettingsResponse:
    cfg = setting_service.get_effective_llm_config()
    return LlmSettingsResponse(
        llm_model=cfg["llm_model"],
        llm_base_url=cfg["llm_base_url"],
        llm_temperature=float(cfg["llm_temperature"]),
        llm_max_tokens=int(cfg["llm_max_tokens"]),
        sources=setting_service.get_source_map(),
    )


@router.get("", response_model=LlmSettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """读取当前生效的 LLM 配置 + 每项来源。"""
    return _response()


@router.put("", response_model=LlmSettingsResponse)
async def update_settings(
    body: LlmSettings,
    req: Request,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """更新 LLM 配置，保存后立即生效（无需重启）。"""
    check_rate_limit(req, "settings")
    data = {k: v for k, v in {
        "llm_model": body.llm_model,
        "llm_base_url": body.llm_base_url,
        "llm_temperature": body.llm_temperature,
        "llm_max_tokens": body.llm_max_tokens,
    }.items() if v is not None}
    setting_service.update_settings(db, data)
    return _response()


@router.post("/test")
async def test_connection(
    body: TestLlmRequest,
    req: Request,
    _user: dict = Depends(require_auth),
):
    """测试 LLM 连通性：用当前配置（或 body 里的临时配置）发一条 ping。"""
    check_rate_limit(req, "settings")
    cfg = setting_service.get_effective_llm_config()

    model = body.llm_model or cfg["llm_model"]
    base_url = body.llm_base_url or cfg["llm_base_url"]
    temperature = body.llm_temperature if body.llm_temperature is not None else float(cfg["llm_temperature"])
    max_tokens = body.llm_max_tokens if body.llm_max_tokens is not None else int(cfg["llm_max_tokens"])

    llm = build_llm(model=model, base_url=base_url, temperature=temperature, max_tokens=max_tokens)
    start = time.time()
    try:
        resp = llm.invoke("请只回复两个字：正常")
        elapsed = round((time.time() - start) * 1000)
        content = resp.content if hasattr(resp, "content") else str(resp)
        return {"ok": True, "elapsed_ms": elapsed, "reply": str(content)[:100], "model": model}
    except Exception as e:
        elapsed = round((time.time() - start) * 1000)
        return {"ok": False, "elapsed_ms": elapsed, "error": str(e)[:300], "model": model}


@router.post("/reset", response_model=LlmSettingsResponse)
async def reset_settings(
    req: Request,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """清除 DB 覆盖，回到 .env 默认配置。"""
    check_rate_limit(req, "settings")
    setting_service.reset_settings(db)
    return _response()
