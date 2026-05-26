import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from sqlalchemy import text
from app.database import engine

async def run():
    async with engine.begin() as conn:
        for tbl, ddl in [
            ("banners", """CREATE TABLE IF NOT EXISTS banners (
                id BIGSERIAL PRIMARY KEY, title VARCHAR(200) NOT NULL,
                image_url VARCHAR(500) NOT NULL, link_url VARCHAR(500),
                sort_order INTEGER NOT NULL DEFAULT 0, status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)"""),
            ("kdocs_sources", """CREATE TABLE IF NOT EXISTS kdocs_sources (
                id BIGSERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL,
                url VARCHAR(500) NOT NULL, type VARCHAR(50) NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                last_sync_at TIMESTAMPTZ, last_sync_result VARCHAR(200),
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)"""),
            ("kdocs_rules", """CREATE TABLE IF NOT EXISTS kdocs_rules (
                id BIGSERIAL PRIMARY KEY,
                cron_expression VARCHAR(100) NOT NULL DEFAULT '0 2,14 * * *',
                enabled BOOLEAN NOT NULL DEFAULT TRUE, last_run_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)"""),
            ("mine_apps", """CREATE TABLE IF NOT EXISTS mine_apps (
                id BIGSERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL,
                app_id VARCHAR(100) NOT NULL, path VARCHAR(200), icon VARCHAR(200),
                sort_order INTEGER NOT NULL DEFAULT 0,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)"""),
            ("reserve_config", """CREATE TABLE IF NOT EXISTS reserve_config (
                id BIGSERIAL PRIMARY KEY, config_type VARCHAR(50) NOT NULL,
                config_data TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)"""),
            ("ad_stats", """CREATE TABLE IF NOT EXISTS ad_stats (
                id BIGSERIAL PRIMARY KEY, position VARCHAR(50) NOT NULL,
                user_id UUID, action VARCHAR(20) NOT NULL,
                estimated_revenue REAL NOT NULL DEFAULT 0,
                stats_date VARCHAR(10) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)"""),
        ]:
            try:
                await conn.execute(text(ddl))
                print(f"[OK] {tbl}")
            except Exception as e:
                print(f"[WARN] {tbl}: {e}")

        # indexes
        for idx in [
            "CREATE INDEX IF NOT EXISTS idx_mine_apps_sort ON mine_apps (sort_order)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_reserve_config_type ON reserve_config (config_type)",
            "CREATE INDEX IF NOT EXISTS idx_ad_stats_pos_date ON ad_stats (position, stats_date)",
        ]:
            try:
                await conn.execute(text(idx))
            except Exception as e:
                print(f"[WARN] index: {e}")

        # 默认数据
        try:
            await conn.execute(text("INSERT INTO kdocs_rules (cron_expression, enabled) SELECT '0 2,14 * * *', TRUE WHERE NOT EXISTS (SELECT 1 FROM kdocs_rules)"))
            print("[OK] kdocs_rules 默认数据")
        except Exception as e:
            print(f"[WARN] kdocs_rules 默认数据: {e}")

        try:
            await conn.execute(text("INSERT INTO reserve_config (config_type, config_data) SELECT 'official_account', '{\"enabled\": false, \"name\": \"\", \"qrcode_url\": \"\"}' WHERE NOT EXISTS (SELECT 1 FROM reserve_config WHERE config_type='official_account')"))
            print("[OK] reserve_config 默认数据")
        except Exception as e:
            print(f"[WARN] reserve_config 默认数据: {e}")

        print("\n=== 验证 ===")
        for tbl in ["banners","kdocs_sources","kdocs_rules","mine_apps","reserve_config","ad_stats"]:
            try:
                r = await conn.execute(text(f"SELECT count(*) FROM {tbl}"))
                print(f"  {tbl}: {r.scalar()} rows")
            except Exception as e:
                print(f"  {tbl}: ERROR - {e}")

asyncio.run(run())