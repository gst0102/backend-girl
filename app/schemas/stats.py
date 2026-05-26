from pydantic import BaseModel


class StatsResponse(BaseModel):
    poop_count: int
    sleep_score: float
    continuous_days: int
    beat_users: int
    trend: list[int]