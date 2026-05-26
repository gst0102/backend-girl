import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.config_models import ConfigUnlock, ConfigPushTemplate
from app.models.feature import UserFeature
from app.models.push import PushLog
from app.models.reward import RewardLog
from app.models.user import User
from app.services.push_service import create_push_log

logger = logging.getLogger(__name__)


async def handle_invite_success(data: dict):
    print("===== on_invite_success 被触发 =====")
    print(f"收到数据: {data}")
    """处理邀请成功事件"""
    inviter_id = data.get("inviter_id")
    invitee_openid = data.get("invitee_openid")
    
    if not inviter_id or not invitee_openid:
        print("没有 inviter_id，跳过")
        logger.error("Invite event missing required data")
        return
    
    async with async_session() as db:
        try:
            print("没有 inviter_id，跳过")
            await _process_invite(db, UUID(inviter_id))
            await db.commit()
            logger.info(f"Invite event processed successfully for inviter: {inviter_id}")
            print("解锁检查完成")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing invite event: {e}")


async def _process_invite(db: AsyncSession, inviter_id: UUID):
    """处理邀请逻辑"""
    user = await db.get(User, inviter_id)
    if not user:
        logger.error(f"Inviter not found: {inviter_id}")
        return
    
    user.invite_count += 1
    await db.flush()
    
    new_unlocked = await _check_and_unlock_features(db, inviter_id, user.invite_count)
    
    if new_unlocked:
        await _create_feature_unlock_pushes(db, inviter_id, new_unlocked)


async def _check_and_unlock_features(db: AsyncSession, user_id: UUID, invite_count: int) -> list:
    """检查并解锁新功能"""
    result = await db.execute(select(ConfigUnlock).order_by(ConfigUnlock.threshold))
    thresholds = result.scalars().all()
    
    if not thresholds:
        return []
    
    result = await db.execute(select(UserFeature).where(UserFeature.user_id == user_id))
    unlocked = {f.feature_key for f in result.scalars().all()}
    
    new_unlocked = []
    for cfg in thresholds:
        if cfg.feature_key in unlocked:
            continue
        if invite_count >= cfg.threshold:
            db.add(UserFeature(user_id=user_id, feature_key=cfg.feature_key))
            db.add(RewardLog(
                user_id=user_id,
                reward_type="feature",
                reward_value=cfg.feature_key,
                grant_reason=f"invite_count_{cfg.threshold}",
            ))
            unlocked.add(cfg.feature_key)
            new_unlocked.append({"key": cfg.feature_key, "name": cfg.feature_name})
            logger.info(f"Feature unlocked for user {user_id}: {cfg.feature_key}")
    
    if new_unlocked:
        await db.flush()
    
    return new_unlocked


async def _create_feature_unlock_pushes(db: AsyncSession, user_id: UUID, unlocked_features: list):
    """创建功能解锁推送"""
    result = await db.execute(
        select(ConfigPushTemplate).where(ConfigPushTemplate.template_id == "msg_feature_unlock")
    )
    template = result.scalar_one_or_none()
    
    if not template:
        logger.warning("Push template not found: msg_feature_unlock")
        return
    
    for feature in unlocked_features:
        content = template.content.format(feature=feature["name"])
        await create_push_log(db, user_id, template.template_id, content, template.channel)
        logger.info(f"Created push for feature unlock: {feature['name']}")