# 合同审查 API 路由
# POST   /api/review/{contract_id}  — 触发一键风险审查
# GET    /api/review/{contract_id}  — 查看已完成的审查结果

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import require_auth
from app.models.contract import Contract
from app.schemas.contract import ReviewResponse
from app.services.review_service import review_contract
from app.middleware.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/review", tags=["合同审查"])


@router.post("/{contract_id}", response_model=ReviewResponse)
async def trigger_review(
    contract_id: str,
    req: Request,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """触发合同风险审查（限流：每分钟最多 5 次，审查很贵）。"""
    check_rate_limit(req, "review")

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在，请检查合同ID")

    if not contract.content:
        raise HTTPException(status_code=400, detail="合同内容为空，请重新上传")

    # 异步执行审查（线程 + 超时保护）
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(review_contract, contract_id, contract.content),
            timeout=120.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="合同审查超时（超过120秒），请稍后重试")

    # 写入数据库
    from datetime import datetime, UTC
    contract.contract_type = result["contract_type"]
    contract.risk_score = result["risk_score"]
    contract.risk_analysis = {
        "summary": result["summary"],
        "risks": result["risks"],
        "raw_response": result.get("_raw_response", ""),
    }
    contract.reviewed_at = datetime.now(UTC)
    db.commit()

    return ReviewResponse(
        contract_id=result["contract_id"],
        contract_type=result["contract_type"],
        risk_score=result["risk_score"],
        summary=result["summary"],
        risks=result["risks"],
    )


@router.get("/{contract_id}", response_model=ReviewResponse)
async def get_review(contract_id: str, db: Session = Depends(get_db)):
    """查看已完成的风险审查结果（无需登录）。"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在，请检查合同ID")

    if not contract.risk_analysis:
        raise HTTPException(
            status_code=404,
            detail="该合同尚未进行风险审查。请先 POST /api/review/{contract_id} 触发审查。",
        )

    analysis = contract.risk_analysis
    return ReviewResponse(
        contract_id=contract_id,
        contract_type=contract.contract_type or "未分析",
        risk_score=contract.risk_score or 0,
        summary=analysis.get("summary", ""),
        risks=analysis.get("risks", []),
    )
