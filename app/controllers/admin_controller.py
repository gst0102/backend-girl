import os
import uuid as _uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.response import success_response, error_response, CodeEnum
from app.services.admin_service import (
    create_banner,
    create_kdocs_source,
    create_mine_app,
    delete_banner,
    delete_kdocs_source,
    delete_mine_app,
    get_ad_config,
    get_ad_stats,
    get_ad_user_contribution,
    get_banners,
    get_kdocs_sources,
    get_marquee_config,
    get_mine_apps,
    get_mine_sections,
    get_overview,
    get_reserve_config,
    get_system_config,
    get_unlock_config,
    get_user_list,
    get_user_trend,
    release_invite,
    sort_mine_apps,
    toggle_banner,
    update_ad_config,
    update_banner,
    update_invite_count,
    update_kdocs_source,
    update_marquee_config,
    update_mine_app,
    update_mine_section,
    update_mine_sections_batch,
    update_reserve_config,
    update_system_config,
    update_system_config_item,
    update_unlock_config,
)

router = APIRouter(prefix="/admin")


class InviteCountReq(BaseModel):
    invite_count: int


class ReleaseInviteReq(BaseModel):
    feature_key: str


class AdConfigReq(BaseModel):
    rewarded_video: dict | None = None
    banner: dict | None = None
    custom_ad: dict | None = None
    ab_test: dict | None = None


class MarqueeReq(BaseModel):
    enabled: bool
    target: int | None = 5
    text_template: str | None = ""
    interval: int | None = 5000


class BannerReq(BaseModel):
    title: str
    image_url: str
    link_url: str | None = ""
    sort_order: int | None = 0
    status: str | None = "active"


class ToggleBannerReq(BaseModel):
    status: str


class UnlockConfigReq(BaseModel):
    sleep: int | None = None
    water: int | None = None
    anime_remind: int | None = None
    anime_preview: int | None = None
    anime_drive: int | None = None
    drive: int | None = None


class OfficialAccountReq(BaseModel):
    enabled: bool
    name: str = ""
    qrcode_url: str = ""
    description: str = ""


class ReserveConfigReq(BaseModel):
    official_account: OfficialAccountReq


class KDocsSourceReq(BaseModel):
    name: str
    url: str
    type: str
    enabled: bool | None = True
    cron_expression: str | None = "*/15 * * * *"


class MineAppReq(BaseModel):
    name: str
    app_id: str
    path: str | None = "/pages/index"
    icon: str | None = ""
    sort_order: int | None = 0
    enabled: bool | None = True


class SortAppsReq(BaseModel):
    ids: list[int]


class SystemConfigReq(BaseModel):
    config: dict


class SystemConfigItemReq(BaseModel):
    key: str
    value: str


class MineSectionReq(BaseModel):
    section_key: str
    title: str | None = None
    enabled: bool | None = None
    sort_order: int | None = None
    description: str | None = None


class MineSectionsBatchReq(BaseModel):
    sections: list[MineSectionReq]


# ===== 用户管理 =====
@router.get("/users")
async def admin_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    data = await get_user_list(db, page, page_size, keyword, status)
    return success_response(data=data)


@router.put("/users/{user_id}/invite-count")
async def admin_update_invite_count(
    user_id: str,
    req: InviteCountReq,
    db: AsyncSession = Depends(get_db),
):
    try:
        await update_invite_count(db, UUID(user_id), req.invite_count)
        await db.commit()
    except ValueError as e:
        if str(e) == "USER_NOT_FOUND":
            return error_response(CodeEnum.NOT_FOUND, "用户不存在")
        raise
    return success_response()


@router.post("/users/{user_id}/release-invite")
async def admin_release_invite(
    user_id: str,
    req: ReleaseInviteReq,
    db: AsyncSession = Depends(get_db),
):
    try:
        await release_invite(db, UUID(user_id), req.feature_key)
        await db.commit()
    except ValueError as e:
        if str(e) == "USER_NOT_FOUND":
            return error_response(CodeEnum.NOT_FOUND, "用户不存在")
        raise
    return success_response()


# ===== 数据看板 =====
@router.get("/stats/overview")
async def admin_stats_overview(db: AsyncSession = Depends(get_db)):
    data = await get_overview(db)
    return success_response(data=data)


