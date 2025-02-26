import logging
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

from app.db.session import SessionLocal

logger = logging.getLogger(__name__)
router = APIRouter()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.get("/health")
async def health_check() -> Dict:
    """Basic health check endpoint.

    Returns a simple status indicating the service is running.
    This endpoint is used for basic liveness probes.
    """
    return {"status": "ok", "service": "analytics"}


@router.get("/readiness")
async def readiness_check(session=Depends(get_session)) -> Dict:
    """Readiness check endpoint.

    Verifies that the service can connect to its database.
    This endpoint is used for readiness probes to determine
    if the service is ready to accept traffic.
    """
    try:
        result = session.execute(text("SELECT 1"))
        result.scalar()
        db_status = "ok"
    except SQLAlchemyError as e:
        logger.error(f"Database connectivity check failed: {str(e)}")
        db_status = "error"

    status = "ok" if db_status == "ok" else "error"

    return {
        "status": status,
        "service": "analytics",
        "dependencies": {"database": db_status},
    }
