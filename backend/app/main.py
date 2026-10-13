# FastAPI 应用主入口
# 所有请求首先到达这里，然后路由到对应的处理函数

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database.session import engine, Base
from app.models import Contract  # 导入模型，确保表被注册

# ===== 日志配置（同时输出到控制台 + 文件） =====
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 根 logger
logger = logging.getLogger("contract-review")
logger.setLevel(logging.INFO)

# 格式
fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 控制台 handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(fmt)
logger.addHandler(console)

# 文件 handler（滚动：每 5MB 一个文件，保留 5 个）
file_handler = RotatingFileHandler(
    LOG_DIR / "app.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(fmt)
logger.addHandler(file_handler)


# ===== 应用生命周期 =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    Base.metadata.create_all(bind=engine, checkfirst=True)
    logger.info("数据库表已创建/确认")
    logger.info("后端已启动，访问 http://localhost:8000/docs 查看API文档")
    yield
    # 关闭时执行：清理 ChromaDB 客户端，避免锁文件残留
    logger.info("后端正在关闭...")
    try:
        from app.services.vector_store import _chroma_client
        if _chroma_client is not None:
            _chroma_client._system.stop() if hasattr(_chroma_client, '_system') else None
            logger.info("ChromaDB 客户端已关闭")
    except Exception:
        pass


# 创建 FastAPI 应用实例
app = FastAPI(
    title="智能合同审查系统 API",
    description="基于 RAG 技术的合同风险分析和智能问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

# ===== 安全响应头（Starlette BaseHTTPMiddleware）=====
from starlette.middleware.base import BaseHTTPMiddleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ===== CORS 中间件 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 根路径 —— 健康检查 =====
@app.get("/")
async def root():
    return {
        "message": "合同审查系统后端运行中 🚀",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ===== 健康检查 =====
@app.get("/health")
async def health_check():
    """系统健康检查：数据库连接、ChromaDB 状态、LLM 配置。"""
    checks = {}

    # 检查数据库
    try:
        from app.database.session import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            checks["database"] = "ok"
        finally:
            db.close()  # 确保不管成功失败都关 session
    except Exception as e:
        checks["database"] = f"error: {str(e)[:80]}"

    # 检查 ChromaDB
    try:
        from app.services.vector_store import get_or_create_collection
        get_or_create_collection()
        checks["vector_store"] = "ok"
    except Exception as e:
        checks["vector_store"] = f"error: {str(e)[:80]}"

    # 检查 LLM 配置
    from app.config import LLM_API_KEY, LLM_API_BASE, LLM_MODEL
    if LLM_API_KEY and "your-api-key" not in LLM_API_KEY:
        checks["llm"] = f"configured ({LLM_MODEL} @ {LLM_API_BASE})"
    else:
        checks["llm"] = "not configured"

    # 只有真正的 error 才算 degraded
    all_ok = all("error" not in v for v in checks.values())

    return {
        "status": "healthy" if all_ok else "degraded",
        "checks": checks,
    }


# ===== 注册路由 =====
from app.routes import upload, review, chat, auth, sessions, settings
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(review.router)
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(settings.router)
