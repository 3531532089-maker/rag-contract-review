# 简单的内存限流中间件
# 生产环境建议用 Redis 替代

import time
import threading
from fastapi import HTTPException, Request

_lock = threading.Lock()
# { "ip:endpoint": [timestamp1, timestamp2, ...] }
_hits: dict[str, list[float]] = {}

# 配置
LIMITS = {
    "login": {"max": 5, "window": 60},          # 登录：每分钟最多5次
    "chat": {"max": 10, "window": 60},           # 聊天：每分钟最多10次
    "review": {"max": 5, "window": 60},          # 审查：每分钟最多5次（审查很贵）
    "upload": {"max": 10, "window": 60},         # 上传：每分钟最多10次
    "settings": {"max": 30, "window": 60},       # 管理设置：每分钟最多30次
}


def _get_client_ip(request: Request) -> str:
    """获取客户端真实 IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, category: str):
    """
    检查请求频率。超出限制则抛出 HTTP 429。

    用法（在路由函数第一行调用）:
        check_rate_limit(request, "chat")
    """
    limit = LIMITS.get(category)
    if not limit:
        return

    ip = _get_client_ip(request)
    key = f"{ip}:{category}"
    now = time.time()
    window_start = now - limit["window"]

    with _lock:
        # 清理过期记录
        if key in _hits:
            _hits[key] = [t for t in _hits[key] if t > window_start]
        else:
            _hits[key] = []

        if len(_hits[key]) >= limit["max"]:
            retry_after = int(_hits[key][0] + limit["window"] - now) + 1
            raise HTTPException(
                status_code=429,
                detail=f"请求过于频繁，请在 {retry_after} 秒后重试",
                headers={"Retry-After": str(retry_after)},
            )

        _hits[key].append(now)
