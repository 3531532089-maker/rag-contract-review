# 文件上传 API
# 处理用户上传的合同文件：保存 → 解析 → 入库

import uuid
import asyncio
import hashlib
import logging
import aiofiles
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, MAX_FILE_SIZE_BYTES
from app.database.session import get_db
from app.dependencies.auth import require_auth
from app.models.contract import Contract
from app.schemas.contract import UploadResponse
from app.services.pdf_parser import parse_contract_file
from app.services.vector_store import add_contract_to_vector_store, delete_contract_vectors
from app.middleware.rate_limit import check_rate_limit

logger = logging.getLogger("contract-review.upload")

router = APIRouter(prefix="/api/upload", tags=["文件上传"])


@router.post("/contract", response_model=UploadResponse)
async def upload_contract(
    file: UploadFile = File(...),
    req: Request = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """上传合同文件（限流：每分钟最多 10 次）。"""
    if req:
        check_rate_limit(req, "upload")

    # ===== 第1步：文件名校验（防路径遍历） =====
    safe_filename = Path(file.filename).name  # 剥离任何目录路径
    if not safe_filename or safe_filename in (".", ".."):
        raise HTTPException(status_code=400, detail="无效的文件名")

    suffix = Path(safe_filename).suffix.lower()
    allowed_types = [".pdf", ".docx"]
    if suffix not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式 '{suffix}'。请上传 PDF 或 Word(.docx) 文件。",
        )

    # ===== 第2步：MIME 类型校验 =====
    if file.content_type and file.content_type not in (
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",  # 浏览器有时发这个
    ):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 '{file.content_type}'。请上传 PDF 或 Word(.docx) 文件。",
        )

    # ===== 第3步：检查文件大小 =====
    content = await file.read()

    if len(content) > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大支持 {max_mb}MB。",
        )

    # ===== 第4步：重复检测 =====
    file_hash = hashlib.sha256(content).hexdigest()
    existing = db.query(Contract).filter(
        Contract.content_hash == file_hash,
        Contract.is_deleted.is_(None),  # 忽略已删除的
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"该合同文件已上传过（合同ID: {existing.id}）。请勿重复上传相同文件。",
        )

    # ===== 第5步：保存文件到磁盘 =====
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{safe_filename}"
    save_path = UPLOAD_DIR / unique_name

    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    # ===== 第6步：解析文本 =====
    try:
        result = parse_contract_file(str(save_path))
        contract_text = result["text"]
        page_count = result["page_count"]
        file_type = result["file_type"]
    except ValueError as e:
        save_path.unlink(missing_ok=True)
        msg = str(e)
        if "加密" in msg or "密码" in msg:
            raise HTTPException(
                status_code=422,
                detail=f"无法解析加密的 PDF：{msg}。请先去除密码保护后重新上传。",
            )
        raise HTTPException(status_code=422, detail=f"文件解析失败: {msg}")
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"文件解析失败: {str(e)}")

    # ===== 第7步：存入数据库 =====
    contract = Contract(
        filename=safe_filename,
        file_path=str(save_path),
        content=contract_text,
        content_hash=file_hash,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    # ===== 第8步：向量化 =====
    try:
        chunk_count = await asyncio.wait_for(
            asyncio.to_thread(add_contract_to_vector_store, contract.id, contract_text),
            timeout=30.0,
        )
        vector_msg = f"，已建立向量索引（{chunk_count} 个文本块）"
    except asyncio.TimeoutError:
        vector_msg = "，向量索引建立超时（已跳过，可稍后重试）"
    except Exception as e:
        logger.warning("向量索引建立失败: %s", str(e)[:80])
        vector_msg = f"，向量索引建立失败: {str(e)[:50]}"

    # ===== 第9步：返回 =====
    preview = contract_text[:500] + "..." if len(contract_text) > 500 else contract_text

    return UploadResponse(
        contract_id=contract.id,
        filename=safe_filename,
        message=f"合同上传成功！已解析 {len(contract_text)} 个字符，共 {page_count or '?'} 页{vector_msg}",
        content_preview=preview,
    )


# ===== 合同列表（分页） =====
@router.get("/contracts")
async def list_contracts(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """查看已上传合同列表（分页，无需登录）。"""
    total = db.query(Contract).filter(Contract.is_deleted.is_(None)).count()
    contracts = (
        db.query(Contract)
        .filter(Contract.is_deleted.is_(None))
        .order_by(Contract.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "contracts": [
            {
                "id": c.id,
                "filename": c.filename,
                "contract_type": c.contract_type or "未分析",
                "risk_score": c.risk_score,
                "char_count": len(c.content) if c.content else 0,
                "created_at": c.created_at.isoformat(),
            }
            for c in contracts
        ],
    }


# ===== 合同详情 =====
@router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str, db: Session = Depends(get_db)):
    """查看单个合同的完整内容（无需登录）。"""
    # 防止路径遍历注入
    if ".." in contract_id or "/" in contract_id or "\\" in contract_id:
        raise HTTPException(status_code=400, detail="无效的合同ID")

    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.is_deleted.is_(None),
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在，请检查ID是否正确")

    return {
        "id": contract.id,
        "filename": contract.filename,
        "contract_type": contract.contract_type or "未分析",
        "risk_score": contract.risk_score,
        "content": contract.content,
        "char_count": len(contract.content) if contract.content else 0,
        "created_at": contract.created_at.isoformat(),
    }


# ===== 删除合同（软删除） =====
@router.delete("/contracts/{contract_id}")
async def delete_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """删除指定合同（软删除 + 清理文件和向量索引）。"""
    if ".." in contract_id or "/" in contract_id or "\\" in contract_id:
        raise HTTPException(status_code=400, detail="无效的合同ID")

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在，请检查ID是否正确")

    filename = contract.filename
    file_path = contract.file_path

    # 软删除
    from datetime import datetime, UTC
    contract.is_deleted = datetime.now(UTC)
    db.commit()

    # 清理原始文件
    if file_path and Path(file_path).exists():
        try:
            Path(file_path).unlink()
        except Exception as e:
            logger.warning("删除文件失败: %s", str(e)[:80])

    # 清理向量索引
    try:
        await asyncio.wait_for(
            asyncio.to_thread(delete_contract_vectors, contract_id),
            timeout=5.0,
        )
    except Exception:
        pass

    return {
        "message": f"合同 '{filename}' 已删除",
        "contract_id": contract_id,
    }
