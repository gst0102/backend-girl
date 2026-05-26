from pydantic import BaseModel


class BadgeInfo(BaseModel):
    id: str
    name: str
    icon: str
    rarity: str
    earned_at: str | None = None


class LockedBadgeInfo(BaseModel):
    id: str
    name: str
    icon: str
    rarity: str
    condition: str


class BadgeListResponse(BaseModel):
    total: int
    owned: int
    owned_badges: list[BadgeInfo]
    locked_badges: list[LockedBadgeInfo]


class BadgeDetailResponse(BaseModel):
    id: str
    name: str
    icon: str
    rarity: str
    condition_type: str
    condition_value: str
    description: str = ""
    earned_at: str | None = None