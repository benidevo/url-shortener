from fastapi import Depends

from app.config import Settings, get_settings
from app.db.session import SessionLocal
from app.grpc.client import AnalyticsClient, GrpcAnalyticsClient
from app.repository import SqlAlchemyUrlRepository, UrlRepository
from app.service import UrlShortenerService


def get_settings_dependency() -> Settings:
    return get_settings()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_repository(session=Depends(get_session)) -> UrlRepository:
    return SqlAlchemyUrlRepository(db_session=session)


def get_analytics_client(
    settings: Settings = Depends(get_settings_dependency),
) -> AnalyticsClient:
    return GrpcAnalyticsClient.get_instance(target=settings.ANALYTICS_SERVICE_GRPC)


def get_url_service(
    repository: UrlRepository = Depends(get_repository),
    analytics_client: AnalyticsClient = Depends(get_analytics_client),
) -> UrlShortenerService:
    return UrlShortenerService(repository, analytics_client)
