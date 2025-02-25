from fastapi import Depends

from app.repository import InMemoryUrlRepository, UrlRepository
from app.service import UrlShortenerService


def get_repository() -> UrlRepository:
    return InMemoryUrlRepository()


def get_url_service(
    repository: UrlRepository = Depends(get_repository),
) -> UrlShortenerService:
    return UrlShortenerService(repository)
