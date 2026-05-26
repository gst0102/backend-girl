from datetime import date, timedelta

from sqlalchemy import select

from app.database import async_session
from app.models.config_models import ConfigPushTemplate
from app.models.record import Record
from app.models.user import User
from app.services.push_service import create_push_log

_rank_cache: list[dict] = []


async def update_rank_cache():
    global _rank_cache
    async with async_session() as db:
        result = await db.execute(
            select(User)
            .where(User.invite_count > 0)
            .order_by(User.invite_count.desc(), User.created_at.asc())
            .limit(100)
        )
        users = result.scalars().all()
        _rank_cache = [
            {
                "rank": i + 1,
                "user_id": str(u.id),
                "nickname": u.nickname,
                "avatar": u.avatar,
                "invite_count": u.invite_count,
            }
            for i, u in enumerate(users)
        ]


def get_cached_rank() -> list[dict]:
    return _rank_cache


async def send_weekly_report():
    async with async_session() as db:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        result = await db.execute(
            select(Record.user_id)
            .where(Record.record_date >= week_start, Record.record_date <= today)
            .distinct()
        )
        active_user_ids = {row[0] for row in result.all()}

        if not active_user_ids:
            return

        result = await db.execute(
            select(ConfigPushTemplate).where(ConfigPushTemplate.template_id == "msg_weekly_report")
        )
        template = result.scalar_one_or_none()
        if template is None:
            return

        for user_id in active_user_ids:
            result = await db.execute(
                select(Record)
                .where(Record.user_id == user_id, Record.record_date >= week_start, Record.record_date <= today)
                .distinct(Record.record_date)
            )
            day_count = len(result.all())

            await create_push_log(
                db,
                user_id,
                template.template_id,
                f"本周你记录了{day_count}天，继续加油！",
                template.channel,
            )

        await db.commit()