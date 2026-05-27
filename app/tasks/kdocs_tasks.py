"""
KDocs 定时抓取同步任务
- 支持按单个数据源同步（用于独立cron调度）
- 支持全量一次同步（用于批量刷新）
- 使用 DrissionPage 无头浏览器
"""
import asyncio
import logging
from datetime import datetime

from app.services.kdocs_fetcher import fetch_all_sources, fetch_single_source_from_db
from app.services.kdocs_sync_service import sync_all, sync_anime_data

logger = logging.getLogger(__name__)


async def sync_kdocs_source(source_id: int, media_type: str):
    """同步单个数据源"""
    logger.info(f"[数据源 {source_id}] 同步任务开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        loop = asyncio.get_running_loop()
        media_type_result, entries = await fetch_single_source_from_db(source_id)

        if not entries:
            logger.info(f"[数据源 {source_id}] 没有抓取到数据")
            return

        result = await sync_anime_data(entries, media_type_result or media_type)
        logger.info(f"[数据源 {source_id}] 同步完成: +{result.get('inserted', 0)} 新增, ~{result.get('updated', 0)} 更新")
    except Exception as e:
        logger.error(f"[数据源 {source_id}] 同步异常: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def sync_all_kdocs_sources():
    """同步所有启用的数据源（全量刷新用）"""
    logger.info("=" * 60)
    logger.info(f"KDocs 全量同步开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    entries_by_type = await fetch_all_sources()
    if entries_by_type:
        await sync_all(entries_by_type)
    else:
        logger.warning("KDocs 全量同步没有抓取到任何数据")

    logger.info(f"KDocs 全量同步完成")
