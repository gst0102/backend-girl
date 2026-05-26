import json
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func, delete, update, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AdStats,
    Banner,
    KDocsSource,
    MineApp,
    ReserveConfig,
    User,
    UserBadge,
    UserFeature,
)
from app.models.config_models import AdConfig, ConfigUnlock, MarqueeConfig, MineSection, SystemConfig


async def get_user_list(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    status_filter: str | None = None,
) -> dict:
    base = select(User)
    count_base = select(func.count(User.id))

    if keyword:
        kw = f"%{keyword}%"
        base = base.where((User.nickname.ilike(kw)) | (User.id.cast(str).ilike(kw)))
        count_base = count_base.where((User.nickname.ilike(kw)) | (User.id.cast(str).ilike(kw)))
    if status_filter:
        base = base.where(User.activity_level == status_filter)
        count_base = count_base.where(User.activity_level == status_filter)

    total_result = await db.execute(count_base)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        base.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    rows = []
    for u in users:
        uf_result = await db.execute(
            select(UserFeature.feature_key).where(UserFeature.user_id == u.id)
        )
        unlocked = [r[0] for r in uf_result.all()]
        rows.append({
            "user_id": str(u.id),
            "nickname": u.nickname,
            "avatar": u.avatar or "",
            "invite_count": u.invite_count or 0,
            "continuous_days": u.continuous_days or 0,
            "unlocked_features": unlocked,
            "status": u.activity_level or "active",
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "",
        })

    return {"total": total, "list": rows}


async def update_invite_count(db: AsyncSession, user_id: UUID, invite_count: int) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise ValueError("USER_NOT_FOUND")
    user.invite_count = invite_count
    await db.flush()


async def release_invite(db: AsyncSession, user_id: UUID, feature_key: str) -> None:
    uf_result = await db.execute(
        select(UserFeature).where(UserFeature.user_id == user_id, UserFeature.feature_key == feature_key)
    )
    uf = uf_result.scalar_one_or_none()
    if not uf:
        uf = UserFeature(user_id=user_id, feature_key=feature_key, unlocked=True)
        db.add(uf)
    else:
        uf.unlocked = True
    await db.flush()


async def get_overview(db: AsyncSession) -> dict:
    today = date.today()
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar() or 0

    result = await db.execute(
        select(func.count(User.id)).where(func.date(User.created_at) == today)
    )
    today_new = result.scalar() or 0

    from app.models.record import Record
    result = await db.execute(select(func.count(Record.id)))
    total_records = result.scalar() or 0

    result = await db.execute(
        select(func.count(Record.id)).where(Record.record_date == today)
    )
    today_records = result.scalar() or 0

    result = await db.execute(select(func.count()).where(User.invite_count.isnot(None)))
    total_invites = result.scalar() or 0

    result = await db.execute(
        select(func.sum(User.invite_count)).where(User.invite_count.isnot(None))
    )
    total_invite_sum = result.scalar() or 0

    return {
        "total_users": total_users,
        "today_new_users": today_new,
        "total_records": total_records,
        "today_records": today_records,
        "total_invites": total_invite_sum,
        "today_invites": 0,
    }


async def get_user_trend(db: AsyncSession, days: int = 7) -> dict:
    labels = []
    values = []
    for i in range(days - 1, -1, -1):
        d = date.today() - timedelta(days=i)
        labels.append(f"{d.month}/{d.day}")
        result = await db.execute(
            select(func.count(User.id)).where(func.date(User.created_at) == d)
        )
        values.append(result.scalar() or 0)
    return {"labels": labels, "values": values}


