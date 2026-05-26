from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    code: str = Field(..., description="微信登录 code，mock 模式使用 mock_code")
    inviter_id: str | None = Field(None, description="邀请人 ID")


class UserInfo(BaseModel):
    user_id: str
    nickname: str
    avatar: str
    invite_count: int
    continuous_days: int

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    user_id: str
    is_new: bool
    invite_count: int
    unlocked_features: list[str]
    token: str