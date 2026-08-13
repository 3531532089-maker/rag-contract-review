# 认证依赖模块
# 提供 FastAPI 的 Depends 函数，用于保护需要登录的端点

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.services.auth_service import verify_token

# FastAPI 的 HTTPBearer 会让 Swagger 文档自动显示 Authorize 按钮
security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    FastAPI 依赖：提取并验证 JWT。

    Swagger 文档中会自动出现 🔒 Authorize 按钮。
    用户点击后输入 token（不需要加 Bearer 前缀，Swagger 会自动加），
    然后所有受保护的端点都能正常调用。

    用法：
        @router.post("/something")
        async def protected_endpoint(user: dict = Depends(require_auth)):
            ...
    """
    try:
        payload = verify_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    return payload
