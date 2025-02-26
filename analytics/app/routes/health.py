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
    return {"status": "ok", "service": "analytics"}


@router.get("/readiness")
async def readiness_check(session=Depends(get_session)) -> Dict:
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
