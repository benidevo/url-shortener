import logging

from fastapi import (APIRouter, Body, Depends, HTTPException, Path, Request,
                     status)

from app.dependencies import get_url_service
from app.models import ResponseModel, UrlCreate, UrlModel
from app.service import UrlShortenerService

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def shorten_url(
    payload: UrlCreate = Body(..., description="URL to shorten"),
    service: UrlShortenerService = Depends(get_url_service),
):
    try:
        shorten_url: UrlModel = service.shorten_url(url=payload.url)
    except Exception as e:
        logger.error(f"Error shortening URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    return ResponseModel(data=shorten_url)


@router.get("/", response_model=ResponseModel)
def list_urls(service: UrlShortenerService = Depends(get_url_service)):
    try:
        shortened_urls = service.get_all_urls()
    except Exception as e:
        logger.error(f"Error listing URLs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    return ResponseModel(data=shortened_urls)


@router.get("/{shortened_url}", response_model=ResponseModel)
def get_url(
    request: Request,
    shortened_url: str = Path(..., min_length=7, max_length=7),
    service: UrlShortenerService = Depends(get_url_service),
):

    client_ip, city, country = _parse_request(request)

    shorten_url = service.get_url(
        shortened_url=shortened_url,
        request_ip=client_ip,
        city=city,
        country=country,
    )
    if not shorten_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )

    return ResponseModel(data=shorten_url)


def _parse_request(request) -> tuple[str, str, str]:
    """
    Extracts the client's IP address, city, and country from the request headers.
    """
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else None

    city = request.headers.get("X-GeoIP-City", "unknown")
    country = request.headers.get("X-GeoIP-Country", "unknown")

    return client_ip, city, country


@router.delete("/{shortened_url}", response_model=ResponseModel)
def delete_url(
    shortened_url: str = Path(..., min_length=7, max_length=7),
    service: UrlShortenerService = Depends(get_url_service),
):
    try:
        service.delete_url(shortened_url=shortened_url)
    except Exception as e:
        logger.error(f"Error deleting URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    return ResponseModel()
