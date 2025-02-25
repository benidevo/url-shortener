from typing import Optional

from app.models import AnalyticsModel
from app.repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    def retrieve_analytics(self, short_link: str) -> Optional[AnalyticsModel]:
        return self.repository.get_analytics_by_short_link(short_link)