async def get_ad_config(db: AsyncSession) -> dict:
    result = await db.execute(select(AdConfig))
    ads = result.scalars().all()
    config = {}
    for ad in ads:
        key = ad.ad_type.replace("-", "_")
        item = {
            "enabled": ad.enabled,
            "unit_id": ad.unit_id or "",
            "test_unit_id": ad.test_unit_id or "",
            "position": ad.position or "",
            "description": ad.description or "",
            "sort_order": ad.sort_order or 0,
        }
        if key == "custom_ad":
            item["insert_interval"] = ad.sort_order or 3
        config[key] = item

    # 确保三种广告类型都有默认值
    defaults = {
        "rewarded_video": {"enabled": False, "unit_id": "", "test_unit_id": "", "position": "", "description": "用户点击复制链接时播放激励视频"},
        "banner": {"enabled": False, "unit_id": "", "test_unit_id": "", "position": "bottom", "description": "首页底部Banner广告"},
        "custom_ad": {"enabled": False, "unit_id": "", "test_unit_id": "", "position": "list", "description": "番剧列表中插入卡片广告", "insert_interval": 3},
    }
    for k, v in defaults.items():
        if k not in config:
            config[k] = v

    # A/B 测试配置（存在第一个 ad_config 记录中）
    ab_test_enabled = False
    ab_test_ratio = 0.5
    if ads:
        ab_test_enabled = ads[0].ab_test_enabled
        ab_test_ratio = ads[0].ab_test_ratio
    config["ab_test"] = {"enabled": ab_test_enabled, "test_ratio": ab_test_ratio}

    return config


async def update_ad_config(db: AsyncSession, config_data: dict) -> None:
    for key, vals in config_data.items():
        if key == "ab_test":
            # A/B 测试配置：存储到所有 ad_config 记录中
            result = await db.execute(select(AdConfig))
            for ad in result.scalars().all():
                if "enabled" in vals:
                    ad.ab_test_enabled = vals["enabled"]
                if "test_ratio" in vals:
                    ad.ab_test_ratio = vals["test_ratio"]
                ad.updated_at = datetime.now()
            continue
        if not isinstance(vals, dict):
            continue
        pos = key.replace("_", "-")
        result = await db.execute(select(AdConfig).where(AdConfig.ad_type == pos))
        ad = result.scalar_one_or_none()
        if ad:
            if "enabled" in vals:
                ad.enabled = vals["enabled"]
            if "unit_id" in vals:
                ad.unit_id = vals["unit_id"]
            if "test_unit_id" in vals:
                ad.test_unit_id = vals["test_unit_id"]
            if "position" in vals:
                ad.position = vals["position"]
            if "description" in vals:
                ad.description = vals["description"]
            if "sort_order" in vals:
                ad.sort_order = vals["sort_order"]
            if "insert_interval" in vals:
                ad.sort_order = vals["insert_interval"]
            ad.updated_at = datetime.now()
        else:
            ad = AdConfig(
                ad_type=pos,
                enabled=vals.get("enabled", False),
                unit_id=vals.get("unit_id", ""),
                test_unit_id=vals.get("test_unit_id", ""),
                position=vals.get("position", ""),
                sort_order=vals.get("sort_order", vals.get("insert_interval", 0)),
                description=vals.get("description", ""),
            )
            db.add(ad)
    await db.flush()


async def get_ad_stats(db: AsyncSession, start_date: str | None = None, end_date: str | None = None) -> dict:
    base = select(AdStats)
    if start_date:
        base = base.where(AdStats.stats_date >= start_date)
    if end_date:
        base = base.where(AdStats.stats_date <= end_date)
    result = await db.execute(base)
    all_stats = result.scalars().all()

    positions = {"rewarded_video": {"show_count": 0, "click_count": 0, "estimated_revenue": 0.0},
                 "banner": {"show_count": 0, "click_count": 0, "estimated_revenue": 0.0},
                 "custom_ad": {"show_count": 0, "click_count": 0, "estimated_revenue": 0.0}}
    total_revenue = 0.0
    for s in all_stats:
        key = s.position.replace("-", "_")
        if key in positions:
            if s.action == "show":
                positions[key]["show_count"] += 1
            elif s.action == "click":
                positions[key]["click_count"] += 1
            positions[key]["estimated_revenue"] += s.estimated_revenue
            total_revenue += s.estimated_revenue

    return {**positions, "total_revenue": round(total_revenue, 2)}


