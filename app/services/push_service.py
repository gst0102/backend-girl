import json
import logging
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config_models import ConfigPushTemplate
from app.models.push import PushLog
from app.models.record import Record
from app.models.user import User
from app.services.wechat_service import send_subscribe_message

logger = logging.getLogger(__name__)


async def create_push_log(
    db: AsyncSession,
    user_id: UUID,
    template_id: str,
    content: str,
    channel: str = "popup",
    wechat_data: str | None = None,
) -> PushLog:
    """创建推送记录"""
    push_log = PushLog(
        user_id=user_id,
        template_id=template_id,
        content=content,
        channel=channel,
        wechat_data=wechat_data,
        status=0,
    )
    db.add(push_log)
    await db.flush()
    logger.info(f"Created push log for user {user_id}: {template_id}")
    return push_log


async def send_pending_pushes(db: AsyncSession = None):
    """发送待处理的推送（定时任务）"""
    from app.database import async_session
    
    if db is None:
        session = async_session()
        db = await session.__aenter__()
    
    try:
        now = datetime.now()
        result = await db.execute(
            select(PushLog)
            .where(PushLog.status == 0)
            .where(PushLog.created_at <= now)
            .limit(100)
        )
        pending_pushes = result.scalars().all()
        
        for push in pending_pushes:
            success = await _send_push(db, push)
            if success:
                push.status = 1
                push.sent_at = now
            else:
                push.status = 2
        
        if pending_pushes:
            await db.commit()
            logger.info(f"Processed {len(pending_pushes)} pending pushes")
    
    except Exception as e:
        logger.error(f"Error sending pending pushes: {e}")
        if db:
            await db.rollback()
    
    finally:
        if db and session:
            await session.__aexit__(None, None, None)


async def process_pending_pushes(db: AsyncSession, limit: int = 100):
    """兼容旧接口的推送处理函数"""
    now = datetime.now()
    result = await db.execute(
        select(PushLog)
        .where(PushLog.status == 0)
        .where(PushLog.created_at <= now)
        .limit(limit)
    )
    pending_pushes = result.scalars().all()
    
    for push in pending_pushes:
        success = await _send_push(db, push)
        if success:
            push.status = 1
            push.sent_at = now
        else:
            push.status = 2
    
    if pending_pushes:
        await db.commit()
    logger.info(f"Processed {len(pending_pushes)} pending pushes")


async def _send_push(db: AsyncSession, push: PushLog) -> bool:
    """发送单条推送
    1. 如果是 subscribe 渠道 -> 调微信订阅消息 API
    2. 如果是 popup 渠道 -> 仅打日志（前端轮询拉取）
    """
    if push.channel == "subscribe":
        user = await db.get(User, push.user_id)
        if not user:
            logger.warning(f"用户不存在: {push.user_id}")
            return False

        openid = user.openid
        if openid == "mock_openid_fixed":
            logger.info(f"[mock模式] 模拟发送订阅消息给 {openid}: {push.content}")
            return True

        # 查模板配置，获取微信模板 ID
        result = await db.execute(
            select(ConfigPushTemplate).where(ConfigPushTemplate.template_id == push.template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            logger.warning(f"推送模板不存在: {push.template_id}")
            return False

        wechat_template_id = template.wechat_template_id
        if not wechat_template_id:
            logger.warning(f"模板 {push.template_id} 未配置 wechat_template_id，跳过微信推送")
            return False

        # 准备消息数据
        data = {}
        if push.wechat_data:
            try:
                wechat_data_dict = json.loads(push.wechat_data)
                for key, value in wechat_data_dict.items():
                    data[key] = {"value": str(value)[:20]}
            except json.JSONDecodeError:
                logger.warning(f"wechat_data JSON 解析失败: {push.wechat_data}")

        result = await send_subscribe_message(openid, wechat_template_id, data)
        if result:
            logger.info(f"[微信推送成功] 用户: {openid}, 模板: {push.template_id}")
        else:
            logger.warning(f"[微信推送失败] 用户: {openid}, 模板: {push.template_id}")
        return result

    logger.debug(f"[popup] 推送记录: user={push.user_id}, content={push.content}")
    return True


async def get_user_pushes(db: AsyncSession, user_id: UUID) -> list:
    """获取用户的推送列表"""
    result = await db.execute(
        select(PushLog)
        .where(PushLog.user_id == user_id)
        .order_by(PushLog.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()


async def mark_push_as_read(db: AsyncSession, push_id: int) -> bool:
    """标记推送为已读"""
    result = await db.execute(
        update(PushLog)
        .where(PushLog.id == push_id)
        .values(status=3, sent_at=datetime.now())
    )
    await db.commit()
    return result.rowcount > 0


async def clean_old_pushes(db: AsyncSession, days_to_keep: int = 30):
    """清理过期的推送记录"""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    result = await db.execute(
        PushLog.__table__.delete().where(PushLog.created_at < cutoff_date)
    )
    await db.commit()
    logger.info(f"Cleaned {result.rowcount} old pushes")


async def send_daily_reminders(db: AsyncSession):
    """发送每日提醒推送"""
    today = date.today()
    
    result = await db.execute(
        select(Record.user_id)
        .where(Record.record_date == today)
        .distinct()
    )
    recorded_user_ids = {row[0] for row in result.all()}
    
    result = await db.execute(
        select(User).where(User.activity_level != "inactive")
    )
    active_users = result.scalars().all()
    
    result = await db.execute(
        select(ConfigPushTemplate).where(ConfigPushTemplate.template_id == "msg_daily_reminder")
    )
    template = result.scalar_one_or_none()
    if not template:
        logger.warning("Template not found: msg_daily_reminder")
        return
    
    count = 0
    for user in active_users:
        if user.id not in recorded_user_ids:
            today_str = today.strftime("%Y年%m月%d日")
            wechat_data = json.dumps({"thing1": "今日打卡提醒", "date3": today_str})
            await create_push_log(
                db,
                user.id,
                template.template_id,
                template.content,
                template.channel,
                wechat_data=wechat_data,
            )
            count += 1
    
    logger.info(f"Sent daily reminders to {count} users")