@router.get("/stats/trend")
async def admin_stats_trend(
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    data = await get_user_trend(db, days)
    return success_response(data=data)


# ===== 广告配置 =====
@router.get("/ads")
async def admin_get_ads(db: AsyncSession = Depends(get_db)):
    data = await get_ad_config(db)
    return success_response(data=data)


@router.put("/ads")
async def admin_update_ads(req: AdConfigReq, db: AsyncSession = Depends(get_db)):
    await update_ad_config(db, req.model_dump(exclude_none=True))
    await db.commit()
    return success_response()


@router.get("/ads/stats")
async def admin_ad_stats(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    data = await get_ad_stats(db, start_date, end_date)
    return success_response(data=data)


@router.get("/ads/user-contribution")
async def admin_ad_user_contribution(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await get_ad_user_contribution(db, page, page_size)
    return success_response(data=data)


# ===== 跑马灯 =====
@router.get("/marquee")
async def admin_get_marquee(db: AsyncSession = Depends(get_db)):
    data = await get_marquee_config(db)
    return success_response(data=data)


@router.put("/marquee")
async def admin_update_marquee(req: MarqueeReq, db: AsyncSession = Depends(get_db)):
    await update_marquee_config(db, req.model_dump())
    await db.commit()
    return success_response()


# ===== Banner 管理 =====
@router.get("/banners")
async def admin_get_banners(db: AsyncSession = Depends(get_db)):
    data = await get_banners(db)
    return success_response(data=data)


@router.post("/banners")
async def admin_create_banner(req: BannerReq, db: AsyncSession = Depends(get_db)):
    banner = await create_banner(db, req.model_dump())
    await db.commit()
    return success_response(data={"id": banner.id})


@router.put("/banners/{banner_id}")
async def admin_update_banner(banner_id: int, req: BannerReq, db: AsyncSession = Depends(get_db)):
    try:
        banner = await update_banner(db, banner_id, req.model_dump(exclude_none=True))
        await db.commit()
    except ValueError as e:
        if str(e) == "BANNER_NOT_FOUND":
            return error_response(CodeEnum.NOT_FOUND, "Banner不存在")
        raise
    return success_response()


@router.delete("/banners/{banner_id}")
async def admin_delete_banner(banner_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await delete_banner(db, banner_id)
        await db.commit()
    except ValueError as e:
        if str(e) == "BANNER_NOT_FOUND":
            return error_response(CodeEnum.NOT_FOUND, "Banner不存在")
        raise
    return success_response()


@router.post("/banners/{banner_id}/toggle")
async def admin_toggle_banner(banner_id: int, req: ToggleBannerReq, db: AsyncSession = Depends(get_db)):
    try:
        await toggle_banner(db, banner_id, req.status)
        await db.commit()
    except ValueError as e:
        if str(e) == "BANNER_NOT_FOUND":
            return error_response(CodeEnum.NOT_FOUND, "Banner不存在")
        raise
    return success_response()


# ===== 系统配置 =====
@router.get("/config/unlock")
async def admin_get_unlock_config(db: AsyncSession = Depends(get_db)):
    data = await get_unlock_config(db)
    return success_response(data=data)


@router.put("/config/unlock")
async def admin_update_unlock_config(req: UnlockConfigReq, db: AsyncSession = Depends(get_db)):
    data = req.model_dump(exclude_none=True)
    if "drive" in data and "anime_drive" not in data:
        data["anime_drive"] = data.pop("drive")
    else:
        data.pop("drive", None)
    await update_unlock_config(db, data)
    await db.commit()
    return success_response()


# ===== 预留配置 =====
@router.get("/reserve")
async def admin_get_reserve(db: AsyncSession = Depends(get_db)):
    data = await get_reserve_config(db)
    return success_response(data=data)


@router.put("/reserve")
async def admin_update_reserve(req: ReserveConfigReq, db: AsyncSession = Depends(get_db)):
    await update_reserve_config(db, req.model_dump(exclude_none=True))
    await db.commit()
    return success_response()


# ===== 数据源配置 =====
@router.get("/kdocs/sources")
async def admin_get_kdocs_sources(db: AsyncSession = Depends(get_db)):
    data = await get_kdocs_sources(db)
    return success_response(data=data)


@router.post("/kdocs/sources")
async def admin_create_kdocs_source(req: KDocsSourceReq, db: AsyncSession = Depends(get_db)):
    ks = await create_kdocs_source(db, req.model_dump())
    await db.commit()
    return success_response(data={"id": ks.id})


@router.put("/kdocs/sources/{source_id}")
async def admin_update_kdocs_source(source_id: int, req: KDocsSourceReq, db: AsyncSession = Depends(get_db)):
    try:
        ks = await update_kdocs_source(db, source_id, req.model_dump(exclude_none=True))
        await db.commit()
    except ValueError as e:
        if str(e) == "SOURCE_NOT_FOUND":
            return error_response(CodeEnum.NOT_FOUND, "数据源不存在")
        raise
    return success_response()


@router.delete("/kdocs/sources/{source_id}")
async def admin_delete_kdocs_source(source_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await delete_kdocs_source(db, source_id)
        await db.commit()
    except ValueError as e:
        if str(e) == "SOURCE_NOT_FOUND":
            return error_response(CodeEnum.NOT_FOUND, "数据源不存在")
        raise
    return success_response()


# ===== Mine 页小程序管理 =====
@router.get("/mine-apps")
async def admin_get_mine_apps(db: AsyncSession = Depends(get_db)):
    data = await get_mine_apps(db)
    return success_response(data=data)


@router.post("/mine-apps")
async def admin_create_mine_app(req: MineAppReq, db: AsyncSession = Depends(get_db)):
    ma = await create_mine_app(db, req.model_dump())
    await db.commit()
    return success_response(data={"id": ma.id})


@router.put("/mine-apps/{app_id}")
async def admin_update_mine_app(app_id: int, req: MineAppReq, db: AsyncSession = Depends(get_db)):
    try:
        ma = await update_mine_app(db, app_id, req.model_dump(exclude_none=True))
        await db.commit()
    except ValueError as e:
        if str(e) == "APP_NOT_FOUND":
            return error_response(CodeEnum.NOT_FOUND, "小程序不存在")
        raise
    return success_response()


@router.delete("/mine-apps/{app_id}")
async def admin_delete_mine_app(app_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await delete_mine_app(db, app_id)
        await db.commit()
    except ValueError as e:
        if str(e) == "APP_NOT_FOUND":
            return error_response(CodeEnum.NOT_FOUND, "小程序不存在")
        raise
    return success_response()


@router.put("/mine-apps/sort")
async def admin_sort_mine_apps(req: SortAppsReq, db: AsyncSession = Depends(get_db)):
    await sort_mine_apps(db, req.ids)
    await db.commit()
    return success_response()


# ===== 系统配置 =====
@router.get("/system")
async def admin_get_system_config(db: AsyncSession = Depends(get_db)):
    data = await get_system_config(db)
    return success_response(data=data)


@router.put("/system")
async def admin_update_system_config(req: SystemConfigReq, db: AsyncSession = Depends(get_db)):
    await update_system_config(db, req.config)
    await db.commit()
    return success_response()


@router.put("/system/item")
async def admin_update_system_config_item(req: SystemConfigItemReq, db: AsyncSession = Depends(get_db)):
    await update_system_config_item(db, req.key, req.value)
    await db.commit()
    return success_response()


# ===== Mine 板块配置 =====
@router.get("/mine-sections")
async def admin_get_mine_sections(db: AsyncSession = Depends(get_db)):
    data = await get_mine_sections(db)
    return success_response(data=data)


@router.put("/mine-sections/{section_key}")
async def admin_update_mine_section(section_key: str, req: MineSectionReq, db: AsyncSession = Depends(get_db)):
    await update_mine_section(db, section_key, req.model_dump(exclude_none=True))
    await db.commit()
    return success_response()


@router.put("/mine-sections")
async def admin_update_mine_sections_batch(req: MineSectionsBatchReq, db: AsyncSession = Depends(get_db)):
    sections = [s.model_dump(exclude_none=True) for s in req.sections]
    await update_mine_sections_batch(db, sections)
    await db.commit()
    return success_response()


# ===== 文件上传 =====
UPLOAD_DIR_QRCODE = "static/qrcode"
UPLOAD_DIR_BANNER = "static/banner"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _save_upload(file: UploadFile, subdir: str) -> str:
    """保存上传文件，返回 /static/ 相对路径"""
    ext = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else "png"
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("文件类型不支持，仅支持 png/jpg/jpeg/webp/gif")

    file_bytes = file.file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("文件过大，限制 5MB 以内")

    os.makedirs(subdir, exist_ok=True)
    filename = f"{_uuid.uuid4()}.{ext}"
    filepath = os.path.join(subdir, filename)
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return f"/{subdir}/{filename}"


@router.post("/upload/qrcode")
async def admin_upload_qrcode(file: UploadFile = File(...)):
    """上传公众号二维码"""
    try:
        url = _save_upload(file, UPLOAD_DIR_QRCODE)
    except ValueError as e:
        return error_response(CodeEnum.PARAM_ERROR, str(e))
    return success_response(data={"url": url})


@router.post("/upload/banner")
async def admin_upload_banner(file: UploadFile = File(...)):
    """上传Banner图片"""
    try:
        url = _save_upload(file, UPLOAD_DIR_BANNER)
    except ValueError as e:
        return error_response(CodeEnum.PARAM_ERROR, str(e))
    return success_response(data={"url": url})
