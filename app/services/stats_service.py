from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import Record
from app.models.user import User


async def get_user_stats(
    db: AsyncSession,
    user_id: UUID,
    period: str = "month",
) -> dict:
    today = date.today()

    if period == "month":
        start = date(today.year, today.month, 1)
    elif period == "last_month":
        if today.month == 1:
            start = date(today.year - 1, 12, 1)
        else:
            start = date(today.year, today.month - 1, 1)
    else:
        start = date(2000, 1, 1)

    result = await db.execute(
        select(func.count())
        .select_from(Record)
        .where(
            Record.user_id == user_id,
            Record.record_type == "poop",
            Record.record_date >= start,
        )
    )
    poop_count = result.scalar() or 0

    result = await db.execute(
        select(func.avg(Record.record_value["score"].as_float()))
        .where(
            Record.user_id == user_id,
            Record.record_type == "sleep",
            Record.record_date >= start,
            Record.record_value["score"].isnot(None),
        )
    )
    avg_score = result.scalar()
    sleep_score = round(avg_score) if avg_score else 0

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    continuous_days = user.continuous_days if user else 0

    trend = await get_poop_trend(db, user_id, 7)

    result = await db.execute(
        select(func.count())
        .select_from(Record)
        .where(Record.record_type == "poop")
    )
    total_users = result.scalar() or 1

    result = await db.execute(
        select(func.count())
        .select_from(Record)
        .where(
            Record.user_id == user_id,
            Record.record_type == "poop",
        )
    )
    my_total = result.scalar() or 0

    result = await db.execute(
        select(func.count())
        .select_from(Record)
        .where(Record.record_type == "poop")
        .group_by(Record.user_id)
        .having(func.count() > my_total)
    )
    better_count = len(result.all())
    beat_users = round((1 - better_count / max(total_users, 1)) * 100)

    return {
        "poop_count": poop_count,
        "sleep_score": sleep_score,
        "continuous_days": continuous_days,
        "beat_users": beat_users,
        "trend": trend,
    }


async def get_poop_trend(
    db: AsyncSession,
    user_id: UUID,
    days: int = 7,
) -> list[int]:
    today = date.today()
    trend = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        result = await db.execute(
            select(func.count())
            .select_from(Record)
            .where(
                Record.user_id == user_id,
                Record.record_type == "poop",
                Record.record_date == d,
            )
        )
        trend.append(result.scalar() or 0)
    return trend


async def get_sleep_score_stats(
    db: AsyncSession,
    user_id: UUID,
    period: str,
) -> float:
    today = date.today()
    if period == "month":
        start = date(today.year, today.month, 1)
    elif period == "last_month":
        if today.month == 1:
            start = date(today.year - 1, 12, 1)
        else:
            start = date(today.year, today.month - 1, 1)
    else:
        start = date(2000, 1, 1)

    result = await db.execute(
        select(func.avg(Record.record_value["score"].as_float()))
        .where(
            Record.user_id == user_id,
            Record.record_type == "sleep",
            Record.record_date >= start,
            Record.record_value["score"].isnot(None),
        )
    )
    avg = result.scalar()
    return round(avg, 1) if avg else 0.0