from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.invite import InviteCreateRequest
from app.schemas.response import CodeEnum, error_json, success_response
from app.services.invite_service import (
    check_and_unlock_features,
    create_invite_relation,
    get_invite_progress,
    get_invite_ranking,
)

router = APIRouter(prefix="/invite")
rank_router = APIRouter(prefix="/rank")


@router.post("/create")
async def create_invite(
    req: InviteCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        invite_count = await create_invite_relation(
            db, UUID(user_id), req.invitee_openid, req.invitee_device
        )
    except ValueError as e:
        error_map = {
            "INVITER_NOT_FOUND": (CodeEnum.USER_NOT_FOUND, "邀请人不存在"),
            "SELF_INVITE": (CodeEnum.SELF_INVITE, "不能邀请自己"),
            "ALREADY_INVITED": (CodeEnum.ALREADY_INVITED, "该用户已被邀请过"),
            "INVITEE_NOT_FOUND": (CodeEnum.NOT_FOUND, "被邀请人不存在"),
        }
        code, detail = error_map.get(str(e), (CodeEnum.SERVER_ERROR, str(e)))
        return error_json(code, detail)

    new_unlocked = await check_and_unlock_features(db, UUID(user_id), invite_count)

    # 邀请徽章检查
    from app.services.badge_service import check_and_award_all
    badges_earned = await check_and_award_all(db, UUID(user_id), "invite")

    await db.commit()
    return success_response(data={
        "invite_count": invite_count,
        "new_unlocked": new_unlocked,
        "badges_earned": badges_earned,
    })


@router.get("/progress")
async def invite_progress(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    data = await get_invite_progress(db, UUID(user_id))
    return success_response(data=data)


@rank_router.get("/list")
async def rank_list(
    request: Request,
    type: str = Query("invite", description="排行榜类型，暂只支持 invite"),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    user_id_raw = getattr(request.state, "user_id", None)
    current_user_id = UUID(user_id_raw) if user_id_raw else None

    data = await get_invite_ranking(db, limit=limit, current_user_id=current_user_id)
    return success_response(data=data)


