import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy.exc import DatabaseError, OperationalError

from app.constants import (
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_MULTIPLIER,
    RETRY_BASE_DELAY_SECONDS,
)
from app.db.objects import Analytics, Click
from app.models import AnalyticsModel, ClickModel

logger = logging.getLogger(__name__)


class AnalyticsRepository(ABC):
    @abstractmethod
    def record_click(
        self,
        click: ClickModel,
        short_link: str,
    ) -> AnalyticsModel:
        raise NotImplementedError

    @abstractmethod
    def get_analytics_by_short_link(self, short_link: str) -> AnalyticsModel | None:
        raise NotImplementedError


class InMemoryAnalyticsRepository(AnalyticsRepository):
    _instance = None
    _analytics: dict[str, AnalyticsModel] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def record_click(
        self,
        click: ClickModel,
        short_link: str,
    ) -> AnalyticsModel:
        existing_analytics = self.get_analytics_by_short_link(short_link)
        if not existing_analytics:
            analytics = AnalyticsModel(
                short_link=short_link,
                updated_at=datetime.now(),
                clicks=[click],
            )
            self._analytics[short_link] = analytics
            return analytics

        existing_analytics.clicks.append(click)
        existing_analytics.updated_at = datetime.now()
        return existing_analytics

    def get_analytics_by_short_link(self, short_link: str) -> AnalyticsModel | None:
        return self._analytics.get(short_link)


class SqlAlchemyAnalyticsRepository(AnalyticsRepository):
    def __init__(self, db_session):
        self.session = db_session

    def record_click(self, click: ClickModel, short_link: str) -> AnalyticsModel:
        db_analytics = (
            self.session.query(Analytics)
            .filter(Analytics.short_link == short_link)
            .first()
        )

        if not db_analytics:
            db_analytics = Analytics(short_link=short_link, clicks=[])
            self.session.add(db_analytics)

        db_click = Click.from_model(click)
        db_analytics.clicks.append(db_click)
        db_analytics.updated_at = datetime.now()

        self._save()

        return db_analytics.to_model()  # type: ignore[no-any-return]

    def get_analytics_by_short_link(self, short_link: str) -> AnalyticsModel | None:
        return self._execute_with_retry(  # type: ignore
            lambda: self._get_analytics_impl(short_link), "get analytics"
        )

    def _get_analytics_impl(self, short_link: str) -> AnalyticsModel | None:
        db_analytics = (
            self.session.query(Analytics)
            .filter(Analytics.short_link == short_link)
            .first()
        )

        if not db_analytics:
            return None

        return db_analytics.to_model()  # type: ignore[no-any-return]

    def _save(self) -> None:
        """Save changes with retry logic for transient failures"""
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                self.session.commit()
                return
            except OperationalError as e:
                self.session.rollback()
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    # Exponential backoff
                    delay = RETRY_BASE_DELAY_SECONDS * (
                        RETRY_BACKOFF_MULTIPLIER**attempt
                    )
                    logger.warning(
                        f"Database connection error (attempt "
                        f"{attempt + 1}/{MAX_RETRY_ATTEMPTS}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Failed to save after {MAX_RETRY_ATTEMPTS} attempts: {e}"
                    )
                    raise
            except DatabaseError as e:
                self.session.rollback()
                logger.error(f"Database error: {e}")
                raise
            except Exception as e:
                self.session.rollback()
                logger.exception(f"Unexpected error saving to database: {e}")
                raise

    def _execute_with_retry(self, func, operation_name: str):
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                return func()
            except OperationalError as e:
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    delay = RETRY_BASE_DELAY_SECONDS * (
                        RETRY_BACKOFF_MULTIPLIER**attempt
                    )
                    logger.warning(
                        f"Database error during {operation_name} (attempt "
                        f"{attempt + 1}/{MAX_RETRY_ATTEMPTS}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    # Rollback to clear any failed transaction state
                    self.session.rollback()
                else:
                    logger.error(
                        f"Failed to {operation_name} after "
                        f"{MAX_RETRY_ATTEMPTS} attempts: {e}"
                    )
                    raise
            except Exception as e:
                logger.error(f"Unexpected error during {operation_name}: {e}")
                raise
