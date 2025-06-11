import builtins
import logging
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from threading import Lock

from pydantic import HttpUrl
from sqlalchemy.exc import DatabaseError, IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.constants import CACHE_MAX_SIZE, CACHE_TTL_SECONDS
from app.db.objects import Url
from app.models import UrlModel

log = logging.getLogger(__name__)


class TTLCache:
    def __init__(
        self, max_size: int = CACHE_MAX_SIZE, ttl_seconds: int = CACHE_TTL_SECONDS
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple[UrlModel, float]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> UrlModel | None:
        with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]
            current_time = time.time()

            if current_time - timestamp > self.ttl_seconds:
                del self._cache[key]
                return None

            self._cache.move_to_end(key)
            return value

    def put(self, key: str, value: UrlModel) -> None:
        """Put item in cache with current timestamp"""
        with self._lock:
            current_time = time.time()

            if key in self._cache:
                self._cache[key] = (value, current_time)
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)

                self._cache[key] = (value, current_time)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, (_, timestamp) in self._cache.items():
                if current_time - timestamp > self.ttl_seconds:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)


class UrlRepository(ABC):
    @abstractmethod
    def create(self, shortened_url: str, url: HttpUrl) -> UrlModel:
        raise NotImplementedError

    def get(self, shortened_url: str) -> UrlModel | None:
        raise NotImplementedError

    def list(self) -> list[UrlModel]:
        raise NotImplementedError

    def delete(self, shortened_url: str) -> None:
        raise NotImplementedError


class InMemoryUrlRepository(UrlRepository):
    _instance = None
    _urls: dict[str, UrlModel] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create(self, shortened_url: str, url: HttpUrl) -> UrlModel:
        url_model = UrlModel(link=url, short_link=shortened_url)
        self._urls[shortened_url] = url_model
        return url_model

    def get(self, shortened_url: str) -> UrlModel | None:
        return self._urls.get(shortened_url)

    def list(self) -> list[UrlModel]:
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
        self._cache = TTLCache()

    def create(self, shortened_url: str, url: HttpUrl) -> UrlModel:
        existing = self.get(shortened_url)
        if existing:
            if str(existing.link) == str(url):
                # Same URL, return existing
                return existing
            else:
                # Different URL with same short code. This is a collision
                error_msg = (
                    f"Short URL '{shortened_url}' already exists for a different URL"
                )
                raise IntegrityError(error_msg, params=None, orig=None)  # type: ignore[arg-type]

        db_url = Url(
            link=str(url),
            short_link=shortened_url,
        )

        try:
            self.session.add(db_url)
            self._save()
            result = db_url.to_model()
            self._cache.put(shortened_url, result)
            return result
        except IntegrityError as e:
            self.session.rollback()
            log.warning(f"Integrity error creating URL: {e}")

            # Check if it's the same URL (race condition)
            existing = self.get(shortened_url)
            if existing and str(existing.link) == str(url):
                return existing
            raise

    def get(self, shortened_url: str) -> UrlModel | None:
        # Try cache first
        cached_result = self._cache.get(shortened_url)
        if cached_result is not None:
            log.debug(f"Cache hit for URL: {shortened_url}")
            return cached_result

        log.debug(f"Cache miss for URL: {shortened_url}")
        result = self._execute_with_retry(  # type: ignore
            lambda: self._get_impl(shortened_url), "get URL"
        )

        if result is not None:
            self._cache.put(shortened_url, result)

        return result

    def _get_impl(self, shortened_url: str) -> UrlModel | None:
        db_url = self.session.query(Url).filter(Url.short_link == shortened_url).first()
        if db_url:
            return db_url.to_model()
        return None

    def list(self) -> list[UrlModel]:
        return self._execute_with_retry(  # type: ignore
            lambda: self._list_impl(), "list URLs"
        )

    def _list_impl(self) -> builtins.list[UrlModel]:
        db_urls = self.session.query(Url).all()
        return [url.to_model() for url in db_urls]

    def delete(self, shortened_url: str) -> None:
        db_url = self.session.query(Url).filter(Url.short_link == shortened_url).first()
        if db_url:
            self.session.delete(db_url)
            self._save()
            self._cache.invalidate(shortened_url)

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
