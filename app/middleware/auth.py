from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError

from app.schemas.response import CodeEnum, error_response
from app.services.auth_service import verify_jwt_token

# 精确匹配白名单
WHITELIST_EXACT = {
    "/health",
    "/api/user/login",
    "/api/rank/list",
    "/docs",
    "/openapi.json",
    "/api/calendar",
    "/api/config/reserve",
    "/redoc",
}

# 前缀匹配白名单
WHITELIST_PREFIX = ("/static", "/api/admin")


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path = request.url.path
        
        # 精确匹配或前缀匹配
        if path in WHITELIST_EXACT or path.startswith(WHITELIST_PREFIX):
            await self.app(scope, receive, send)
            return

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            response = JSONResponse(
                status_code=200,
                content=error_response(CodeEnum.AUTH_FAILED, "缺少认证 Token").model_dump(),
            )
            await response(scope, receive, send)
            return

        token = auth_header[7:]
        try:
            user_id = verify_jwt_token(token)
        except JWTError:
            response = JSONResponse(
                status_code=200,
                content=error_response(CodeEnum.AUTH_FAILED, "Token 无效或已过期").model_dump(),
            )
            await response(scope, receive, send)
            return

        request.state.user_id = user_id
        await self.app(scope, receive, send)