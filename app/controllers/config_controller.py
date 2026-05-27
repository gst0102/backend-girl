import json
import os
import uuid
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_id
from app.models import (
    AdConfig,
    Feedback,
    MarqueeConfig,
    MineApp,
    ReserveConfig,
)
from app.schemas.response import success_response, error_response, CodeEnum
from app.services.admin_service import (
    get_public_ad_config,
    get_public_banners,
    get_public_mine_sections,
)

router = APIRouter(prefix="/config")
UPLOAD_DIR = "static/feedback"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# 跑马灯接口
@router.get("/marquee")
async def get_marquee_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MarqueeConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        config = MarqueeConfig(enabled=False, content="")
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return success_response(data={
        "enabled": config.enabled,
        "content": config.content,
        "link_url": config.link_url
    })


@router.post("/marquee")
async def set_marquee_config(
    enabled: bool = Form(...),
    content: str = Form(None),
    link_url: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MarqueeConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        config = MarqueeConfig()
    config.enabled = enabled
    config.content = content
    config.link_url = link_url
    config.updated_at = datetime.now()
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return success_response(data=None)


# 广告配置接口（小程序端公开） - 接口45
@router.get("/ad")
async def get_ad_config_client(db: AsyncSession = Depends(get_db)):
    data = await get_public_ad_config(db)
    return success_response(data=data)


# 公开Banner列表（小程序首页轮播） - 新接口
@router.get("/banners")
async def get_banners_client(db: AsyncSession = Depends(get_db)):
    data = await get_public_banners(db)
    return success_response(data=data)


# 公开Mine板块配置（小程序我的页面板块标题） - 新接口
@router.get("/mine-sections")
async def get_mine_sections_client(db: AsyncSession = Depends(get_db)):
    data = await get_public_mine_sections(db)
    return success_response(data=data)


# 问题反馈接口
@router.post("/feedback")
async def submit_feedback(
    type: str = Form(...),
    content: str = Form(...),
    contact: str = Form(None),
    screenshots: list[UploadFile] = File(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    screenshot_urls = []
    if screenshots:
        for f in screenshots:
            ext = f.filename.split('.')[-1] if '.' in f.filename else 'png'
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            file_bytes = await f.read()
            with open(filepath, "wb") as out:
                out.write(file_bytes)
            screenshot_urls.append(f"/static/feedback/{filename}")
    feedback = Feedback(
        user_id=user_id,
        type=type,
        content=content,
        contact=contact,
        screenshots=json.dumps(screenshot_urls) if screenshot_urls else None,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return success_response(data=None)


# 反馈提交（接口40 - 客户端路径）
feedback_router = APIRouter(prefix="")


class FeedbackSubmitRequest(BaseModel):
    content: str = Field(..., max_length=500)
    screenshots: list[str] | None = None
    contact: str | None = None
    platform: str | None = None
    type: str | None = "feedback"


@feedback_router.post("/feedback")
async def submit_feedback_client(
    req: FeedbackSubmitRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    content = req.content.strip()
    if not content:
        return error_response(CodeEnum.PARAM_ERROR, "内容不能为空且不超过500字符")
    screenshots = req.screenshots or None
    feedback = Feedback(
        user_id=user_id,
        type=req.type or "feedback",
        content=content,
        contact=req.contact or req.platform,
        screenshots=json.dumps(screenshots) if screenshots else None,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return success_response(data={"id": feedback.id})


# 反馈截图上传（接口41）
upload_router = APIRouter(prefix="/upload")

FEEDBACK_UPLOAD_DIR = "static/feedback"
os.makedirs(FEEDBACK_UPLOAD_DIR, exist_ok=True)


@upload_router.post("/feedback")
async def upload_feedback_image(
    image: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    ext = image.filename.split(".")[-1] if "." in image.filename else "png"
    if ext.lower() not in ("jpg", "jpeg", "png", "gif"):
        return error_response(CodeEnum.PARAM_ERROR, "仅支持 jpg/png/gif 格式")
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(FEEDBACK_UPLOAD_DIR, filename)
    content = await image.read()
    if len(content) > 5 * 1024 * 1024:
        return error_response(CodeEnum.PARAM_ERROR, "图片大小不能超过5MB")
    with open(filepath, "wb") as f:
        f.write(content)
    return success_response(data={"url": f"/static/feedback/{filename}"})


# 预留配置客户端获取（接口44）
@router.get("/reserve")
async def get_reserve_config_client(db: AsyncSession = Depends(get_db)):
    mini_result = await db.execute(
        select(MineApp).where(MineApp.enabled == True).order_by(MineApp.sort_order)
    )
    apps = mini_result.scalars().all()
    mini_programs = []
    for app in apps:
        mini_programs.append({
            "enabled": True,
            "app_id": app.app_id,
            "path": app.path or "/pages/index",
            "name": app.name,
            "icon": app.icon or "",
        })

    result = await db.execute(select(ReserveConfig).where(ReserveConfig.config_type == "official_account"))
    row = result.scalar_one_or_none()
    official_account = None
    if row:
        oa = json.loads(row.config_data)
        if oa.get("enabled"):
            official_account = {
                "enabled": True,
                "name": oa.get("name", ""),
                "qrcode_url": oa.get("qrcode_url", ""),
                "description": oa.get("description", ""),
            }

    return success_response(data={
        "mini_programs": mini_programs if mini_programs else None,
        "official_account": official_account,
    })


# 跑马灯配置 - 客户端获取（接口42）
marquee_router = APIRouter(prefix="/marquee")


@marquee_router.get("/config")
async def get_marquee_config_client(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MarqueeConfig).limit(1))
    m = result.scalar_one_or_none()
    if not m or not m.enabled:
        return success_response(data={"enabled": False, "target": 5, "text_template": ""})
    return success_response(data={
        "enabled": m.enabled,
        "target": 5,
        "text_template": m.content or "🎁 邀请{target}位好友，解锁定制影视剧网盘资源自动推送功能！当前进度：{current}/{target}，还差{remaining}人 → 点击邀请好友 →",
    })


@marquee_router.post("/config")
async def set_marquee_config_client(
    enabled: bool = Form(...),
    target: int = Form(5),
    text_template: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MarqueeConfig).limit(1))
    m = result.scalar_one_or_none()
    if not m:
        m = MarqueeConfig()
        db.add(m)
    m.enabled = enabled
    if text_template:
        m.content = text_template
    m.updated_at = datetime.now()
    await db.commit()
    return success_response(data=None)
