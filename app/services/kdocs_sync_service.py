"""
KDocs 数据同步服务
- 将抓取的结构化数据同步到数据库 animes 表
- 以 title 为主键做增量更新
  - 新条目 → INSERT
  - 已有条目且字段变化 → UPDATE（只变更的字段）
  - 动态字段：episode / status / baidu_url / baidu_password / quark_url / update_time
"""
import logging
import re
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.anime import Anime

logger = logging.getLogger(__name__)


def _parse_title(raw_title):
    """解析原始标题 -> 结构化字段"""
    quality = "1080P"
    if "4K" in raw_title:
        quality = "4K"
    elif "1080P" in raw_title:
        quality = "1080P"
    elif "720P" in raw_title:
        quality = "720P"

    episode = ""
    m = re.search(r'更(\d+\.?\d*)[期集]?', raw_title)
    if m:
        episode = f"更{m.group(1)}"
    else:
        m = re.search(r'(\d+\.?\d*)[期集]全', raw_title)
        if m:
            episode = f"{m.group(1)}集全"

    status = None
    if "完结" in raw_title:
        status = "已完结"
    elif "超前" in raw_title:
        status = "超前点播"
    elif "铂金" in raw_title or "高码" in raw_title:
        status = "珍藏版"

    clean = raw_title.strip()
    clean = re.sub(r'^[\.\s,，、、;；：:！!?？]+|[\.\s,，、、;；：:！!?？]+$', '', clean)

    update_time = None
    tm = re.search(r'(\d{1,2})\.(\d{1,2})', raw_title)
    if tm:
        mo, da = tm.group(1).zfill(2), tm.group(2).zfill(2)
        if int(mo) <= 12:
            update_time = f"{mo}-{da}"

    return {
        "title": clean,
        "quality": quality,
        "episode": episode,
        "status": status,
        "update_time": update_time,
    }


def _title_fingerprint(title):
    """生成标题指纹用于匹配去重"""
    t = title.lower().strip()
    t = re.sub(r'[（(].*?[）)]', '', t)
    t = re.sub(r'[^\w\u4e00-\u9fa5]', '', t)
    return t


async def _get_existing_animes(db: AsyncSession, media_type: str):
    """获取数据库中已存在的指定类型全部番剧"""
    result = await db.execute(
        select(Anime).where(Anime.type == media_type)
    )
    rows = result.scalars().all()
    index = {}
    for r in rows:
        fp = _title_fingerprint(r.title)
        index[fp] = r
    return index


async def sync_anime_data(entries, media_type: str):
    """同步一批数据到数据库"""
    if not entries:
        logger.warning(f"[{media_type}] 无数据，跳过同步")
        return {"inserted": 0, "updated": 0}

    async with async_session() as db:
        existing_map = await _get_existing_animes(db, media_type)
        inserted = 0
        updated = 0

        for entry in entries:
            raw_title = entry.get("title", "")
            parsed = _parse_title(raw_title)
            fingerprint = _title_fingerprint(parsed["title"])

            # 提取链接
            baidu_url = ""
            baidu_password = "1120"
            quark_url = ""
            for link in entry.get("links", []):
                t = link.get("type", "")
                if "百度" in t:
                    baidu_url = link.get("url", "")
                    if "extract_code" in link:
                        baidu_password = link.get("extract_code", "1120")
                elif "夸克" in t:
                    quark_url = link.get("url", "")

            if fingerprint in existing_map:
                existing = existing_map[fingerprint]
                need_update = False
                updates = {}

                if existing.title != parsed["title"]:
                    updates["title"] = parsed["title"]
                    need_update = True
                if existing.episode != parsed["episode"]:
                    updates["episode"] = parsed["episode"]
                    need_update = True
                if existing.status != parsed["status"]:
                    updates["status"] = parsed["status"]
                    need_update = True
                if existing.baidu_url != baidu_url:
                    updates["baidu_url"] = baidu_url
                    need_update = True
                if existing.baidu_password != baidu_password:
                    updates["baidu_password"] = baidu_password
                    need_update = True
                if existing.quark_url != quark_url:
                    updates["quark_url"] = quark_url
                    need_update = True
                if existing.update_time != parsed["update_time"]:
                    updates["update_time"] = parsed["update_time"]
                    need_update = True

                if need_update:
                    updates["updated_at"] = datetime.now()
                    stmt = (
                        update(Anime)
                        .where(Anime.id == existing.id)
                        .values(**updates)
                    )
                    await db.execute(stmt)
                    updated += 1
                    logger.info(f"[{media_type}] 更新: {parsed['title']} -> {updates}")
            else:
                # 新条目 - INSERT
                anime_id = f"{media_type}_{len(existing_map) + inserted + 1}_{fingerprint[:15]}"
                new_anime = Anime(
                    id=anime_id,
                    title=parsed["title"],
                    quality=parsed["quality"],
                    episode=parsed["episode"],
                    status=parsed["status"],
                    baidu_url=baidu_url,
                    baidu_password=baidu_password,
                    quark_url=quark_url,
                    update_time=parsed["update_time"],
                    type=media_type,
                )
                db.add(new_anime)
                inserted += 1
                logger.info(f"[{media_type}] 新增: {parsed['title']}")

        await db.commit()
        logger.info(f"[{media_type}] 同步完成: +{inserted} 新增, ~{updated} 更新")
        return {"inserted": inserted, "updated": updated}


async def sync_all(entries_by_type: dict):
    """同步三个类型的数据"""
    results = {}
    for media_type, entries in entries_by_type.items():
        if entries:
            result = await sync_anime_data(entries, media_type)
            results[media_type] = result
        else:
            logger.warning(f"[{media_type}] 无数据传入")
    return results