import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine

WX_TPL_ID = "SSFCkERVN0YEV_zk5RFK0GpUIwAgbtHkex9P9_rbvC4"

async def setup():
    async with engine.begin() as conn:
        await conn.execute(text(
            f"UPDATE config_push_templates SET wechat_template_id = '{WX_TPL_ID}' WHERE template_id = 'msg_anime_update'"
        ))
        await conn.execute(text(
            f"UPDATE config_push_templates SET wechat_template_id = '{WX_TPL_ID}' WHERE template_id = 'msg_anime_remind'"
        ))
        print(f"[OK] 微信模板ID已设置: {WX_TPL_ID}")

        r = await conn.execute(text("SELECT id::text, nickname, openid FROM users WHERE nickname='高先生'"))
        user = r.first()
        if user:
            print(f"[OK] 找到用户: {user[1]}  ID={user[0]}  openid={user[2]}")
            uid = user[0]
            await conn.execute(text(
                f"INSERT INTO push_logs (user_id, template_id, content, channel, wechat_data, status) "
                f"VALUES ('{uid}', 'msg_anime_update', '你订阅的《全职法师》更新了：更5.25，点击查看最新资源', 'subscribe', "
                f"'{{\"thing1\":\"全职法师\",\"thing2\":\"更5.25\",\"date3\":\"2026-05-25\"}}', 0)"
            ))
            print("[OK] 测试推送已插入！")
        else:
            r2 = await conn.execute(text("SELECT id::text, nickname FROM users LIMIT 5"))
            print("[ERROR] 找不到高先生，可用用户：")
            for row in r2.all():
                print(f"  {row[0]} -> {row[1]}")

        r3 = await conn.execute(text(
            "SELECT pl.id, u.nickname, pl.template_id, pl.status, pl.channel "
            "FROM push_logs pl JOIN users u ON pl.user_id = u.id "
            "WHERE pl.status=0 ORDER BY pl.id DESC LIMIT 3"
        ))
        print("\n=== 待处理推送 ===")
        for row in r3.all():
            print(f"  id={row[0]}  user={row[1]}  template={row[2]}  status={row[3]}  channel={row[4]}")

asyncio.run(setup())