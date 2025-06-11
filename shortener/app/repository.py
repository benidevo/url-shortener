import builtins
import json
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar, cast

import redis
from pydantic import HttpUrl
from sqlalchemy.exc import DatabaseError, IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import CACHE_TTL_SECONDS
from app.db.objects import Url
from app.models import UrlModel

T = TypeVar("T")

log = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        settings = get_settings()

        self._pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_CONNECTION_POOL_SIZE,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        self._client = redis.Redis(connection_pool=self._pool, decode_responses=True)

    def get(self, key: str) -> UrlModel | None:
        try:
            cached_result = self._client.get(f"url:{key}")
            if cached_result is None:
                return None
            # Ensure we have string data
            if isinstance(cached_result, bytes):
                cached_data = cached_result.decode("utf-8")
            else:
                cached_data = str(cached_result)
            data = json.loads(cached_data)
            return UrlModel(**data)
        except (redis.RedisError, json.JSONDecodeError, ValueError) as e:
            log.warning(f"Error retrieving from Redis cache: {e}")
            return None

    def put(self, key: str, value: UrlModel) -> None:
        try:
            cached_data = value.model_dump_json()
            self._client.setex(f"url:{key}", self.ttl_seconds, cached_data)
        except redis.RedisError as e:
            log.warning(f"Error storing to Redis cache: {e}")

    def invalidate(self, key: str) -> None:
        try:
            self._client.delete(f"url:{key}")
        except redis.RedisError as e:
            log.warning(f"Error invalidating Redis cache: {e}")

    def clear(self) -> None:
        try:
            pattern = "url:*"
            key_result = self._client.keys(pattern)
            if key_result:
                # Convert keys to list to ensure they are iterable
                key_list = list(cast(list, key_result))
                if key_list:
                    self._client.delete(*key_list)
        except redis.RedisError as e:
            log.warning(f"Error clearing Redis cache: {e}")

    def size(self) -> int:
        try:
            key_result = self._client.keys("url:*")
            return len(list(cast(list, key_result)))
        except redis.RedisError as e:
            log.warning(f"Error getting Redis cache size: {e}")
            return 0


class UrlRepository(ABC):
    @abstractmethod
    def create(self, shortened_url: str, url: HttpUrl) -> UrlModel:
        raise NotImplementedError

    @abstractmethod
    def get(self, shortened_url: str) -> UrlModel | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_url(self, url: HttpUrl) -> UrlModel | None:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list[UrlModel]:
        raise NotImplementedError

    @abstractmethod
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

    def find_by_url(self, url: HttpUrl) -> UrlModel | None:
        url_str = str(url)
        for url_model in self._urls.values():
            if str(url_model.link) == url_str:
                return url_model
        return None

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
        settings = get_settings()
        self._cache: RedisCache | None = None
        if settings.CACHE_ENABLED:
            self._cache = RedisCache(ttl_seconds=settings.CACHE_TTL_SECONDS)

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
            if self._cache:
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
        # Try cache first if enabled
        if self._cache:
            cached_result = self._cache.get(shortened_url)
            if cached_result is not None:
                log.debug(f"Cache hit for URL: {shortened_url}")
                return cached_result

        log.debug(f"Cache miss for URL: {shortened_url}")
        result = self._execute_with_retry(
            lambda: self._get_impl(shortened_url), "get URL"
        )

        if result is not None and self._cache:
            self._cache.put(shortened_url, result)

        return result

    def _get_impl(self, shortened_url: str) -> UrlModel | None:
        db_url = self.session.query(Url).filter(Url.short_link == shortened_url).first()
        if db_url:
            return db_url.to_model()
        return None

    def find_by_url(self, url: HttpUrl) -> UrlModel | None:
        return self._execute_with_retry(
            lambda: self._find_by_url_impl(url), "find URL by link"
        )

    def _find_by_url_impl(self, url: HttpUrl) -> UrlModel | None:
        url_str = str(url)
        db_url = self.session.query(Url).filter(Url.link == url_str).first()
        if db_url:
            return db_url.to_model()
        return None

    def list(self) -> list[UrlModel]:
        return self._execute_with_retry(lambda: self._list_impl(), "list URLs")

    def _list_impl(self) -> builtins.list[UrlModel]:
        db_urls = self.session.query(Url).all()
        return [url.to_model() for url in db_urls]

    def delete(self, shortened_url: str) -> None:
        db_url = self.session.query(Url).filter(Url.short_link == shortened_url).first()
        if db_url:
            self.session.delete(db_url)
            self._save()
            if self._cache:
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

    def _execute_with_retry(self, func: Callable[[], T], operation_name: str) -> T:
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
        # This should never be reached, but mypy requires it
        raise RuntimeError(f"Failed to {operation_name} after all retries")
