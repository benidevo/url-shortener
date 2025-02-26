from app.db.session import SessionLocal
from app.repository import AnalyticsRepository, SqlAlchemyAnalyticsRepository
from app.service import AnalyticsService
from fastapi import Depends
from sqlalchemy.orm import Session


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_repository(session: Session = Depends(get_session)) -> AnalyticsRepository:
    return SqlAlchemyAnalyticsRepository(session)


def get_analytics_service(
    repository: AnalyticsRepository = Depends(get_repository),
) -> AnalyticsService:
    return AnalyticsService(repository)
