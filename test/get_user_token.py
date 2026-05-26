#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取指定用户的 JWT Token"""
import asyncio
import sys

sys.path.insert(0, '.')

from sqlalchemy import select

from app.database import async_session
from app.models.user import User
from app.services.auth_service import create_jwt_token


async def main():
    if len(sys.argv) < 2:
        print("Usage: python get_user_token.py <nickname>")
        sys.exit(1)
    
    nickname = sys.argv[1]
    
    async with async_session() as db:
        result = await db.execute(select(User).where(User.nickname == nickname))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User not found: {nickname}")
            sys.exit(1)
        
        token = create_jwt_token(str(user.id))
        print(f"User ID: {user.id}")
        print(f"Nickname: {user.nickname}")
        print(f"Invite Count: {user.invite_count}")
        print(f"Token: Bearer {token}")


if __name__ == "__main__":
    asyncio.run(main())
