import logging
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def internal_server_error_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())

    logger.error(
        f"Internal Server Error [ID: {error_id}]: {exc!s}",
        exc_info=True,
        extra={
            "error_id": error_id,
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else "unknown",
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "error_id": error_id,
        },
    )


async def catch_all_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())

    logger.error(
        f"Unhandled Exception [ID: {error_id}]: {exc!s}",
        exc_info=True,
        extra={
            "error_id": error_id,
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else "unknown",
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "error_id": error_id,
        },
    )
