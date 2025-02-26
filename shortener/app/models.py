from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


class UrlCreate(BaseModel):
    url: HttpUrl = Field(..., title="url", description="The URL to shorten")


class UrlModel(BaseModel):
    link: HttpUrl = Field(..., title="link", description="The URL to shorten")
    short_link: str = Field(..., title="short_link", description="The shortened URL")
    created_at: datetime = Field(
        default_factory=datetime.now,
        title="created_at",
        description="The date and time the URL was shortened",
    )

    def __eq__(self, value):
        return self.short_link == value.short_link


class ResponseModel(BaseModel):
    success: bool = Field(
        default=True, title="success", description="Whether the request was successful"
    )
    data: Optional[Union[UrlModel, List[UrlModel]]] = Field(
        default=None, title="data", description="The data returned by the request"
    )
