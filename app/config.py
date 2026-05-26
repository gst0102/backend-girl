import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(override=True)


class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "dev")
    DEBUG: bool = ENV == "dev"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost:5432/your_db",
    )

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    WECHAT_APP_ID: str = os.getenv("WECHAT_APP_ID", "")
    WECHAT_APP_SECRET: str = os.getenv("WECHAT_APP_SECRET", "")
    WECHAT_LOGIN_URL: str = os.getenv(
        "WECHAT_LOGIN_URL", "https://api.weixin.qq.com/sns/jscode2session"
    )

    model_config = {"env_file": ".env", "extra": "allow"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()