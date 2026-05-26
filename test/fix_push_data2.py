import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine

async def fix():
    async with engine.begin() as conn:
        await conn.execute(text(
            "UPDATE push_logs SET wechat_data = '{\"thing1\":\"全职法师\",\"thing2\":\"更5.25\",\"thing3\":\"五月新番\",\"thing4\":\"正在热播\",\"thing5\":\"快来观看\",\"time6\":\"2026-05-25\"}', status = 0 WHERE id = 11"
        ))
        print("[OK] wechat_data 已补全6个字段，status重置为0")

asyncio.run(fix())