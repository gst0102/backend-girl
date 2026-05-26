"""
徽章服务
"""
from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.badges_config import BADGES_CONFIG
from app.models.badge import Badge, UserBadge
from app.models.invite import InviteRelation
from app.models.record import Record
from app.models.user import User
from app.models.reward import RewardLog


async def get_user_badges(db: AsyncSession, user_id: UUID) -> List[Dict[str, Any]]:
    """获取用户已获得的徽章列表"""
    result = await db.execute(
        select(UserBadge, Badge)
        .join(Badge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user_id)
    )
    items = result.all()
    return [
        {
            "id": badge.id,
            "name": badge.name,
            "icon": badge.icon,
            "rarity": badge.rarity,
        }
        for ub, badge in items
    ]


async def check_and_award_badges(
    db: AsyncSession, user_id: UUID, trigger_type: str, trigger_value: Any = None
) -> List[Dict[str, Any]]:
    """检查并颁发徽章，返回本次新获得的徽章列表"""
    # 获取用户已获得的徽章
    earned_result = await db.execute(
        select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
    )
    earned_ids = set(row[0] for row in earned_result.all())

    # 获取用户统计数据
    stats = await _get_user_stats(db, user_id)
    new_badges = []

    for badge_id, config in BADGES_CONFIG.items():
        if badge_id in earned_ids:
            continue

        if _meets_condition(config, stats, trigger_type, trigger_value):
            # 颁发徽章
            ub = UserBadge(user_id=user_id, badge_id=badge_id)
            db.add(ub)
            # 添加奖励日志
            db.add(RewardLog(
                user_id=user_id,
                reward_type="badge",
                reward_value=badge_id,
                grant_reason=f"{trigger_type}_{badge_id}"
            ))
            new_badges.append({
                "badge_id": badge_id,
                "name": config["name"],
                "icon": config["icon"],
                "rarity": config["rarity"],
            })

    if new_badges:
        await db.commit()

    return new_badges


async def _get_user_stats(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
    """获取用户统计数据"""
    # 获取所有记录
    result = await db.execute(
        select(Record).where(Record.user_id == user_id)
    )
    records = result.scalars().all()

    record_counts: Dict[str, int] = {}
    record_dates: set = set()
    first_records: Dict[str, bool] = {}

    for r in records:
        # 记录类型计数
        record_counts[r.record_type] = record_counts.get(r.record_type, 0) + 1
        # 记录日期
        record_dates.add(r.record_date)
        # 首次记录标记
        if r.record_type not in first_records:
            first_records[r.record_type] = True

    # 计算连续天数
    continuous_days = 0
    today = date.today()
    check_date = today
    while check_date in record_dates:
        continuous_days += 1
        check_date -= timedelta(days=1)

    # 邀请数量
    invite_result = await db.execute(
        select(func.count(InviteRelation.id)).where(
            InviteRelation.inviter_id == user_id
        )
    )
    invite_count = invite_result.scalar() or 0

    return {
        "record_counts": record_counts,
        "first_records": first_records,
        "continuous_days": continuous_days,
        "invite_count": invite_count,
        "record_dates": record_dates,
    }


def _meets_condition(
    config: Dict[str, Any],
    stats: Dict[str, Any],
    trigger_type: str,
    trigger_value: Any = None
) -> bool:
    """检查是否满足徽章条件"""
    ct = config["condition_type"]
    cv = config["condition_value"]

    if ct == "first_record":
        # 首次记录
        record_type = cv.get("record_type")
        return stats["first_records"].get(record_type, False)

    elif ct == "continuous_days":
        # 连续天数
        return stats["continuous_days"] >= cv

    elif ct == "record_count":
        # 记录次数
        record_type = cv.get("record_type")
        count = cv.get("count")
        return stats["record_counts"].get(record_type, 0) >= count

    elif ct == "invite_count":
        # 邀请数量
        return stats["invite_count"] >= cv

    return False


async def get_all_badges_with_status(
    db: AsyncSession, user_id: UUID
) -> Dict[str, Any]:
    """获取全部徽章列表（含用户拥有状态）"""
    # 获取用户已获得的徽章
    earned_result = await db.execute(
        select(UserBadge.badge_id, UserBadge.earned_at)
        .where(UserBadge.user_id == user_id)
    )
    earned = {
        row[0]: row[1].isoformat() if row[1] else None
        for row in earned_result.all()
    }

    owned_badges = []
    locked_badges = []

    for badge_id, config in BADGES_CONFIG.items():
        data = {
            "id": config["id"],
            "name": config["name"],
            "icon": config["icon"],
            "rarity": config["rarity"],
            "category": config["category"],
            "condition_type": config["condition_type"],
            "condition_value": config["condition_value"],
            "description": config["description"],
        }
        if badge_id in earned:
            data["earned_at"] = earned[badge_id]
            owned_badges.append(data)
        else:
            locked_badges.append(data)

    return {
        "total": len(BADGES_CONFIG),
        "owned": len(owned_badges),
        "owned_badges": owned_badges,
        "locked_badges": locked_badges,
    }


async def get_badge_by_id(
    db: AsyncSession,
    badge_id: str,
    user_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """获取单个徽章详情"""
    config = BADGES_CONFIG.get(badge_id)
    if not config:
        return None

    result = {
        "id": config["id"],
        "name": config["name"],
        "icon": config["icon"],
        "rarity": config["rarity"],
        "category": config["category"],
        "condition_type": config["condition_type"],
        "condition_value": config["condition_value"],
        "description": config["description"],
        "earned_at": None,
    }

    if user_id:
        earned_result = await db.execute(
            select(UserBadge.earned_at)
            .where(
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge_id
            )
        )
        row = earned_result.first()
        if row:
            result["earned_at"] = row[0].isoformat() if row[0] else None

    return result


# 保持旧接口兼容
async def check_badges(
    db: AsyncSession, user_id: UUID, continuous_days: int
) -> List[Dict[str, Any]]:
    """创建记录后检查徽章（兼容旧调用）"""
    return await check_and_award_badges(
        db, user_id, "record_create"
    )
