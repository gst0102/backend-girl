from pydantic import BaseModel, Field


class AnimeSubscribeRequest(BaseModel):
    anime_id: str = Field(..., description="番剧 ID")


class GetLinkRemindRequest(BaseModel):
    anime_id: str = Field(..., description="番剧 ID")
    current_episode: str | None = Field(None, description="催更时的集数，如 更40")


class AnimeLibraryQuery(BaseModel):
    keyword: str | None = Field(None, description="搜索关键词")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class AnimeScheduleQuery(BaseModel):
    week: str | None = Field(None, description="周次，格式 2026-W21")


class AnimeDriveQuery(BaseModel):
    episode: int | None = Field(None, ge=1, description="指定集数，默认最新")


class SubscribedAnimeItem(BaseModel):
    anime_id: str
    name: str
    cover: str
    update_day: int
    update_day_text: str
    latest_episode: int
    is_today_update: bool


class SubscribedListResponse(BaseModel):
    list: list[SubscribedAnimeItem]


class LibraryAnimeItem(BaseModel):
    anime_id: str
    name: str
    cover: str
    update_day: int
    update_day_text: str
    description: str | None
    is_subscribed: bool


class LibraryListResponse(BaseModel):
    total: int
    list: list[LibraryAnimeItem]


class ScheduleAnimeItem(BaseModel):
    anime_id: str
    name: str
    episode: int


class ScheduleDayBlock(BaseModel):
    day: int
    day_text: str
    animes: list[ScheduleAnimeItem]


class ScheduleResponse(BaseModel):
    schedule: list[ScheduleDayBlock]


class DriveResourceResponse(BaseModel):
    url: str
    password: str | None
    expire_at: str | None


DAY_TEXT_MAP = {
    1: "周一", 2: "周二", 3: "周三", 4: "周四",
    5: "周五", 6: "周六", 7: "周日",
}