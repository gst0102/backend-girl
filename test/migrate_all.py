import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import text


async def migrate():
    async with engine.begin() as conn:
        # 重建 ad_config 表
        await conn.execute(text("DROP TABLE IF EXISTS ad_config CASCADE"))
        await conn.execute(text("""
            CREATE TABLE ad_config (
                id BIGSERIAL PRIMARY KEY,
                ad_type VARCHAR(50) NOT NULL UNIQUE,
                enabled BOOLEAN NOT NULL DEFAULT FALSE,
                unit_id VARCHAR(200),
                position VARCHAR(50),
                sort_order INTEGER DEFAULT 0,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_config_ad_type ON ad_config(ad_type)"))

        # 创建 banners 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS banners (
                id BIGSERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                image_url VARCHAR(500) NOT NULL,
                link_url VARCHAR(500),
                sort_order INTEGER NOT NULL DEFAULT 0,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 重建 kdocs_sources 表（增加 cron_expression 字段）
        await conn.execute(text("DROP TABLE IF EXISTS kdocs_sources CASCADE"))
        await conn.execute(text("""
            CREATE TABLE kdocs_sources (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                url VARCHAR(500) NOT NULL,
                type VARCHAR(50) NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                cron_expression VARCHAR(100) NOT NULL DEFAULT '0 2,14 * * *',
                last_sync_at TIMESTAMP,
                last_sync_result VARCHAR(200),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 删除 kdocs_rules 表（已废弃，每个数据源独立配置）
        await conn.execute(text("DROP TABLE IF EXISTS kdocs_rules CASCADE"))

        # 创建 mine_apps 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS mine_apps (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                app_id VARCHAR(100) NOT NULL,
                path VARCHAR(200),
                icon VARCHAR(200),
                sort_order INTEGER NOT NULL DEFAULT 0,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_mine_apps_sort ON mine_apps(sort_order)"))

        # 创建 reserve_config 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reserve_config (
                id BIGSERIAL PRIMARY KEY,
                config_type VARCHAR(50) NOT NULL UNIQUE,
                config_data TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reserve_config_type ON reserve_config(config_type)"))

        # 创建 ad_stats 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ad_stats (
                id BIGSERIAL PRIMARY KEY,
                position VARCHAR(50) NOT NULL,
                user_id UUID,
                action VARCHAR(20) NOT NULL,
                estimated_revenue DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                stats_date VARCHAR(10) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_stats_date ON ad_stats(position, stats_date)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_stats_user ON ad_stats(user_id)"))

        # 插入默认数据
        ad_types = ['rewarded_video', 'banner', 'custom_ad']
        descriptions = {
            'rewarded_video': '用户点击复制链接时播放',
            'banner': '首页底部Banner',
            'custom_ad': '番剧列表中插入卡片广告'
        }
        for ad_type in ad_types:
            await conn.execute(
                text("INSERT INTO ad_config (ad_type, enabled, unit_id, description) VALUES (:ad_type, :enabled, :unit_id, :desc) ON CONFLICT (ad_type) DO NOTHING"),
                {"ad_type": ad_type, "enabled": False, "unit_id": "", "desc": descriptions[ad_type]}
            )

        # 插入默认KDocs数据源（三个预设源）
        default_sources = [
            {"name": "影视剧", "url": "https://www.kdocs.cn/l/co72a28MWkmI", "type": "anime", "cron": "*/15 * * * *"},
            {"name": "电影", "url": "https://www.kdocs.cn/l/cmbapmIwVsfi", "type": "movie", "cron": "0 2 * * *"},
            {"name": "4K资源", "url": "https://www.kdocs.cn/l/cdv0WUisFk3x?openfrom=docs", "type": "anime_4k", "cron": "0 3 * * *"},
        ]
        for s in default_sources:
            await conn.execute(
                text("INSERT INTO kdocs_sources (name, url, type, enabled, cron_expression) VALUES (:name, :url, :type, True, :cron) ON CONFLICT DO NOTHING"),
                {"name": s["name"], "url": s["url"], "type": s["type"], "cron": s["cron"]}
            )

    print("迁移完成！所有表已创建。")


if __name__ == "__main__":
    asyncio.run(migrate())