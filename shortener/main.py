import asyncio
import logging
from contextlib import asynccontextmanager
from http import HTTPMethod as Method

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.exceptions import catch_all_exception_handler, internal_server_error_handler
from app.middleware.rate_limiting import cleanup_rate_limiter, rate_limit_middleware
from app.routes.health import router as health_router
from app.routes.urls import router as urls_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    logger.info("Starting background tasks...")
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    logger.info("Shutting down background tasks...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


async def periodic_cleanup():
    """Background task for periodic cleanup operations"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            cleanup_rate_limiter()
            logger.debug("Periodic cleanup completed")
        except asyncio.CancelledError:
            logger.info("Cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}")


class AppFactory:
    @staticmethod
    def create_app() -> FastAPI:
        app = FastAPI(
            title="URL Shortener Service",
            description="API for shortening URLs",
            version="0.1.0",
            lifespan=lifespan,
        )

        AppFactory._register_routers(app)

        AppFactory._configure_middleware(app)
        AppFactory._register_exception_handlers(app)

        logger.info("Shortener service started")
        return app

    @staticmethod
    def _register_routers(app: FastAPI):
        app.include_router(urls_router, prefix="/api/v1", tags=["urls"])
        app.include_router(health_router, tags=["health"])

    @staticmethod
    def _configure_middleware(app: FastAPI):
        app.middleware("http")(rate_limit_middleware)

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=[
                Method.GET,
                Method.POST,
                Method.DELETE,
                Method.HEAD,
            ],
            allow_headers=["*"],
        )

    @staticmethod
    def _register_exception_handlers(app: FastAPI):
        app.add_exception_handler(500, internal_server_error_handler)
        app.add_exception_handler(Exception, catch_all_exception_handler)


app = AppFactory.create_app()
