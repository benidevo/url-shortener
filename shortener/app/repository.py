import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from pydantic import HttpUrl
from sqlalchemy.orm import Session

from app.db.objects import Url
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

    def list(self) -> List[UrlModel]:
        result = self._urls.values()
        return result

    def delete(self, shortened_url: str) -> None:
        if shortened_url not in self._urls:
            return

        del self._urls[shortened_url]


class SqlAlchemyUrlRepository(UrlRepository):
    def __init__(self, db_session: Session):
        self.session = db_session

    def create(self, shortened_url: str, url: HttpUrl) -> UrlModel:
        db_url = Url(
            link=str(url),
            short_link=shortened_url,
        )
        self.session.add(db_url)
        self._save()
        return db_url.to_model()

    def get(self, shortened_url: str) -> Optional[UrlModel]:
        db_url = self.session.query(Url).filter(
            Url.short_link == shortened_url).first()
        if db_url:
            return db_url.to_model()
        return

    def list(self) -> List[UrlModel]:
        db_urls = self.session.query(Url).all()
        return [url.to_model() for url in db_urls]

    def delete(self, shortened_url: str) -> None:
        db_url = self.session.query(Url).filter(
            Url.short_link == shortened_url).first()
        if db_url:
            self.session.delete(db_url)
            self._save()

    def _save(self) -> None:
        try:
            self.session.commit()
        except Exception:
            log.exception("Failed to save changes to database")
            self.session.rollback()
            raise
