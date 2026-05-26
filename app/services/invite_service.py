from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config_models import ConfigUnlock
from app.models.feature import UserFeature
from app.models.invite import InviteRelation
from app.models.reward import RewardLog
from app.models.user import User
from app.services.badge_service import check_and_award_badges
from app.events.base import event_bus


async def create_invite_relation(
    db: AsyncSession,
    inviter_id: UUID,
    invitee_openid: str,
    invitee_device: str | None = None,
) -> int:
    result = await db.execute(select(User).where(User.id == inviter_id))
    inviter = result.scalar_one_or_none()
    if inviter is None:
        raise ValueError("INVITER_NOT_FOUND")

    if inviter.openid == invitee_openid:
        raise ValueError("SELF_INVITE")

    existing = await db.execute(
        select(InviteRelation).where(InviteRelation.invitee_openid == invitee_openid)
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("ALREADY_INVITED")

    result = await db.execute(select(User).where(User.openid == invitee_openid))
    invitee = result.scalar_one_or_none()
    if invitee is None:
        raise ValueError("INVITEE_NOT_FOUND")

    relation = InviteRelation(
        inviter_id=inviter.id,
        invitee_id=invitee.id,
        invitee_openid=invitee_openid,
        invitee_device=invitee_device,
    )
    db.add(relation)

    inviter.invite_count += 1
    db.add(inviter)
    await db.flush()

    # ✅ 直接调用解锁检查（新增）
    print(f"准备调用 check_and_unlock_features, inviter_id={inviter.id}, invite_count={inviter.invite_count}")
    from app.services.invite_service import check_and_unlock_features
    await check_and_unlock_features(db, inviter.id, inviter.invite_count)
    print("check_and_unlock_features 调用完成")
    await event_bus.publish("invite_success", {
        "inviter_id": str(inviter.id),
        "invitee_id": str(invitee.id),
        "invite_count": inviter.invite_count,
    })

    return inviter.invite_count


async def check_and_unlock_features(
    db: AsyncSession,
    user_id: UUID,
    invite_count: int,
) -> list[str]:
    result = await db.execute(
        select(ConfigUnlock).order_by(ConfigUnlock.threshold)
    )
    thresholds = result.scalars().all()

    if not thresholds:
        return []

    result = await db.execute(
        select(UserFeature).where(UserFeature.user_id == user_id)
    )
    unlocked = {f.feature_key for f in result.scalars().all()}

    new_unlocked: list[str] = []
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
            new_unlocked.append(cfg.feature_key)

    await db.flush()

    await check_and_award_badges(db, user_id, "invite_count", invite_count)

    return new_unlocked


async def get_invite_progress(db: AsyncSession, user_id: UUID) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError("USER_NOT_FOUND")

    result = await db.execute(
        select(ConfigUnlock).order_by(ConfigUnlock.threshold)
    )
    thresholds = result.scalars().all()

    result = await db.execute(
        select(UserFeature).where(UserFeature.user_id == user_id)
    )
    unlocked = {f.feature_key for f in result.scalars().all()}

    rewards = []
    next_threshold = None
    for cfg in thresholds:
        if cfg.feature_key in unlocked:
            rewards.append({
                "threshold": cfg.threshold,
                "reward": cfg.feature_name,
                "feature_key": cfg.feature_key,
                "status": "unlocked",
                "progress": None,
            })
        else:
            rewards.append({
                "threshold": cfg.threshold,
                "reward": cfg.feature_name,
                "feature_key": cfg.feature_key,
                "status": "locked",
                "progress": f"{user.invite_count}/{cfg.threshold}",
            })
            if next_threshold is None:
                next_threshold = cfg.threshold

    target = 30
    remaining = max(target - user.invite_count, 0)

    return {
        "current": user.invite_count,
        "target": target,
        "next_threshold": next_threshold or user.invite_count,
        "remaining": remaining,
        "rewards": rewards,
    }


async def get_invite_ranking(
    db: AsyncSession,
    limit: int = 10,
    current_user_id: UUID | None = None,
) -> dict:
    result = await db.execute(
        select(User)
        .where(User.invite_count > 0)
        .order_by(User.invite_count.desc(), User.created_at.asc())
        .limit(limit)
    )
    top_users = result.scalars().all()

    ranking = []
    for rank, u in enumerate(top_users, start=1):
        ranking.append({
            "rank": rank,
            "user_id": str(u.id),
            "nickname": u.nickname,
            "avatar": u.avatar,
            "invite_count": u.invite_count,
        })

    my_rank_info = None
    my_invite_count_info = None
    if current_user_id:
        result = await db.execute(
            select(User).where(User.id == current_user_id)
        )
        me = result.scalar_one_or_none()
        if me and me.invite_count > 0:
            result = await db.execute(
                select(func.count())
                .select_from(User)
                .where(User.invite_count > me.invite_count)
            )
            my_rank = result.scalar() + 1
            my_rank_info = my_rank
            my_invite_count_info = me.invite_count
        elif me:
            my_rank_info = 0
            my_invite_count_info = 0

    return {
        "list": ranking,
        "my_rank": my_rank_info,
        "my_invite_count": my_invite_count_info,
    }