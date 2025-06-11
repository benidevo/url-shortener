from datetime import datetime

from pydantic import BaseModel, Field


class ClickModel(BaseModel):
    ip: str = Field(..., title="ip", description="The IP address of the click")
    city: str = Field(..., title="city", description="The city of the click")
    country: str = Field(..., title="country", description="The country of the click")
    created_at: datetime = Field(
        default_factory=datetime.now,
        title="created_at",
        description="When the click occurred",
    )


class AnalyticsModel(BaseModel):
    short_link: str = Field(..., title="short_link", description="The shortened URL")
    clicks: list[ClickModel] = Field(..., title="clicks", description="The clicks")
    updated_at: datetime = Field(
        default_factory=datetime.now,
        title="updated_at",
        description="The date and time the URL was shortened",
    )


class ResponseModel(BaseModel):
    success: bool = Field(
        default=True, title="success", description="Whether the request was successful"
    )
    data: AnalyticsModel | list[AnalyticsModel] | None = Field(
        default=None, title="data", description="The data returned by the request"
    )
