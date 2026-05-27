from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anime import Anime, AnimeReminder, UserAnimeSubscription


def _dt_iso(value) -> str:
    return value.isoformat() if value else ""


def _anime_item(a: Anime, is_subscribed: bool, is_reminded: bool | None = None) -> dict:
    item = {
        "anime_id": a.id,
        "title": a.title,
        "quality": a.quality or "",
        "episode": a.episode or "",
        "status": a.status,
        "baidu_url": a.baidu_url or "",
        "baidu_password": a.baidu_password or "",
        "quark_url": a.quark_url or "",
        "update_time": a.update_time or "",
        "created_at": _dt_iso(a.created_at),
        "updated_at": _dt_iso(a.updated_at),
        "is_subscribed": is_subscribed,
    }
    if is_reminded is not None:
        item["is_reminded"] = is_reminded
    return item


async def get_anime_library(
    db: AsyncSession,
    user_id: UUID,
    type: str | None = "anime",
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    base_query = select(Anime)
    count_query = select(Anime)

    # 类型过滤
    if type:
        base_query = base_query.where(Anime.type == type)
        count_query = count_query.where(Anime.type == type)

    # 关键词搜索
    if keyword:
        kw = f"%{keyword}%"
        base_query = base_query.where(Anime.title.ilike(kw))
        count_query = count_query.where(Anime.title.ilike(kw))

    # 总数查询
    total_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
    total = total_result.scalar() or 0

    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.order_by(Anime.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    animes = result.scalars().all()

    # 获取用户的订阅和催更状态
    sub_result = await db.execute(
        select(UserAnimeSubscription.anime_id).where(UserAnimeSubscription.user_id == user_id)
    )
    subscribed_ids = {row[0] for row in sub_result.all()}

    reminder_result = await db.execute(
        select(AnimeReminder.anime_id).where(AnimeReminder.user_id == user_id, AnimeReminder.is_reminded == True)
    )
    reminded_ids = {row[0] for row in reminder_result.all()}

    return {
        "total": total,
        "list": [
            _anime_item(a, is_subscribed=a.id in subscribed_ids, is_reminded=a.id in reminded_ids)
            for a in animes
        ],
    }


async def get_subscribed_list(db: AsyncSession, user_id: UUID) -> dict:
    result = await db.execute(
        select(Anime).join(
            UserAnimeSubscription,
            (UserAnimeSubscription.anime_id == Anime.id)
            & (UserAnimeSubscription.user_id == user_id),
        ).order_by(Anime.updated_at.desc())
    )
    animes = result.scalars().all()

    reminder_result = await db.execute(
        select(AnimeReminder.anime_id).where(
            AnimeReminder.user_id == user_id, AnimeReminder.is_reminded == True
        )
    )
    reminded_ids = {row[0] for row in reminder_result.all()}

    return {
        "list": [
            _anime_item(a, is_subscribed=True, is_reminded=a.id in reminded_ids)
            for a in animes
        ],
    }


async def subscribe_anime(db: AsyncSession, user_id: UUID, anime_id: str) -> None:
    anime = await db.get(Anime, anime_id)
    if anime is None:
        raise ValueError("ANIME_NOT_FOUND")

    result = await db.execute(
        select(UserAnimeSubscription).where(
            UserAnimeSubscription.user_id == user_id,
            UserAnimeSubscription.anime_id == anime_id,
        )
    )
    if result.scalar_one_or_none() is not None:
        raise ValueError("ALREADY_SUBSCRIBED")

    sub = UserAnimeSubscription(user_id=user_id, anime_id=anime_id)
    db.add(sub)
    await db.flush()


async def unsubscribe_anime(db: AsyncSession, user_id: UUID, anime_id: str) -> None:
    anime = await db.get(Anime, anime_id)
    if anime is None:
        raise ValueError("ANIME_NOT_FOUND")

    await db.execute(
        delete(UserAnimeSubscription).where(
            UserAnimeSubscription.user_id == user_id,
            UserAnimeSubscription.anime_id == anime_id,
        )
    )
    await db.flush()


async def get_link_and_remind(db: AsyncSession, user_id: UUID, anime_id: str, current_episode: str | None = None) -> dict:
    anime = await db.get(Anime, anime_id)
    if anime is None:
        raise ValueError("ANIME_NOT_FOUND")

    # 获取或创建催更记录
    reminder_result = await db.execute(
        select(AnimeReminder).where(
            AnimeReminder.user_id == user_id,
            AnimeReminder.anime_id == anime_id
        )
    )
    reminder = reminder_result.scalar_one_or_none()
    
    if reminder is None:
        reminder = AnimeReminder(
            user_id=user_id, 
            anime_id=anime_id, 
            is_reminded=True,
            current_episode=current_episode
        )
        db.add(reminder)
    else:
        reminder.is_reminded = True
        reminder.current_episode = current_episode

    await db.flush()

    return {
        "baidu_url": anime.baidu_url or "",
        "baidu_password": anime.baidu_password or "",
        "quark_url": anime.quark_url or "",
        "is_reminded": True
    }