async def get_ad_user_contribution(db: AsyncSession, page: int = 1, page_size: int = 20) -> dict:
    # 按用户聚合：总行为数、预估收益
    agg = (
        select(
            AdStats.user_id,
            func.count().label("total_actions"),
            func.sum(AdStats.estimated_revenue).label("revenue"),
        )
        .where(AdStats.user_id.isnot(None))
        .group_by(AdStats.user_id)
    )
    subq = agg.subquery()

    total_result = await db.execute(select(func.count()).select_from(subq))
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(subq.c.user_id, subq.c.total_actions, subq.c.revenue)
        .order_by(subq.c.revenue.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = result.all()

    list_data = []
    for row in rows:
        uid = row.user_id
        # 按广告位分项统计
        pos_result = await db.execute(
            select(AdStats.position, AdStats.action, func.count().label("cnt"))
            .where(AdStats.user_id == uid)
            .group_by(AdStats.position, AdStats.action)
        )
        pos_stats = {}
        for pos_name, action, cnt in pos_result.all():
            key = pos_name or "unknown"
            if key not in pos_stats:
                pos_stats[key] = {"views": 0, "clicks": 0}
            if action == "click":
                pos_stats[key]["clicks"] = cnt
            else:
                pos_stats[key]["views"] += cnt

        user = await db.get(User, uid) if uid else None
        list_data.append({
            "user_id": str(uid) if uid else "",
            "nickname": user.nickname if user else "未知",
            "rewarded_video_views": pos_stats.get("rewarded-video", {}).get("views", 0),
            "rewarded_video_clicks": pos_stats.get("rewarded-video", {}).get("clicks", 0),
            "banner_clicks": pos_stats.get("banner", {}).get("clicks", 0),
            "custom_ad_clicks": pos_stats.get("custom-ad", {}).get("clicks", 0),
            "estimated_revenue": round(float(row.revenue or 0), 2),
        })
    return {"list": list_data, "total": total, "page": page, "page_size": page_size}


async def get_marquee_config(db: AsyncSession) -> dict:
    result = await db.execute(select(MarqueeConfig).limit(1))
    m = result.scalar_one_or_none()
    if not m:
        return {"enabled": False, "target": 5, "text_template": "", "interval": 5000}
    return {"enabled": m.enabled, "target": 5, "text_template": m.content or "", "interval": 5000}


async def update_marquee_config(db: AsyncSession, data: dict) -> None:
    result = await db.execute(select(MarqueeConfig).limit(1))
    m = result.scalar_one_or_none()
    if not m:
        m = MarqueeConfig()
        db.add(m)
    m.enabled = data.get("enabled", m.enabled)
    if "text_template" in data:
        m.content = data["text_template"]
    m.updated_at = datetime.now()
    await db.flush()


async def get_banners(db: AsyncSession) -> dict:
    result = await db.execute(select(Banner).order_by(Banner.sort_order))
    banners = result.scalars().all()
    return {"list": [
        {"id": b.id, "title": b.title, "image_url": b.image_url, "link_url": b.link_url or "",
         "sort_order": b.sort_order, "status": b.status,
         "created_at": b.created_at.strftime("%Y-%m-%d %H:%M:%S") if b.created_at else ""}
        for b in banners
    ]}


async def create_banner(db: AsyncSession, data: dict) -> Banner:
    b = Banner(
        title=data["title"], image_url=data["image_url"],
        link_url=data.get("link_url", ""), sort_order=data.get("sort_order", 0),
        status=data.get("status", "active"),
    )
    db.add(b)
    await db.flush()
    await db.refresh(b)
    return b


async def update_banner(db: AsyncSession, banner_id: int, data: dict) -> Banner:
    b = await db.get(Banner, banner_id)
    if not b:
        raise ValueError("BANNER_NOT_FOUND")
    for field in ["title", "image_url", "link_url", "sort_order", "status"]:
        if field in data:
            setattr(b, field, data[field])
    b.updated_at = datetime.now()
    await db.flush()
    await db.refresh(b)
    return b


async def delete_banner(db: AsyncSession, banner_id: int) -> None:
    b = await db.get(Banner, banner_id)
    if not b:
        raise ValueError("BANNER_NOT_FOUND")
    await db.delete(b)
    await db.flush()


async def toggle_banner(db: AsyncSession, banner_id: int, status: str) -> Banner:
    b = await db.get(Banner, banner_id)
    if not b:
        raise ValueError("BANNER_NOT_FOUND")
    b.status = status
    b.updated_at = datetime.now()
    await db.flush()
    await db.refresh(b)
    return b


async def get_unlock_config(db: AsyncSession) -> dict:
    result = await db.execute(select(ConfigUnlock))
    rows = result.scalars().all()
    return {r.feature_key: r.threshold for r in rows}


async def update_unlock_config(db: AsyncSession, config: dict) -> None:
    for k, v in config.items():
        result = await db.execute(select(ConfigUnlock).where(ConfigUnlock.feature_key == k))
        cu = result.scalar_one_or_none()
        if cu:
            cu.threshold = v
        else:
            cu = ConfigUnlock(feature_key=k, feature_name=k, threshold=v)
            db.add(cu)
    await db.flush()


async def get_reserve_config(db: AsyncSession) -> dict:
    result = await db.execute(select(ReserveConfig).where(ReserveConfig.config_type == "official_account"))
    row = result.scalar_one_or_none()
    if not row:
        return {"official_account": {"enabled": False, "name": "", "qrcode_url": "", "description": ""}}
    oa = json.loads(row.config_data)
    return {"official_account": oa}


async def update_reserve_config(db: AsyncSession, data: dict) -> None:
    oa = data.get("official_account")
    if not oa:
        return
    result = await db.execute(select(ReserveConfig).where(ReserveConfig.config_type == "official_account"))
    row = result.scalar_one_or_none()
    if row:
        row.config_data = json.dumps(oa, ensure_ascii=False)
    else:
        db.add(ReserveConfig(config_type="official_account", config_data=json.dumps(oa, ensure_ascii=False)))
    await db.flush()


async def get_kdocs_sources(db: AsyncSession) -> dict:
    result = await db.execute(select(KDocsSource))
    rows = result.scalars().all()
    return {"list": [
        {"id": r.id, "name": r.name, "url": r.url, "type": r.type, "enabled": r.enabled,
         "cron_expression": r.cron_expression,
         "last_sync_at": r.last_sync_at.strftime("%Y-%m-%d %H:%M:%S") if r.last_sync_at else None,
         "last_sync_result": r.last_sync_result or ""}
        for r in rows
    ]}


async def create_kdocs_source(db: AsyncSession, data: dict) -> KDocsSource:
    ks = KDocsSource(
        name=data["name"], url=data["url"], type=data["type"],
        enabled=data.get("enabled", True),
        cron_expression=data.get("cron_expression", "0 2,14 * * *"),
    )
    db.add(ks)
    await db.flush()
    await db.refresh(ks)
    return ks


async def update_kdocs_source(db: AsyncSession, source_id: int, data: dict) -> KDocsSource:
    ks = await db.get(KDocsSource, source_id)
    if not ks:
        raise ValueError("SOURCE_NOT_FOUND")
    for field in ["url", "name", "type", "enabled", "cron_expression"]:
        if field in data:
            setattr(ks, field, data[field])
    ks.updated_at = datetime.now()
    await db.flush()
    await db.refresh(ks)
    return ks


async def delete_kdocs_source(db: AsyncSession, source_id: int) -> None:
    ks = await db.get(KDocsSource, source_id)
    if not ks:
        raise ValueError("SOURCE_NOT_FOUND")
    await db.delete(ks)
    await db.flush()


async def get_mine_apps(db: AsyncSession) -> dict:
    result = await db.execute(select(MineApp).order_by(MineApp.sort_order))
    apps = result.scalars().all()
    return {"list": [
        {"id": a.id, "name": a.name, "app_id": a.app_id, "path": a.path or "/pages/index",
         "icon": a.icon or "", "sort_order": a.sort_order, "enabled": a.enabled}
        for a in apps
    ]}


async def create_mine_app(db: AsyncSession, data: dict) -> MineApp:
    ma = MineApp(
        name=data["name"], app_id=data["app_id"],
        path=data.get("path", "/pages/index"), icon=data.get("icon", ""),
        sort_order=data.get("sort_order", 0), enabled=data.get("enabled", True),
    )
    db.add(ma)
    await db.flush()
    await db.refresh(ma)
    return ma


async def update_mine_app(db: AsyncSession, app_id: int, data: dict) -> MineApp:
    ma = await db.get(MineApp, app_id)
    if not ma:
        raise ValueError("APP_NOT_FOUND")
    for field in ["name", "app_id", "path", "icon", "sort_order", "enabled"]:
        if field in data:
            setattr(ma, field, data[field])
    ma.updated_at = datetime.now()
    await db.flush()
    await db.refresh(ma)
    return ma


async def delete_mine_app(db: AsyncSession, app_id: int) -> None:
    ma = await db.get(MineApp, app_id)
    if not ma:
        raise ValueError("APP_NOT_FOUND")
    await db.delete(ma)
    await db.flush()


async def sort_mine_apps(db: AsyncSession, ids: list[int]) -> None:
    for order, app_id in enumerate(ids):
        await db.execute(update(MineApp).where(MineApp.id == app_id).values(sort_order=order))
    await db.flush()


# ===== 系统配置 =====
async def get_system_config(db: AsyncSession) -> dict:
    result = await db.execute(select(SystemConfig))
    rows = result.scalars().all()
    return {r.config_key: r.config_value for r in rows}


async def update_system_config(db: AsyncSession, config: dict) -> None:
    for key, value in config.items():
        result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == key))
        sc = result.scalar_one_or_none()
        if sc:
            sc.config_value = str(value) if not isinstance(value, str) else value
            sc.updated_at = datetime.now()
        else:
            sc = SystemConfig(config_key=key, config_value=str(value) if not isinstance(value, str) else value)
            db.add(sc)
    await db.flush()


