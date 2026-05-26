import time
from collections import defaultdict

from fastapi import Request
from starlette.responses import JSONResponse

from app.schemas.response import CodeEnum, error_response

RATE_LIMIT_CONFIG: dict[str, tuple[int, int]] = {
    "POST /record/create": (10, 60),
    "POST /invite/create": (5, 60),
    "POST /poster/generate": (3, 60),
}

DEFAULT_LIMIT = (2, 1)


class RateLimitMiddleware:
    """速率限制中间件 - 原生 ASGI 实现，兼容 CORSMiddleware"""

    def __init__(self, app):
        self.app = app
        self._storage: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path = request.url.path

        # 健康检查和文档直接放行
        if path in {"/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}:
            await self.app(scope, receive, send)
            return

        method_path = f"{scope['method']} {path}"
        limit, window = RATE_LIMIT_CONFIG.get(method_path, (None, None))
        if limit is None:
            stripped = "/".join(path.split("/")[:3])
            generic = f"{scope['method']} {stripped}"
            limit, window = RATE_LIMIT_CONFIG.get(generic, DEFAULT_LIMIT)

        user_id = None
        if "user_id" in scope:
            user_id = scope["user_id"]
        if user_id:
            base = f"user:{user_id}"
        else:
            client = scope.get("client", ("unknown", 0))
            base = f"ip:{client[0]}"

        key = f"{base}|{method_path}"
        now = time.time()
        cutoff = now - window

        timestamps = self._storage[key]
        timestamps[:] = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= limit:
            resp = JSONResponse(
                status_code=200,
                content=error_response(CodeEnum.RATE_LIMITED, f"请 {window} 秒后重试").model_dump(),
            )
            await resp(scope, receive, send)
            return

        timestamps.append(now)
        await self.app(scope, receive, send)