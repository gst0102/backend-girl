#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解锁指定用户的所有功能权限
"""
import asyncio
import sys

sys.path.insert(0, '.')

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.feature import UserFeature
from app.models.user import User


ALL_FEATURES = [
    "poop",        # 拉屎记录（基础）
    "period",      # 姨妈记录（基础）
    "sleep",       # 睡眠记录（邀请1人）
    "water",       # 喝水提醒（邀请3人）
    "anime_remind",   # 追番提醒（邀请8人）
    "anime_preview",  # 追番预告（邀请15人）
    "anime_drive",    # 网盘资源（邀请30人）
    "sport",       # 运动记录
    "study",       # 学习记录
    "pill",        # 吃药提醒
    "mood",        # 心情记录
    "pet",         # 宠物护理
]


async def unlock_all_features_for_user(db: AsyncSession, user_id: UUID):
    """为指定用户解锁所有功能"""
    
    # 检查用户是否存在
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        print(f"[ERROR] 用户不存在: {user_id}")
        return False
    
    print(f"[INFO] 正在为用户 {user_id} 解锁所有功能...")
    
    # 获取用户已解锁的功能
    result = await db.execute(
        select(UserFeature.feature_key).where(UserFeature.user_id == user_id)
    )
    existing_features = {row[0] for row in result.all()}
    print(f"[INFO] 用户当前已解锁 {len(existing_features)} 个功能")
    
    # 解锁所有功能
    new_unlocked = []
    for feature_key in ALL_FEATURES:
        if feature_key not in existing_features:
            db.add(UserFeature(user_id=user_id, feature_key=feature_key))
            new_unlocked.append(feature_key)
    
    if new_unlocked:
        await db.commit()
        print(f"[SUCCESS] 成功解锁 {len(new_unlocked)} 个新功能:")
        for feature in new_unlocked:
            print(f"  ✓ {feature}")
    else:
        print("[INFO] 用户已经拥有所有功能权限")
    
    # 更新用户邀请数为30（解锁全部功能所需人数）
    user.invite_count = 30
    await db.commit()
    print(f"[INFO] 用户邀请数已设置为 30")
    
    return True


async def get_user_by_nickname(db: AsyncSession, nickname: str):
    """通过昵称查找用户"""
    result = await db.execute(select(User).where(User.nickname == nickname))
    return result.scalar_one_or_none()


async def create_test_user(db: AsyncSession, nickname: str) -> User:
    """创建测试用户"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        openid=f"mock_openid_{nickname}",
        nickname=nickname,
        avatar=f"avatar_{nickname}",
        invite_count=30,
        continuous_days=30,
    )
    db.add(user)
    await db.flush()
    print(f"[INFO] 创建测试用户: {user.id} ({nickname})")
    return user


async def main():
    if len(sys.argv) < 2:
        print("用法: python unlock_all_features.py <user_id_or_nickname>")
        print("示例: python unlock_all_features.py mock_user_001")
        sys.exit(1)
    
    identifier = sys.argv[1]
    
    async with async_session() as db:
        # 尝试解析为UUID
        try:
            user_id = UUID(identifier)
            user = await db.get(User, user_id)
            if not user:
                print(f"[ERROR] 未找到用户: {user_id}")
                sys.exit(1)
        except ValueError:
            # 尝试按昵称查找
            user = await get_user_by_nickname(db, identifier)
            if not user:
                print(f"[INFO] 用户 {identifier} 不存在，正在创建...")
                user = await create_test_user(db, identifier)
            
            user_id = user.id
        
        success = await unlock_all_features_for_user(db, user_id)
        
        # 打印用户token方便测试
        from app.services.auth_service import create_jwt_token
        token = create_jwt_token(str(user_id))
        print(f"\n[INFO] 用户 Token (有效期30分钟):")
        print(f"Bearer {token}")
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
