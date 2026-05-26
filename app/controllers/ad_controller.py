from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import AdConfig
from app.schemas.ad import AdConfigUpdateRequest
from app.schemas.response import success_response
from app.services.admin_service import get_public_ad_config

router = APIRouter(prefix="/ad", tags=["广告"])


@router.get("/config")
async def get_ad_config(db: AsyncSession = Depends(get_db)):
    """获取所有广告配置（小程序端）"""
    data = await get_public_ad_config(db)
    return success_response(data=data)


@router.post("/config")
async def update_ad_config(
    req: AdConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """更新广告配置（管理端）"""
    result = await db.execute(select(AdConfig).where(AdConfig.ad_type == req.ad_type))
    config = result.scalar_one_or_none()

    if config:
        config.enabled = req.enabled
        if req.unit_id is not None:
            config.unit_id = req.unit_id
        if req.test_unit_id is not None:
            config.test_unit_id = req.test_unit_id
        if req.position is not None:
            config.position = req.position
        if req.sort_order is not None:
            config.sort_order = req.sort_order
        if req.description is not None:
            config.description = req.description
        if req.ab_test_enabled is not None:
            config.ab_test_enabled = req.ab_test_enabled
        if req.ab_test_ratio is not None:
            config.ab_test_ratio = req.ab_test_ratio
    else:
        config = AdConfig(
            ad_type=req.ad_type,
            enabled=req.enabled,
            unit_id=req.unit_id or "",
            test_unit_id=req.test_unit_id or "",
            position=req.position or "",
            sort_order=req.sort_order or 0,
            description=req.description or "",
            ab_test_enabled=req.ab_test_enabled or False,
            ab_test_ratio=req.ab_test_ratio if req.ab_test_ratio is not None else 0.5,
        )
        db.add(config)

    await db.commit()
    return success_response(data={"success": True})
