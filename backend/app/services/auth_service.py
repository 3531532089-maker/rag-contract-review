# 认证服务
# 密码校验 + JWT 签发 + JWT 验证

import hashlib
import time
import jwt

from app.config import ADMIN_PASSWORD_HASH, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS


def verify_password(password: str) -> bool:
    """验证管理员密码（SHA256 比对）。"""
    if not ADMIN_PASSWORD_HASH:
        return False
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH


def create_token(password: str) -> str:
    """
    验证密码并签发 JWT。

    返回: JWT 字符串（Bearer token）
    异常: ValueError — 密码错误
    """
    if not verify_password(password):
        raise ValueError("密码错误")

    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET 未配置，请在 .env 中设置")

    now = int(time.time())
    payload = {
        "sub": "admin",
        "name": "橘",
        "iat": now,
        "exp": now + JWT_EXPIRE_HOURS * 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """
    验证 JWT 并返回 payload。

    返回: {"sub": "admin", "iat": ..., "exp": ...}
    异常: jwt.ExpiredSignatureError — 过期
          jwt.InvalidTokenError — 无效
    """
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET 未配置")
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
