import logging
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.badge import UserBadge
from app.models.user import User

logger = logging.getLogger(__name__)

BADGE_THRESHOLDS = [7, 14, 30]


async def handle_record_created(data: dict):
    """处理记录创建事件"""
    user_id = data.get("user_id")
    
    if not user_id:
        logger.error("Record event missing required data")
        return
    
    async with async_session() as db:
        try:
            await _process_record(db, UUID(user_id))
            await db.commit()
            logger.info(f"Record event processed successfully for user: {user_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing record event: {e}")


async def _process_record(db: AsyncSession, user_id: UUID):
    """处理记录逻辑"""
    user = await db.get(User, user_id)
    if not user:
        logger.error(f"User not found: {user_id}")
        return
    
    today = date.today()
    # 先基于 DB 旧值计算连续天数（不提前 flush，否则会覆盖 streak 起点）
    new_continuous_days = await _calculate_continuous_days(db, user_id, today)
    
    user.last_record_at = today
    days_changed = (new_continuous_days != user.continuous_days)
    if days_changed:
        user.continuous_days = new_continuous_days
    
    # 合并为一次 flush，减少锁竞争
    await db.flush()
    
    if days_changed:
        logger.info(f"User {user_id} continuous days updated: {new_continuous_days}")
        await _check_and_award_badges(db, user_id, new_continuous_days)


async def _calculate_continuous_days(db: AsyncSession, user_id: UUID, today: date) -> int:
    """计算连续记录天数"""
    from app.services.record_service import get_today_status
    
    status = await get_today_status(db, user_id)
    
    if not any(feature["recorded"] for feature in status.values()):
        return 0
    
    # 只查一次 last_record_at，不要在循环里反复查
    result = await db.execute(
        select(User.last_record_at).where(User.id == user_id)
    )
    last_record = result.scalar_one_or_none()
    
    if not last_record:
        return 0
    
    continuous_days = 1
    check_date = today - timedelta(days=1)
    
    while check_date >= last_record:
        continuous_days += 1
        check_date -= timedelta(days=1)
    
    return continuous_days


async def _check_and_award_badges(db: AsyncSession, user_id: UUID, continuous_days: int):
    """检查并颁发徽章"""
    result = await db.execute(select(UserBadge.badge_id).where(UserBadge.user_id == user_id))
    earned_badges = {row[0] for row in result.all()}
    
    for threshold in BADGE_THRESHOLDS:
        if continuous_days >= threshold:
            badge_id = f"badge_00{threshold // 7}" if threshold <= 14 else "badge_003"
            
            if badge_id not in earned_badges:
                # 这里可以根据实际 badges_config 来处理
                db.add(UserBadge(user_id=user_id, badge_id=badge_id))
                earned_badges.add(badge_id)
                logger.info(f"Badge awarded to user {user_id}: {badge_id}")

