from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel


class ClickModel(BaseModel):
    ip: str
    city: str
    country: str


class AnalyticsModel(BaseModel):
    short_link: str
    clicks: List[ClickModel]
    updated_at: datetime


class ResponseModel(BaseModel):
    success: bool = True
    data: Optional[Union[AnalyticsModel, List[AnalyticsModel]]] = None
