import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from pydantic import HttpUrl

from app.models import UrlModel

log = logging.getLogger(__name__)


class UrlRepository(ABC):
    @abstractmethod
    def create(self, shortened_url: str, url: HttpUrl) -> UrlModel:
        raise NotImplementedError

    def get(self, shortened_url: HttpUrl) -> Optional[UrlModel]:
        raise NotImplementedError

    def list(self) -> list[UrlModel]:
        raise NotImplementedError

    def delete(self, shortened_url: str) -> None:
        raise NotImplementedError


class InMemoryUrlRepository(UrlRepository):
    _instance = None
    _urls: Dict[str, UrlModel] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create(self, shortened_url: str, url: HttpUrl) -> UrlModel:
        url_model = UrlModel(link=url, short_link=shortened_url)
        self._urls[shortened_url] = url_model
        return url_model

    def get(self, shortened_url: str) -> Optional[UrlModel]:
        return self._urls.get(shortened_url)

    def list(self) -> list[UrlModel]:
        result = self._urls.values()
        return result

    def delete(self, shortened_url: str) -> None:
        if shortened_url not in self._urls:
            return

        del self._urls[shortened_url]
