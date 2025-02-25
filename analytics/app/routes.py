from app.dependencies import get_analytics_service
from app.models import ResponseModel
from app.service import AnalyticsService
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.get("/", response_model=ResponseModel)
def get_analytics(
    service: AnalyticsService = Depends(get_analytics_service),
) -> ResponseModel:
    analytics = service.retrieve_analytics("example")
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analytics entry for short link",
        )
    return ResponseModel(data=analytics)
