import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine

async def fix():
    async with engine.begin() as conn:
        await conn.execute(text(
            "UPDATE push_logs SET wechat_data = '{\"thing1\":\"全职法师\",\"thing2\":\"更5.25\",\"thing3\":\"五月新番\",\"thing4\":\"正在热播\",\"thing5\":\"快来观看\"}', status = 0 WHERE id = 11"
        ))
        print("[OK] wechat_data 已补全5个字段，status重置为0")

        r = await conn.execute(text("SELECT id, status, wechat_data FROM push_logs WHERE id=11"))
        row = r.first()
        print(f"  当前状态: id={row[0]} status={row[1]} data={row[2]}")

asyncio.run(fix())