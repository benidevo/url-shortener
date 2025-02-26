import base64
import hashlib
import logging
from datetime import datetime
from typing import Optional

from pydantic import HttpUrl

from app.grpc.client import AnalyticsClient
from app.models import UrlModel
from app.repository import UrlRepository

logger = logging.getLogger(__name__)


class UrlShortenerService:
    def __init__(self, repository: UrlRepository, analytics_client: AnalyticsClient):
        self.analytics_client = analytics_client
        self.repository = repository

    def shorten_url(self, url: HttpUrl) -> UrlModel:
        shortened_url = self._generate_short_url(url)
        return self.repository.create(shortened_url=shortened_url, url=url)

    @staticmethod
    def _generate_short_url(url: HttpUrl) -> str:
        nanoseconds = int(datetime.now().timestamp() * 1_000_000)
        seed_string = f"{url}:{nanoseconds}"

        url_hash = hashlib.md5(seed_string.encode()).digest()
        b64_string = base64.urlsafe_b64encode(url_hash).decode().rstrip("=")

        return b64_string[:7]

    def get_all_urls(self) -> list[UrlModel]:
        return self.repository.list()

    def get_url(
        self,
        shortened_url: str,
        request_ip: Optional[str] = None,
        city: str = "unknown",
        country: str = "unknown"
    ) -> Optional[UrlModel]:
        try:
            ip = request_ip if request_ip else "0.0.0.0"

            self.analytics_client.record_click(
                short_link=shortened_url,
                ip=ip,
                city=city,
                country=country,
            )
        except Exception as e:
            logger.error(f"Error recording click: {str(e)}")

        return self.repository.get(shortened_url)

    def delete_url(self, shortened_url: str) -> None:
        self.repository.delete(shortened_url)
