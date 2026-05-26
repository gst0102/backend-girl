import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from sqlalchemy import text
from app.database import engine

async def run():
    async with engine.begin() as conn:
        r = await conn.execute(text("SELECT 1 FROM kdocs_rules"))
        if not r.scalar():
            await conn.execute(text("INSERT INTO kdocs_rules (cron_expression, enabled) VALUES ('0 2,14 * * *', true)"))
            print("[OK] kdocs_rules 默认数据插入")
        r2 = await conn.execute(text("SELECT 1 FROM reserve_config WHERE config_type='official_account'"))
        if not r2.scalar():
            await conn.execute(text("INSERT INTO reserve_config (config_type, config_data) VALUES ('official_account', '{\"enabled\": false, \"name\": \"\", \"qrcode_url\": \"\"}')"))
            print("[OK] reserve_config 默认数据插入")
        for tbl in ["banners","kdocs_sources","kdocs_rules","mine_apps","reserve_config","ad_stats"]:
            r = await conn.execute(text(f"SELECT count(*) FROM {tbl}"))
            print(f"  {tbl}: {r.scalar()} rows")
asyncio.run(run())