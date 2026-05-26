from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badge import Badge, UserBadge
from app.models.feature import UserFeature
from app.models.record import Record
from app.models.user import User
from app.events.base import event_bus
from app.utils.calendar_helper import get_period_day_count

BASE_FEATURES = ["poop", "period"]
BADGE_THRESHOLDS = [7, 14, 30]

# 一天只能记录一次的类型
SINGLE_PER_DAY_TYPES = ["period", "sleep", "mood", "weight", "medicine"]

async def create_record(
    db: AsyncSession,
    user_id: UUID,
    record_type: str,
    record_date: date,
    record_value: dict | None,
) -> tuple[int, int]:
    # 功能解锁检查
    feature = await db.execute(
        select(UserFeature).where(
            UserFeature.user_id == user_id,
            UserFeature.feature_key == record_type,
        )
    )
    if feature.scalar_one_or_none() is None:
        raise ValueError("FEATURE_LOCKED")

    # # 一天只能记录一次的类型检查
    # if record_type in SINGLE_PER_DAY_TYPES:
    #     existing = await db.execute(
    #         select(Record).where(
    #             Record.user_id == user_id,
    #             Record.record_type == record_type,
    #             Record.record_date == record_date,
    #         )
    #     )
    #     if existing.scalar_one_or_none() is not None:
    #         raise ValueError("RECORD_EXISTS")

    # 创建记录
    record = Record(
        user_id=user_id,
        record_type=record_type,
        record_date=record_date,
        record_value=record_value,
    )
    db.add(record)

    # 更新用户 last_record_at
    user = await db.get(User, user_id)
    user.last_record_at = datetime.now()
    
    # 只有拉屎才增加连续记录天数
    if record_type == "poop":
        user.continuous_days += 1
    else:
        # 其他类型不增加连续记录天数
        pass

    await db.flush()

    await event_bus.publish("record_created", {
        "user_id": str(user_id),
        "record_type": record_type,
        "continuous_days": user.continuous_days,
    })

    return record.id, user.continuous_days

# 其余代码不变...


async def check_badges(db: AsyncSession, user_id: UUID, continuous_days: int) -> list[dict]:
    earned = []
    if continuous_days not in BADGE_THRESHOLDS:
        return earned

    result = await db.execute(
        select(Badge).where(
            Badge.condition_type == "continuous_days",
            Badge.condition_value == continuous_days,
        )
    )
    badge = result.scalar_one_or_none()
    if badge is None:
        return earned

    existing = await db.execute(
        select(UserBadge).where(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge.id,
        )
    )
    if existing.scalar_one_or_none() is None:
        user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
        db.add(user_badge)
        earned.append({
            "id": badge.id,
            "name": badge.name,
            "icon": badge.icon,
            "rarity": badge.rarity,
        })

    return earned


async def get_calendar_data(
    db: AsyncSession,
    user_id: UUID,
    year: int,
    month: int,
) -> dict:
    from app.utils.calendar_helper import get_month_days, is_today

    start_date = date(year, month, 1)
    last_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1)
    else:
        last_day = date(year, month + 1, 1)

    result = await db.execute(
        select(Record).where(
            Record.user_id == user_id,
            Record.record_date >= start_date,
            Record.record_date < last_day,
        ).order_by(Record.record_date)
    )
    records = result.scalars().all()

    records_map: dict[str, list[str]] = {}
    date_has_record: set[str] = set()
    for r in records:
        key = r.record_date.isoformat()
        date_has_record.add(key)
        if key not in records_map:
            records_map[key] = []
        records_map[key].append(r.record_type)

    today = date.today()
    days = get_month_days(year, month)
    for d in days:
        if d["date"] in date_has_record:
            d["has_record"] = True
        if is_today(date.fromisoformat(d["date"])):
            d["is_today"] = True

    return {
        "year": year,
        "month": month,
        "today": today.day if today.year == year and today.month == month else 0,
        "record_days": sorted([date.fromisoformat(d).day for d in date_has_record]),
        "days": days,
        "records_map": records_map,
    }


ALL_FEATURE_TYPES = ["poop", "period", "sleep", "water", "mood", "exercise", "weight"]


async def get_today_status(db: AsyncSession, user_id: UUID) -> dict:
    today = date.today()

    # 获取用户解锁的功能
    features_result = await db.execute(
        select(UserFeature).where(UserFeature.user_id == user_id)
    )
    unlocked = {f.feature_key for f in features_result.scalars().all()}
    # BASE_FEATURES 永远视为已解锁
    unlocked.update(BASE_FEATURES)

    # 获取今日所有记录
    records_result = await db.execute(
        select(Record).where(
            Record.user_id == user_id,
            Record.record_date == today,
        ).order_by(Record.created_at)
    )
    records = records_result.scalars().all()

    # 按 record_type 分组今日记录
    today_records: dict[str, list[Record]] = {}
    for r in records:
        today_records.setdefault(r.record_type, []).append(r)

    # 计算 period day（月经第几天）
    period_day = None
    period_result = await db.execute(
        select(Record).where(
            Record.user_id == user_id,
            Record.record_type == "period",
        ).order_by(Record.record_date.desc())
    )
    period_records = period_result.scalars().all()
    if period_records:
        period_day = get_period_day_count(period_records)

    result = {}
    for ft in ALL_FEATURE_TYPES:
        is_unlocked = ft in unlocked
        has_record = ft in today_records

        entry = {
            "recorded": has_record,
            "unlocked": is_unlocked,
        }

        if ft == "period":
            entry["day"] = period_day

        if ft == "sleep":
            if has_record and today_records[ft]:
                last_sleep = today_records[ft][-1]
                entry["score"] = last_sleep.record_value.get("score") if last_sleep.record_value else None
            else:
                entry["score"] = None

        result[ft] = entry

    return result


async def calculate_continuous_days(db: AsyncSession, user_id: UUID) -> int:
    result = await db.execute(
        select(Record.record_date)
        .where(Record.user_id == user_id)
        .distinct()
        .order_by(Record.record_date.desc())
    )
    dates = [row[0] for row in result.all()]
    if not dates:
        return 0

    if dates[0] < date.today():
        return 0

    count = 1
    for i in range(1, len(dates)):
        expected = dates[i - 1] - timedelta(days=1)
        if dates[i] == expected:
            count += 1
        else:
            break

    return count