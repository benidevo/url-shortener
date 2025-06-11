import asyncio
import base64
import hashlib
import logging
import secrets
from datetime import datetime

from pydantic import HttpUrl

from app.constants import NANOSECONDS_MULTIPLIER, SHORT_URL_LENGTH
from app.grpc.client import AnalyticsClient
from app.models import UrlModel
from app.repository import UrlRepository

logger = logging.getLogger(__name__)


class UrlShortenerService:
    MAX_RETRIES = 5

    def __init__(self, repository: UrlRepository, analytics_client: AnalyticsClient):
        self.analytics_client = analytics_client
        self.repository = repository

    def shorten_url(self, url: HttpUrl) -> UrlModel:
        for attempt in range(self.MAX_RETRIES):
            shortened_url = self._generate_short_url(url)

            existing = self.repository.get(shortened_url)
            if not existing:
                return self.repository.create(shortened_url=shortened_url, url=url)
            elif str(existing.link) == str(url):
                logger.info(f"URL already shortened: {url} -> {shortened_url}")
                return existing
            else:
                logger.warning(
                    f"Collision detected for {shortened_url}, "
                    f"attempt {attempt + 1}/{self.MAX_RETRIES}"
                )

        raise ValueError(
            f"Failed to generate unique short URL after " f"{self.MAX_RETRIES} attempts"
        )

    @staticmethod
    def _generate_short_url(url: HttpUrl) -> str:
        # Add secure random salt to prevent predictable hashes
        salt = secrets.token_bytes(16)
        nanoseconds = int(datetime.now().timestamp() * NANOSECONDS_MULTIPLIER)
        seed_string = f"{url}:{nanoseconds}:{salt.hex()}"

        url_hash = hashlib.sha256(seed_string.encode()).digest()
        b64_string = base64.urlsafe_b64encode(url_hash).decode().rstrip("=")

        return b64_string[:SHORT_URL_LENGTH]

    def get_all_urls(self) -> list[UrlModel]:
        return self.repository.list()

    def get_url(
        self,
        shortened_url: str,
        request_ip: str | None = None,
        city: str = "unknown",
        country: str = "unknown",
    ) -> UrlModel | None:
        self._record_analytics_async(shortened_url, request_ip, city, country)

        return self.repository.get(shortened_url)

    def _record_analytics_async(
        self, shortened_url: str, request_ip: str | None, city: str, country: str
    ) -> None:
        """Record analytics in background without blocking the main request"""
        try:
            ip = request_ip if request_ip else "0.0.0.0"

            task = asyncio.create_task(
                self._record_click_with_error_handling(shortened_url, ip, city, country)
            )
            # Don't await the task to keep it fire-and-forget
            task.add_done_callback(lambda _: None)
        except Exception as e:
            logger.warning(
                f"Failed to create async analytics task: {e!s}, falling back to sync"
            )
            self._record_click_sync(shortened_url, request_ip, city, country)

    async def _record_click_with_error_handling(
        self, shortened_url: str, ip: str, city: str, country: str
    ) -> None:
        """Background task for recording analytics with proper error handling"""
        try:
            await self.analytics_client.record_click_async(
                short_link=shortened_url,
                ip=ip,
                city=city,
                country=country,
            )
        except Exception as e:
            logger.error(f"Error recording click asynchronously: {e!s}")

    def _record_click_sync(
        self, shortened_url: str, request_ip: str | None, city: str, country: str
    ) -> None:
        """Synchronous fallback for analytics recording"""
        try:
            ip = request_ip if request_ip else "0.0.0.0"
            self.analytics_client.record_click(
                short_link=shortened_url,
                ip=ip,
                city=city,
                country=country,
            )
        except Exception as e:
            logger.error(f"Error recording click synchronously: {e!s}")

    def delete_url(self, shortened_url: str) -> None:
        self.repository.delete(shortened_url)
