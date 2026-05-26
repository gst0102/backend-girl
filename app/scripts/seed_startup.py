"""
首次部署种子数据
- 在 lifespan 中 create_all 之后调用
- 幂等：已存在的记录不会重复插入
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_models import KDocsSource
from app.models.badge import Badge
from app.models.config_models import ConfigPushTemplate, ConfigUnlock

logger = logging.getLogger(__name__)


async def seed_startup_data(db: AsyncSession):
    """种子数据 - 仅插入缺失的记录"""
    await _seed_config_unlock(db)
    await _seed_config_push_templates(db)
    await _seed_badges(db)
    await _seed_kdocs_sources(db)
    logger.info("种子数据检查完成")


async def _seed_config_unlock(db: AsyncSession):
    """功能解锁阈值"""
    defaults = [
        (1, "sleep", "睡眠记录"),
        (3, "water", "喝水提醒"),
        (8, "anime_remind", "追番提醒"),
        (15, "anime_preview", "追番预告"),
        (30, "anime_drive", "网盘资源"),
    ]
    for threshold, feature_key, feature_name in defaults:
        result = await db.execute(
            select(ConfigUnlock).where(ConfigUnlock.feature_key == feature_key)
        )
        if result.scalar_one_or_none() is None:
            db.add(ConfigUnlock(
                threshold=threshold,
                feature_key=feature_key,
                feature_name=feature_name,
            ))
            logger.info(f"种子 config_unlock: {feature_key} (≥{threshold}人)")


async def _seed_config_push_templates(db: AsyncSession):
    """推送消息模板"""
    defaults = [
        ("msg_invite_progress", "邀请进度更新", "你已经邀请了{count}人，还差{remaining}人就能解锁{feature}", "popup"),
        ("msg_feature_unlock", "新功能解锁", "恭喜！你已解锁{feature}", "popup"),
        ("msg_continuous_7", "连续记录7天", "恭喜你连续记录7天，获得🔥徽章", "popup"),
        ("msg_daily_reminder", "每日提醒", "今天还没记录，点一下只需要2秒", "notice"),
        ("msg_low_activity", "低活跃提醒", "{nickname}，已经7天没记录了，记得来打卡哦！", "popup"),
        ("msg_weekly_report", "周报推送", "本周你记录了{day_count}天，继续保持！", "popup"),
    ]
    for template_id, title, content, channel in defaults:
        result = await db.execute(
            select(ConfigPushTemplate).where(ConfigPushTemplate.template_id == template_id)
        )
        if result.scalar_one_or_none() is None:
            db.add(ConfigPushTemplate(
                template_id=template_id,
                title=title,
                content=content,
                channel=channel,
            ))
            logger.info(f"种子 config_push_templates: {template_id}")


async def _seed_badges(db: AsyncSession):
    """徽章定义"""
    defaults = [
        ("badge_001", "连续拉屎7天", "💩", "rare", "continuous_days", 7),
        ("badge_002", "连续拉屎14天", "💩✨", "epic", "continuous_days", 14),
        ("badge_003", "连续拉屎30天", "💩🏆", "epic", "continuous_days", 30),
        ("badge_004", "记录满7天", "📅", "common", "record_count", 7),
        ("badge_005", "记录满30天", "📅✨", "rare", "record_count", 30),
        ("badge_006", "记录满100天", "📅🏆", "epic", "record_count", 100),
        ("badge_007", "邀请1人", "🤝", "common", "invite_count", 1),
        ("badge_008", "邀请3人", "🤝✨", "rare", "invite_count", 3),
        ("badge_009", "邀请10人", "🤝🏆", "epic", "invite_count", 10),
        ("badge_010", "裂变之王", "🏆", "epic", "invite_count", 30),
    ]
    for badge_id, name, icon, rarity, condition_type, condition_value in defaults:
        result = await db.execute(
            select(Badge).where(Badge.id == badge_id)
        )
        if result.scalar_one_or_none() is None:
            db.add(Badge(
                id=badge_id,
                name=name,
                icon=icon,
                rarity=rarity,
                condition_type=condition_type,
                condition_value=condition_value,
            ))
            logger.info(f"种子 badges: {badge_id}")


async def _seed_kdocs_sources(db: AsyncSession):
    """KDocs 数据源 - 番剧/电影/4K 三个源，确保定时拉取能运行"""
    defaults = [
        {
            "name": "影视剧（番剧）",
            "url": "https://www.kdocs.cn/l/co72a28MWkmI",
            "type": "anime",
            "enabled": True,
            "cron_expression": "*/15 * * * *",
        },
        {
            "name": "电影",
            "url": "https://www.kdocs.cn/l/cmbapmIwVsfi",
            "type": "movie",
            "enabled": True,
            "cron_expression": "0 2 * * *",
        },
        {
            "name": "4K资源",
            "url": "https://www.kdocs.cn/l/cdv0WUisFk3x?openfrom=docs",
            "type": "anime_4k",
            "enabled": True,
            "cron_expression": "0 3 * * *",
        },
    ]
    for src in defaults:
        result = await db.execute(
            select(KDocsSource).where(KDocsSource.url == src["url"])
        )
        if result.scalar_one_or_none() is None:
            db.add(KDocsSource(**src))
            logger.info(f"种子 kdocs_sources: {src['name']} ({src['type']})")