"""种子脚本 - 初始化广告配置"""
import asyncio, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../..")
os.environ["ENV"] = "dev"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:w12345@127.0.0.1:5432/agent"

from sqlalchemy import select
from app.database import async_session, engine
from app.models.base import Base
from app.models.ad_config import AdConfig


DEFAULT_CONFIGS = [
    ("rewarded_video", False, "", 1),
    ("banner", False, "", 2),
    ("custom_ad", False, "", 3),
]


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        for ad_type, enabled, unit_id, sort_order in DEFAULT_CONFIGS:
            result = await db.execute(select(AdConfig).where(AdConfig.ad_type == ad_type))
            existing = result.scalar_one_or_none()
            if not existing:
                db.add(AdConfig(
                    ad_type=ad_type,
                    enabled=enabled,
                    unit_id=unit_id,
                    sort_order=sort_order,
                ))
                print(f"插入广告配置: {ad_type}")
            else:
                print(f"广告配置已存在: {ad_type}")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
