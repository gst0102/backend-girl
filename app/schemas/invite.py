from pydantic import BaseModel, Field


class InviteCreateRequest(BaseModel):
    invitee_openid: str = Field(..., description="被邀请人的 openid")
    invitee_device: str | None = Field(None, description="设备标识")


class InviteCreateResponse(BaseModel):
    invite_count: int
    new_unlocked: list[str]


class RewardProgress(BaseModel):
    threshold: int
    reward: str
    feature_key: str
    status: str
    progress: str | None = None


class InviteProgressResponse(BaseModel):
    current: int
    target: int
    next_threshold: int
    remaining: int
    rewards: list[RewardProgress]


class RankItem(BaseModel):
    rank: int
    user_id: str
    nickname: str
    avatar: str
    invite_count: int


class RankListResponse(BaseModel):
    list: list[RankItem]
    my_rank: int | None = None
    my_invite_count: int | None = None