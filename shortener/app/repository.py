import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from pydantic import HttpUrl
from sqlalchemy.exc import DatabaseError, IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.db.objects import Url
from app.models import UrlModel

log = logging.getLogger(__name__)


class UrlRepository(ABC):
    @abstractmethod
    def create(self, shortened_url: str, url: HttpUrl) -> UrlModel:
        raise NotImplementedError

    def get(self, shortened_url: str) -> Optional[UrlModel]:
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
        return list(self._urls.values())

    def delete(self, shortened_url: str) -> None:
        if shortened_url not in self._urls:
            return

        del self._urls[shortened_url]


class SqlAlchemyUrlRepository(UrlRepository):
    MAX_RETRIES = 3
    RETRY_DELAY = 0.1  # Initial delay in seconds

    def __init__(self, db_session: Session):
        self.session = db_session

    def create(self, shortened_url: str, url: HttpUrl) -> UrlModel:
        existing = self.get(shortened_url)
        if existing:
            if str(existing.link) == str(url):
                # Same URL, return existing
                return existing
            else:
                # Different URL with same short code. This is a collision
                raise IntegrityError(  # type: ignore
                    f"Short URL '{shortened_url}' already exists "
                    f"for a different URL",
                    None,
                    None,
                )

        db_url = Url(
            link=str(url),
            short_link=shortened_url,
        )

        try:
            self.session.add(db_url)
            self._save()
            return db_url.to_model()
        except IntegrityError as e:
            self.session.rollback()
            log.warning(f"Integrity error creating URL: {e}")

            # Check if it's the same URL (race condition)
            existing = self.get(shortened_url)
            if existing and str(existing.link) == str(url):
                return existing
            raise

    def get(self, shortened_url: str) -> Optional[UrlModel]:
        return self._execute_with_retry(  # type: ignore
            lambda: self._get_impl(shortened_url), "get URL"
        )

    def _get_impl(self, shortened_url: str) -> Optional[UrlModel]:
        db_url = self.session.query(Url).filter(Url.short_link == shortened_url).first()
        if db_url:
            return db_url.to_model()
        return None

    def list(self) -> List[UrlModel]:
        return self._execute_with_retry(  # type: ignore
            lambda: self._list_impl(), "list URLs"
        )

    def _list_impl(self) -> List[UrlModel]:
        db_urls = self.session.query(Url).all()
        return [url.to_model() for url in db_urls]

    def delete(self, shortened_url: str) -> None:
        db_url = self.session.query(Url).filter(Url.short_link == shortened_url).first()
        if db_url:
            self.session.delete(db_url)
            self._save()

    def _save(self) -> None:
        """Save changes with retry logic for transient failures"""
        for attempt in range(self.MAX_RETRIES):
            try:
                self.session.commit()
                return
            except OperationalError as e:
                self.session.rollback()
                if attempt < self.MAX_RETRIES - 1:
                    # Exponential backoff
                    delay = self.RETRY_DELAY * (2**attempt)
                    log.warning(
                        f"Database connection error (attempt "
                        f"{attempt + 1}/{self.MAX_RETRIES}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    log.error(
                        f"Failed to save after " f"{self.MAX_RETRIES} attempts: {e}"
                    )
                    raise
            except IntegrityError:
                self.session.rollback()
                raise
            except DatabaseError as e:
                self.session.rollback()
                log.error(f"Database error: {e}")
                raise
            except Exception as e:
                self.session.rollback()
                log.exception(f"Unexpected error saving to database: {e}")
                raise

    def _execute_with_retry(self, func, operation_name: str):
        """Execute a read operation with retry logic"""
        for attempt in range(self.MAX_RETRIES):
            try:
                return func()
            except OperationalError as e:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2**attempt)
                    log.warning(
                        f"Database error during {operation_name} (attempt "
                        f"{attempt + 1}/{self.MAX_RETRIES}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    # Rollback to clear any failed transaction state
                    self.session.rollback()
                else:
                    log.error(
                        f"Failed to {operation_name} after "
                        f"{self.MAX_RETRIES} attempts: {e}"
                    )
                    raise
            except Exception as e:
                log.error(f"Unexpected error during {operation_name}: {e}")
                raise
