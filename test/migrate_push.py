import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


async def run():
    async with engine.begin() as conn:
        for tbl, col, typ in [
            ("push_logs", "wechat_data", "TEXT"),
            ("config_push_templates", "wechat_template_id", "VARCHAR(100)"),
            ("config_push_templates", "wechat_keywords", "TEXT"),
        ]:
            try:
                await conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col} {typ}"))
                print(f"[OK] {tbl}.{col} added")
            except Exception as e:
                print(f"[WARN] {tbl}.{col}: {e}")

        templates = [
            ("msg_anime_update", "追番更新提醒", "你订阅的《{anime_title}》更新了：{episode}，点击查看最新资源", "subscribe",
             '{"thing1":"{anime_title}","thing2":"{episode}","date3":"{update_time}"}'),
            ("msg_anime_remind", "剧集催更提醒", "你催更的《{anime_title}》有新资源了：{episode}，快来看看吧", "subscribe",
             '{"thing1":"{anime_title}","thing2":"{episode}","date3":"{update_time}"}'),
            ("msg_daily_reminder", "每日打卡提醒", "亲爱的，今天还没有记录哦，快来打卡吧~", "subscribe",
             '{"thing1":"今日打卡提醒","date3":"{today}"}'),
        ]
        for tid, title, content, channel, kw in templates:
            r = await conn.execute(
                text(f"SELECT 1 FROM config_push_templates WHERE template_id='{tid}'")
            )
            if not r.scalar():
                await conn.execute(text(
                    f"INSERT INTO config_push_templates (template_id, title, content, channel, wechat_keywords) "
                    f"VALUES ('{tid}', '{title}', '{content}', '{channel}', '{kw}')"
                ))
                print(f"[OK] template {tid} inserted")
            else:
                print(f"[SKIP] template {tid} exists")

        r = await conn.execute(text(
            "SELECT template_id, channel, wechat_template_id, wechat_keywords FROM config_push_templates"
        ))
        print("\n=== Final templates ===")
        for row in r.all():
            print(f"  {row[0]:25s} channel={row[1]:10s} wx_tpl={row[2]}   kw={str(row[3])[:40]}")


asyncio.run(run())