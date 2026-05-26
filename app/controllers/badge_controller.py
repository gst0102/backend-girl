from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.response import success_response, error_response, CodeEnum
from app.services.badge_service import (
    get_user_badges,
    get_all_badges_with_status,
    get_badge_by_id,
    check_and_award_badges,
)

router = APIRouter(prefix="/badge")


class CheckBadgeRequest(BaseModel):
    trigger_type: str
    record_type: str | None = None
    invite_count: int | None = None


@router.get("/list")
async def badge_list(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    data = await get_all_badges_with_status(db, UUID(user_id))
    return success_response(data=data)


@router.get("/detail/{badge_id}")
async def badge_detail(
    badge_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    badge = await get_badge_by_id(db, badge_id, UUID(user_id))
    if badge is None:
        return error_response(CodeEnum.NOT_FOUND, "徽章不存在")
    return success_response(data=badge)


@router.post("/check")
async def check_badges_endpoint(
    req: CheckBadgeRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    earned = await check_and_award_badges(
        db, UUID(user_id), req.trigger_type, req.invite_count
    )
    return success_response(data={"badges_earned": earned})
