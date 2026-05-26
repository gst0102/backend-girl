from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.feature import UserFeature
from app.models.user import User

settings = get_settings()

BASE_FEATURES = ["poop", "period"]


def create_jwt_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_jwt_token(token: str) -> str:
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise JWTError("token missing sub field")
    return user_id


async def get_user_by_openid(db: AsyncSession, openid: str) -> User | None:
    result = await db.execute(select(User).where(User.openid == openid))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    return result.scalar_one_or_none()


async def create_new_user(db: AsyncSession, openid: str) -> User:
    import random
    suffix = "".join(random.choices("0123456789abcdef", k=4))
    nickname = f"momo"

    user = User(
        openid=openid,
        nickname=nickname,
        avatar="👤",
        invite_count=0,
        continuous_days=0,
    )
    db.add(user)
    await db.flush()

    for feature_key in BASE_FEATURES:
        db.add(UserFeature(user_id=user.id, feature_key=feature_key))

    await db.flush()
    return user