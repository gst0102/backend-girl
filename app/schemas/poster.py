from pydantic import BaseModel, Field


class PosterGenerateRequest(BaseModel):
    template: str = Field(..., description="模板类型: monthly / couple / badge")
    style: str | None = Field("default", description="风格选择: default / xiaohongshu / cartoon / japanese / vintage")
    badge_id: str | None = Field(None, description="徽章 ID，template=badge 时必填")


class PosterGenerateResponse(BaseModel):
    image_base64: str


class TemplateListResponse(BaseModel):
    templates: list[dict]
