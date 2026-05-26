from pydantic import BaseModel, Field


class RecordCreateRequest(BaseModel):
    record_type: str = Field(..., description="记录类型：poop/period/sleep/water 等")
    record_date: str = Field(..., description="记录日期 yyyy-mm-dd")
    record_value: dict | None = Field(None, description="扩展值")


class BadgeEarned(BaseModel):
    id: str
    name: str
    icon: str
    rarity: str


class RecordCreateResponse(BaseModel):
    record_id: int
    continuous_days: int
    badges_earned: list[BadgeEarned]


class DayInfo(BaseModel):
    date: str
    day: int
    has_record: bool
    is_current_month: bool
    is_today: bool = False


class CalendarResponse(BaseModel):
    year: int
    month: int
    today: int
    days: list[DayInfo]
    records_map: dict[str, list[str]]


class FeatureStatus(BaseModel):
    recorded: bool
    unlocked: bool
    day: int | None = None


class TodayStatusResponse(BaseModel):
    features: dict[str, FeatureStatus]