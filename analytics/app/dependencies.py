from app.repository import AnalyticsRepository, InMemoryAnalyticsRepository
from app.service import AnalyticsService
from fastapi import Depends


def get_repository() -> AnalyticsRepository:
    return InMemoryAnalyticsRepository()


def get_analytics_service(
    repository: AnalyticsRepository = Depends(get_repository),
) -> AnalyticsService:
    return AnalyticsService(repository)
