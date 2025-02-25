import base64
import hashlib
from datetime import datetime
from typing import Optional

from app.models import UrlModel
from app.repository import UrlRepository
from pydantic import HttpUrl


class UrlShortenerService:
    def __init__(self, repository: UrlRepository):
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

    def get_url(self, shortened_url: str) -> Optional[UrlModel]:
        # inform analytics about the click
        return self.repository.get(shortened_url)

    def delete_url(self, shortened_url: str) -> None:
        # inform analytics about the deletion
        self.repository.delete(shortened_url)
