import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional

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
    def get_analytics_by_short_link(self, short_link: str) -> Optional[AnalyticsModel]:
        raise NotImplementedError


class InMemoryAnalyticsRepository(AnalyticsRepository):
    _instance = None
    _analytics: Dict[str, AnalyticsModel] = {}

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

    def get_analytics_by_short_link(self, short_link: str) -> Optional[AnalyticsModel]:
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

        return db_analytics.to_model()

    def get_analytics_by_short_link(self, short_link: str) -> Optional[AnalyticsModel]:
        db_analytics = (
            self.session.query(Analytics)
            .filter(Analytics.short_link == short_link)
            .first()
        )

        if not db_analytics:
            return None

        return db_analytics.to_model()

    def _save(self) -> None:
        try:
            self.session.commit()
        except Exception:
            logger.exception("Failed to save changes to database")
            self.session.rollback()
            raise
