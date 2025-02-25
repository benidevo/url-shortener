from fastapi import Depends

from app.service import AnalyticsService
from app.repository import AnalyticsRepository, InMemoryAnalyticsRepository


def get_repository() -> AnalyticsRepository:
    return InMemoryAnalyticsRepository()


def get_analytics_service(
    repository: AnalyticsRepository = Depends(get_repository),
) -> AnalyticsService:
    return AnalyticsService(repository)
