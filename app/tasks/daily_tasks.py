import logging
from datetime import date, datetime, timedelta

from sqlalchemy import select, func

from app.database import async_session
from app.models.config_models import ConfigPushTemplate
from app.models.invite import InviteRelation
from app.models.push import PushLog
from app.models.record import Record
from app.models.user import User
from app.services.push_service import send_daily_reminders as _send_daily_reminders, create_push_log

logger = logging.getLogger(__name__)


async def update_user_activity():
    """更新用户活跃度分群"""
    async with async_session() as db:
        today = date.today()
        one_day_ago = today - timedelta(days=1)
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=30)

        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            result = await db.execute(
                select(Record).where(
                    Record.user_id == user.id,
                    Record.record_date >= thirty_days_ago,
                )
            )
            records = result.scalars().all()

            if not records:
                user.activity_level = "inactive"
            elif any(r.record_date >= one_day_ago for r in records):
                user.activity_level = "active"
            elif any(r.record_date >= seven_days_ago for r in records):
                user.activity_level = "low_active"
            else:
                user.activity_level = "silent"

            db.add(user)

        await db.commit()
        logger.info("User activity levels updated")


async def check_low_activity_users():
    """检查低活跃用户，触发流失预警"""
    async with async_session() as db:
        today = date.today()
        seven_days_ago = today - timedelta(days=7)

        result = await db.execute(
            select(User).where(User.activity_level == "low_active")
        )
        low_active_users = result.scalars().all()

        result = await db.execute(
            select(ConfigPushTemplate).where(ConfigPushTemplate.template_id == "msg_low_activity")
        )
        template = result.scalar_one_or_none()
        if not template:
            logger.warning("Template not found: msg_low_activity")
            return

        for user in low_active_users:
            result = await db.execute(
                select(Record).where(
                    Record.user_id == user.id,
                    Record.record_date >= seven_days_ago,
                )
            )
            recent_records = result.scalars().all()
            if not recent_records:
                await create_push_log(
                    db,
                    user.id,
                    template.template_id,
                    template.content.format(nickname=user.nickname),
                    template.channel,
                )
                logger.info(f"Sent low activity warning to user {user.id}")

        await db.commit()
        logger.info("Low activity check completed")


async def update_continuous_days():
    async with async_session() as db:
        yesterday = date.today() - timedelta(days=1)

        result = await db.execute(
            select(Record.user_id)
            .where(Record.record_date == yesterday)
            .distinct()
        )
        active_user_ids = {row[0] for row in result.all()}

        result = await db.execute(select(User))
        all_users = result.scalars().all()

        for user in all_users:
            if user.id in active_user_ids:
                user.continuous_days += 1
            else:
                user.continuous_days = 0
            db.add(user)

        await db.commit()


async def clean_expired_invites():
    async with async_session() as db:
        cutoff = datetime.now() - timedelta(days=30)
        result = await db.execute(
            select(InviteRelation).where(InviteRelation.created_at < cutoff)
        )
        expired = result.scalars().all()
        for rel in expired:
            await db.delete(rel)
        await db.commit()


async def send_daily_reminders():
    async with async_session() as db:
        await _send_daily_reminders(db)
        await db.commit()
