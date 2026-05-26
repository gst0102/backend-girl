from pydantic import BaseModel, Field
from typing import Optional


class AdConfigUpdateRequest(BaseModel):
    ad_type: str = Field(..., description="广告类型: rewarded_video/banner/custom_ad")
    enabled: bool
    unit_id: Optional[str] = None
    test_unit_id: Optional[str] = None
    position: Optional[str] = None
    sort_order: Optional[int] = None
    description: Optional[str] = None
    ab_test_enabled: Optional[bool] = None
    ab_test_ratio: Optional[float] = None
