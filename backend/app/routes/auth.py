# 认证 API 路由
# POST /api/auth/login — 管理员登录

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.services.auth_service import create_token
from app.middleware.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """管理员登录（限流：每分钟最多 5 次）。"""
    check_rate_limit(req, "login")

    try:
        token = create_token(request.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="密码错误")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return LoginResponse(token=token)