async def update_system_config_item(db: AsyncSession, key: str, value: str) -> None:
    result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == key))
    sc = result.scalar_one_or_none()
    if sc:
        sc.config_value = value
        sc.updated_at = datetime.now()
    else:
        sc = SystemConfig(config_key=key, config_value=value)
        db.add(sc)
    await db.flush()


# ===== Mine 板块配置 =====
async def get_mine_sections(db: AsyncSession) -> dict:
    result = await db.execute(select(MineSection).order_by(MineSection.sort_order))
    rows = result.scalars().all()
    return {"list": [
        {
            "id": s.id, "section_key": s.section_key, "title": s.title,
            "enabled": s.enabled, "sort_order": s.sort_order,
            "description": s.description or "",
        }
        for s in rows
    ]}


async def update_mine_section(db: AsyncSession, section_key: str, data: dict) -> MineSection:
    result = await db.execute(select(MineSection).where(MineSection.section_key == section_key))
    s = result.scalar_one_or_none()
    if not s:
        s = MineSection(section_key=section_key, title=data.get("title", section_key))
        db.add(s)
    for field in ["title", "enabled", "sort_order", "description"]:
        if field in data:
            setattr(s, field, data[field])
    s.updated_at = datetime.now()
    await db.flush()
    await db.refresh(s)
    return s


