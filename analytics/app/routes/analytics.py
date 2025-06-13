from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.dependencies import get_analytics_service
from app.models import ResponseModel
from app.service import AnalyticsService

router = APIRouter()


@router.get("/{short_link}", response_model=ResponseModel)
def get_analytics(
    short_link: str = Path(..., min_length=8, max_length=8),
    service: AnalyticsService = Depends(get_analytics_service),
) -> ResponseModel:
    analytics = service.retrieve_analytics(short_link)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analytics entry for short link",
        )

    return ResponseModel(data=analytics)
