import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine

async def check():
    async with engine.begin() as conn:
        # 1. 查用户
        r1 = await conn.execute(text("SELECT id::text, nickname, openid FROM users ORDER BY created_at DESC LIMIT 5"))
        print("=== 用户列表（前5） ===")
        for row in r1.all():
            print(f"  ID: {row[0]}, 昵称: {row[1]}, openid: {row[2]}")
        
        # 2. 查推送模板
        r2 = await conn.execute(text("SELECT * FROM config_push_templates"))
        print("\n=== 推送模板 ===")
        rows2 = r2.all()
        if rows2:
            for row in rows2:
                print(f"  template_id: {row[1]}, 标题: {row[2]}, 内容: {row[3][:50]}..., 渠道: {row[4]}")
        else:
            print("  (空)")
        
        # 3. 查推送记录
        r3 = await conn.execute(text("SELECT count(*) FROM push_logs"))
        cnt = r3.scalar()
        print(f"\n=== 推送记录数: {cnt} ===")
        if cnt > 0:
            r3b = await conn.execute(text("SELECT * FROM push_logs ORDER BY created_at DESC LIMIT 3"))
            for row in r3b.all():
                print(f"  ID: {row[0]}, 用户: {row[1]}, 模板: {row[2]}, 状态: {row[5]}, 渠道: {row[4]}")

asyncio.run(check())