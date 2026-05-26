from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.feature import UserFeature
from app.models.user import User
from app.schemas.response import CodeEnum, error_response


async def get_current_user_id(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="未获取到用户身份"
        )
    return user_id


async def get_current_user_id_optional(request: Request) -> str | None:
    return getattr(request.state, "user_id", None)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return JSONResponse(
            status_code=200,
            content=error_response(CodeEnum.USER_NOT_FOUND).model_dump(),
        )
    return user


def require_feature(feature_key: str):
    async def dependency(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        result = await db.execute(
            select(UserFeature).where(
                UserFeature.user_id == user.id,
                UserFeature.feature_key == feature_key,
            )
        )
        feature = result.scalar_one_or_none()
        if feature is None:
            return JSONResponse(
                status_code=200,
                content=error_response(CodeEnum.FEATURE_LOCKED, f"功能 [{feature_key}] 尚未解锁").model_dump(),
            )
        return feature

    return dependency