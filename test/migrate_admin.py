import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


async def run():
    async with engine.begin() as conn:
        # 建新表
        tables = {
            "banners": """
                CREATE TABLE IF NOT EXISTS banners (
                    id BIGSERIAL NOT NULL PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    image_url VARCHAR(500) NOT NULL,
                    link_url VARCHAR(500),
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )""",
            "kdocs_sources": """
                CREATE TABLE IF NOT EXISTS kdocs_sources (
                    id BIGSERIAL NOT NULL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    url VARCHAR(500) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    last_sync_at TIMESTAMPTZ,
                    last_sync_result VARCHAR(200),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )""",
            "kdocs_rules": """
                CREATE TABLE IF NOT EXISTS kdocs_rules (
                    id BIGSERIAL NOT NULL PRIMARY KEY,
                    cron_expression VARCHAR(100) NOT NULL DEFAULT '0 2,14 * * *',
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    last_run_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )""",
            "mine_apps": """
                CREATE TABLE IF NOT EXISTS mine_apps (
                    id BIGSERIAL NOT NULL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    app_id VARCHAR(100) NOT NULL,
                    path VARCHAR(200),
                    icon VARCHAR(200),
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )""",
            "reserve_config": """
                CREATE TABLE IF NOT EXISTS reserve_config (
                    id BIGSERIAL NOT NULL PRIMARY KEY,
                    config_type VARCHAR(50) NOT NULL,
                    config_data TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )""",
            "ad_stats": """
                CREATE TABLE IF NOT EXISTS ad_stats (
                    id BIGSERIAL NOT NULL PRIMARY KEY,
                    position VARCHAR(50) NOT NULL,
                    user_id UUID,
                    action VARCHAR(20) NOT NULL,
                    estimated_revenue REAL NOT NULL DEFAULT 0,
                    stats_date VARCHAR(10) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )""",
        }

        for name, ddl in tables.items():
            # 先检查表是否存在
            r = await conn.execute(text(
                f"SELECT 1 FROM information_schema.tables WHERE table_name='{name}'"
            ))
            if r.scalar():
                print(f"[OK] {name} 已存在，跳过")
            else:
                await conn.execute(text(ddl))
                print(f"[OK] {name} 已创建")

        # 建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_mine_apps_sort ON mine_apps (sort_order)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_reserve_config_type ON reserve_config (config_type)",
            "CREATE INDEX IF NOT EXISTS idx_ad_stats_pos_date ON ad_stats (position, stats_date)",
        ]
        for idx in indexes:
            await conn.execute(text(idx))

        # 插入默认数据
        await conn.execute(text(
            "INSERT INTO kdocs_rules (cron_expression, enabled) SELECT '0 2,14 * * *', TRUE WHERE NOT EXISTS (SELECT 1 FROM kdocs_rules)"
        ))
        await conn.execute(text(
            "INSERT INTO reserve_config (config_type, config_data) SELECT 'official_account', '{\"enabled\":false,\"name\":\"\",\"qrcode_url\":\"\"}' WHERE NOT EXISTS (SELECT 1 FROM reserve_config WHERE config_type='official_account')"
        ))

        print("\n[OK] 所有新表创建完成！")

        # 验证
        for name in tables.keys():
            r = await conn.execute(text(f"SELECT count(*) FROM {name}"))
            print(f"  {name}: {r.scalar()} rows")

asyncio.run(run())