from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from app.dependencies import get_url_service
from app.models import ResponseModel, UrlCreate, UrlModel
from app.service import UrlShortenerService

router = APIRouter()


@router.post(
    "/",
    response_model=ResponseModel,
    status_code=status.HTTP_201_CREATED
)
def shorten_url(
    payload: UrlCreate = Body(..., description="URL to shorten"),
    service: UrlShortenerService = Depends(get_url_service),
):
    shorten_url: UrlModel = service.shorten_url(url=payload.url)
    return ResponseModel(data=shorten_url)


@router.get("/", response_model=ResponseModel)
def list_urls(service: UrlShortenerService = Depends(get_url_service)):
    shortened_urls = service.get_all_urls()
    return ResponseModel(data=shortened_urls)


@router.get("/{shortened_url}", response_model=ResponseModel)
def get_url(
    shortened_url: str = Path(..., min_length=7, max_length=7),
    service: UrlShortenerService = Depends(get_url_service),
):
    shorten_url = service.get_url(shortened_url=shortened_url)
    if not shorten_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found"
        )
    return ResponseModel(data=shorten_url)


@router.delete("/{shortened_url}", response_model=ResponseModel)
def delete_url(
    shortened_url: str = Path(..., min_length=7, max_length=7),
    service: UrlShortenerService = Depends(get_url_service),
):
    service.delete_url(shortened_url=shortened_url)
    return ResponseModel()
