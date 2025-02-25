from app.db.session import SessionLocal
from app.repository import SqlAlchemyUrlRepository, UrlRepository
from app.service import UrlShortenerService
from fastapi import Depends
from sqlalchemy.orm import Session


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_repository(session: Session = Depends(get_session)) -> UrlRepository:
    return SqlAlchemyUrlRepository(db_session=session)


def get_url_service(
    repository: UrlRepository = Depends(get_repository),
) -> UrlShortenerService:
    return UrlShortenerService(repository)
