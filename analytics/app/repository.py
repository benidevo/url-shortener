from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional

from app.models import ClickModel, AnalyticsModel


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


example = {
    "example": AnalyticsModel(
        short_link="example",
        updated_at=datetime.now(),
        clicks=[
            ClickModel(
                ip="127.0.0.1",
                city="New York",
                country="United States",
            )
        ],
    )
}


class InMemoryAnalyticsRepository(AnalyticsRepository):
    _instance = None
    _analytics: Dict[str, AnalyticsModel] = example

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._analytics = example
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
    def __ini__(self, db_session):
        self.db_session = db_session

    def record_click(
        self,
        click: ClickModel,
        short_link: str,
    ) -> AnalyticsModel:
        raise NotImplementedError

    def get_analytics_by_short_link(self, short_link):
        raise NotImplementedError
