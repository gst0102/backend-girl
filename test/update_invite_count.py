#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新用户邀请人数"""
import asyncio
import sys

sys.path.insert(0, '.')

from sqlalchemy import select

from app.database import async_session
from app.models.user import User


async def main():
    if len(sys.argv) < 3:
        print("用法: python update_invite_count.py <nickname> <invite_count>")
        print("示例: python update_invite_count.py mock_user_001 50")
        sys.exit(1)
    
    nickname = sys.argv[1]
    try:
        invite_count = int(sys.argv[2])
    except ValueError:
        print("邀请人数必须是整数")
        sys.exit(1)
    
    async with async_session() as db:
        result = await db.execute(select(User).where(User.nickname == nickname))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"用户 {nickname} 不存在")
            sys.exit(1)
        
        old_count = user.invite_count
        user.invite_count = invite_count
        await db.commit()
        
        print(f"✅ 用户 {nickname} 的邀请人数已更新")
        print(f"   旧值: {old_count}")
        print(f"   新值: {invite_count}")


if __name__ == "__main__":
    asyncio.run(main())
