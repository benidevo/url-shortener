from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl, field_validator


class UrlCreate(BaseModel):
    url: HttpUrl = Field(
        ..., title="url", description="The URL to shorten", max_length=2048
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, url: HttpUrl) -> HttpUrl:
        url_str = str(url)

        if len(url_str) > 2048:
            raise ValueError("URL must not exceed 2048 characters")

        parsed = urlparse(url_str)

        if parsed.scheme not in ["http", "https"]:
            raise ValueError("Only HTTP and HTTPS URLs are allowed")

        if not parsed.netloc:
            raise ValueError("URL must have a valid host")

        suspicious_patterns = [
            "javascript:",
            "data:",
            "vbscript:",
            "file:",
            "about:",
            "<script",
            "%3Cscript",
            "&#x3C;script",
            "\x3cscript",
        ]

        url_lower = url_str.lower()
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                raise ValueError(f"URL contains suspicious pattern: {pattern}")

        if parsed.hostname:
            # Block localhost and private IPs
            blocked_hosts = [
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "10.",
                "172.16.",
                "172.17.",
                "172.18.",
                "172.19.",
                "172.20.",
                "172.21.",
                "172.22.",
                "172.23.",
                "172.24.",
                "172.25.",
                "172.26.",
                "172.27.",
                "172.28.",
                "172.29.",
                "172.30.",
                "172.31.",
                "192.168.",
                "169.254.",
            ]

            hostname_lower = parsed.hostname.lower()
            for blocked in blocked_hosts:
                if hostname_lower.startswith(blocked):
                    raise ValueError(
                        "URLs to private/internal addresses are not allowed"
                    )

        return url


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
    data: UrlModel | list[UrlModel] | None = Field(
        default=None, title="data", description="The data returned by the request"
    )
