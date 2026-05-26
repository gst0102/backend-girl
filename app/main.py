from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from sqlalchemy import text

from app.config import get_settings
from app.controllers import api_router
from app.database import async_session, engine
from app.models import Base
from app.events import register_event_handlers
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.schemas.response import CodeEnum, error_response
from app.scripts.seed_startup import seed_startup_data
from app.tasks.scheduler import shutdown_scheduler, start_scheduler
from fastapi.staticfiles import StaticFiles
settings = get_settings()

security = HTTPBearer()
# 确保目录存在
import os
os.makedirs("static/avatars", exist_ok=True)
os.makedirs("static/qrcode", exist_ok=True)
os.makedirs("static/banner", exist_ok=True)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # 自动建表（幂等，已存在的表不会重复创建）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 种子数据（幂等，已存在的记录跳过）
    async with async_session() as db:
        try:
            await seed_startup_data(db)
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"种子数据写入失败（不影响启动）: {e}")
    register_event_handlers()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="GirlBackend",
    version="1.0.0",
    description="记录生活小程序后端 API",
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="static"), name="static")
# ========== 加在这里：验证错误处理 ==========
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("=" * 50)
    print("请求体校验失败:")
    print(f"URL: {request.method} {request.url}")
    print(f"错误详情: {exc.errors()}")
    print("=" * 50)
    
    return JSONResponse(
        status_code=422,
        content={"code": 40001, "message": f"参数错误", "data": exc.errors()}
    )
# =========================================

# CORS 必须放在最外层（第一个 add_middleware），确保所有响应都带 CORS 头
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.ENV}


@app.get("/test-db")
async def test_db():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return {"status": "ok", "result": result.scalar()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content=error_response(CodeEnum.SERVER_ERROR, str(exc)).model_dump(),
    )


# ── Swagger Authorize ──────────────────────────────────
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi