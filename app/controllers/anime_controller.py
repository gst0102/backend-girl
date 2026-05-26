from uuid import UUID
from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.response import CodeEnum, error_json, success_response
from app.services.anime_service import (
    get_anime_library,
    get_subscribed_list,
    subscribe_anime,
    unsubscribe_anime,
    get_link_and_remind,
)

router = APIRouter(prefix="/anime")


class SubscribeRequest(BaseModel):
    anime_id: str


class GetLinkRequest(BaseModel):
    anime_id: str
    current_episode: str | None = None


@router.get("/library")
async def anime_library(
    type: str = Query("anime"),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    data = await get_anime_library(db, UUID(user_id), type, keyword, page, page_size)
    return success_response(data=data)


@router.get("/subscribe")
async def my_subscriptions(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    data = await get_subscribed_list(db, UUID(user_id))
    return success_response(data=data)


@router.post("/subscribe")
async def subscribe_anime_endpoint(
    req: SubscribeRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        await subscribe_anime(db, UUID(user_id), req.anime_id)
        await db.commit()
    except ValueError as e:
        error_map = {
            "ANIME_NOT_FOUND": (CodeEnum.ANIME_NOT_FOUND, "番剧不存在"),
            "ALREADY_SUBSCRIBED": (CodeEnum.ALREADY_SUBSCRIBED, "已订阅该番剧"),
        }
        code, detail = error_map.get(str(e), (CodeEnum.SERVER_ERROR, str(e)))
        return error_json(code, detail)
    return success_response(data={"success": True})


@router.delete("/subscribe/{anime_id}")
async def unsubscribe_anime_endpoint(
    anime_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        await unsubscribe_anime(db, UUID(user_id), anime_id)
        await db.commit()
    except ValueError as e:
        error_map = {
            "ANIME_NOT_FOUND": (CodeEnum.ANIME_NOT_FOUND, "番剧不存在"),
        }
        code, detail = error_map.get(str(e), (CodeEnum.SERVER_ERROR, str(e)))
        return error_json(code, detail)
    return success_response(data={"success": True})


@router.post("/get-link-and-remind")
async def get_link_and_remind_endpoint(
    req: GetLinkRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await get_link_and_remind(db, UUID(user_id), req.anime_id, req.current_episode)
        await db.commit()
    except ValueError as e:
        error_map = {
            "ANIME_NOT_FOUND": (CodeEnum.ANIME_NOT_FOUND, "番剧不存在"),
        }
        code, detail = error_map.get(str(e), (CodeEnum.SERVER_ERROR, str(e)))
        return error_json(code, detail)
    return success_response(data=data)
