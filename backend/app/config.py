# 后端配置管理
# 从 .env 文件读取所有配置，集中管理，避免硬编码

import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件
load_dotenv(BASE_DIR / ".env")

# ===== LLM 配置 =====
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-pro")

# ===== 管理员认证 =====
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# ===== 数据库配置 =====
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'contract_review.db'}")

# ===== 文件上传 =====
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ===== 文本切片配置 =====
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# ===== 合同审查配置 =====
# 发送给 LLM 的合同文本最大字符数（0=不限制）
REVIEW_MAX_CHARS = int(os.getenv("REVIEW_MAX_CHARS", "15000"))

# ===== ChromaDB 配置 =====
CHROMA_PERSIST_DIR = str(BASE_DIR / "chroma_db")
CHROMA_COLLECTION_NAME = "contract_chunks"

# ===== CORS 配置 =====
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

# ===== 启动时校验关键配置 =====
def validate_config():
    """校验必要的配置项，缺失则启动失败并给出清晰提示。"""
    errors = []
    if not LLM_API_KEY or LLM_API_KEY == "your-api-key-here":
        errors.append("LLM_API_KEY 未配置，请在 .env 中设置 DeepSeek API Key")
    if not ADMIN_PASSWORD_HASH:
        errors.append("ADMIN_PASSWORD_HASH 未配置，运行: python -c \"import hashlib; print(hashlib.sha256(b'密码').hexdigest())\"")
    if not JWT_SECRET:
        errors.append("JWT_SECRET 未配置，运行: python -c \"import secrets; print(secrets.token_hex(32))\"")
    if errors:
        msg = "\n  ❌ ".join(errors)
        raise RuntimeError(f"配置检查失败:\n  ❌ {msg}")
