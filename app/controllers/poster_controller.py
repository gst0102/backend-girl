from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.poster import PosterGenerateRequest
from app.schemas.response import CodeEnum, error_json, success_response
from app.services.poster_service import (
    generate_badge_poster,
    generate_monthly_poster,
)
from app.services.poster_templates_extended import (
    get_available_templates,
    generate_with_template,
)

router = APIRouter(prefix="/poster")


@router.get("/templates")
async def get_poster_templates():
    """获取所有可用的海报风格模板列表"""
    templates = get_available_templates()
    return success_response(data={"templates": templates})


@router.post("/generate")
async def poster_generate(
    req: PosterGenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if req.template == "monthly":
        if req.style and req.style != "default":
            from app.services.stats_service import get_user_stats
            stats = await get_user_stats(db, UUID(user_id), "month")
            try:
                image_base64 = generate_with_template(req.style, stats)
            except ValueError as e:
                return error_json(CodeEnum.PARAM_ERROR, str(e))
        else:
            image_base64 = await generate_monthly_poster(db, UUID(user_id))
    elif req.template == "badge":
        if not req.badge_id:
            return error_json(CodeEnum.PARAM_ERROR, "badge 模板需要 badge_id")
        image_base64 = await generate_badge_poster(db, UUID(user_id), req.badge_id)
    else:
        return error_json(CodeEnum.PARAM_ERROR, f"不支持的模板: {req.template}")

    return success_response(data={"image_base64": image_base64})
