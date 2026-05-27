import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from app.tasks.daily_tasks import (
    check_low_activity_users,
    clean_expired_invites,
    send_daily_reminders,
    update_continuous_days,
    update_user_activity,
)
from app.tasks.hourly_tasks import process_pending_pushes
from app.tasks.kdocs_tasks import sync_all_kdocs_sources, sync_kdocs_source
from app.tasks.weekly_tasks import send_weekly_report, update_rank_cache

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(
    jobstores={"default": MemoryJobStore()},
    timezone=ZoneInfo("Asia/Shanghai"),
)

SCHEDULER_TZ = ZoneInfo("Asia/Shanghai")


def start_scheduler():
    # 每日任务（00:00 执行）
    scheduler.add_job(update_user_activity, "cron", hour=0, minute=0, id="update_user_activity")
    scheduler.add_job(update_continuous_days, "cron", hour=0, minute=2, id="update_continuous_days")
    scheduler.add_job(check_low_activity_users, "cron", hour=0, minute=10, id="check_low_activity_users")
    scheduler.add_job(clean_expired_invites, "cron", hour=0, minute=20, id="clean_expired_invites")
    
    # KDocs 数据同步注册一个启动后延迟执行的初始化任务
    scheduler.add_job(
        init_kdocs_jobs_after_start, "date",
        run_date=datetime.now(SCHEDULER_TZ),
        id="init_kdocs_jobs",
        max_instances=1,
    )

    # 每日提醒（20:00 执行）
    scheduler.add_job(send_daily_reminders, "cron", hour=20, minute=0, id="send_daily_reminders")

    # 每周任务
    scheduler.add_job(update_rank_cache, "cron", day_of_week="mon", hour=0, minute=30, id="update_rank_cache")
    scheduler.add_job(send_weekly_report, "cron", day_of_week="sun", hour=20, minute=0, id="send_weekly_report")

    # 每小时任务
    scheduler.add_job(process_pending_pushes, "cron", minute=0, id="process_pending_pushes")

    scheduler.start()
    logger.info("Scheduler started successfully with all jobs registered")


async def init_kdocs_jobs_after_start():
    """从数据库读取所有启用的数据源，按各自cron注册独立定时任务（启动后异步执行）"""
    import asyncio
    from app.database import async_session
    from app.models.anime import Anime
    from app.models.admin_models import KDocsSource
    from sqlalchemy import func, select

    try:
        async with async_session() as db:
            result = await db.execute(select(KDocsSource).where(KDocsSource.enabled == True))
            sources = result.scalars().all()
            source_types = sorted({src.type for src in sources})
            counts = {}
            if source_types:
                count_result = await db.execute(
                    select(Anime.type, func.count(Anime.id))
                    .where(Anime.type.in_(source_types))
                    .group_by(Anime.type)
                )
                counts = dict(count_result.all())
    except Exception as e:
        logger.warning(f"读取数据源时出错（可能是首次部署，表不存在）: {e}")
        sources = []
        source_types = []
        counts = {}

    if not sources:
        logger.info("没有启用的KDocs数据源，跳过注册定时任务")
        return

    for src in sources:
        try:
            cron_parts = src.cron_expression.strip().split()
            if len(cron_parts) >= 5:
                minute, hour = cron_parts[0], cron_parts[1]
                job_id = f"sync_kdocs_source_{src.id}"
                scheduler.add_job(
                    sync_kdocs_source,
                    "cron",
                    hour=hour,
                    minute=minute,
                    args=[src.id, src.type],
                    id=job_id,
                    replace_existing=True,
                )
                logger.info(f"注册数据源[{src.name}]定时同步: {src.cron_expression}")
            else:
                logger.warning(f"数据源[{src.name}]的cron表达式无效: {src.cron_expression}")
        except Exception as e:
            logger.warning(f"注册数据源[{src.name}]定时任务失败: {e}")

    initial_sync_enabled = os.getenv("KDOCS_INITIAL_FULL_SYNC", "1").lower() in {"1", "true", "yes"}
    missing_types = [media_type for media_type in source_types if counts.get(media_type, 0) == 0]
    if initial_sync_enabled and missing_types:
        scheduler.add_job(
            sync_all_kdocs_sources,
            "date",
            run_date=datetime.now(SCHEDULER_TZ),
            id="initial_kdocs_full_sync",
            replace_existing=True,
            max_instances=1,
        )
        logger.info(f"KDocs 检测到空数据类型 {missing_types}，已注册首次全量同步任务")


def shutdown_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shutdown completed")