async def update_mine_sections_batch(db: AsyncSession, sections: list[dict]) -> None:
    for item in sections:
        key = item.get("section_key")
        if not key:
            continue
        await update_mine_section(db, key, item)
    await db.flush()


# ===== 公开接口: 广告配置 =====
async def get_public_ad_config(db: AsyncSession) -> dict:
    """小程序端获取广告配置"""
    result = await db.execute(select(AdConfig))
    ads = result.scalars().all()
    config = {}
    ab_test_enabled = False
    ab_test_ratio = 0.5
    for ad in ads:
        key = ad.ad_type.replace("-", "_")
        if ad.ab_test_enabled:
            ab_test_enabled = True
            ab_test_ratio = ad.ab_test_ratio
        config[key] = {
            "enabled": ad.enabled,
            "unit_id": ad.unit_id or "",
            "test_unit_id": ad.test_unit_id or "",
            "position": ad.position or "",
            "sort_order": ad.sort_order or 0,
        }
    defaults = {
        "rewarded_video": {"enabled": False, "unit_id": "", "test_unit_id": "", "position": ""},
        "banner": {"enabled": False, "unit_id": "", "test_unit_id": "", "position": "bottom"},
        "custom_ad": {"enabled": False, "unit_id": "", "test_unit_id": "", "position": "list", "sort_order": 3},
    }
    for k, v in defaults.items():
        if k not in config:
            config[k] = v
    return {
        **config,
        "ab_test": {"enabled": ab_test_enabled, "test_ratio": ab_test_ratio},
    }


# ===== 公开接口: Banner列表 =====
async def get_public_banners(db: AsyncSession) -> dict:
    result = await db.execute(
        select(Banner).where(Banner.status == "active").order_by(Banner.sort_order)
    )
    banners = result.scalars().all()
    return {"list": [
        {"id": b.id, "title": b.title, "image_url": b.image_url, "link_url": b.link_url or ""}
        for b in banners
    ]}


# ===== 公开接口: Mine板块 =====
async def get_public_mine_sections(db: AsyncSession) -> dict:
    result = await db.execute(
        select(MineSection).where(MineSection.enabled == True).order_by(MineSection.sort_order)
    )
    rows = result.scalars().all()
    return {"list": [
        {"section_key": s.section_key, "title": s.title, "sort_order": s.sort_order}
        for s in rows
    ]}