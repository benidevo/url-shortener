import logging
from http import HTTPMethod as Method

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.exceptions import (catch_all_exception_handler,
                            internal_server_error_handler)
from app.routes import router

logger = logging.getLogger(__name__)


class AppFactory:
    """Factory for creating configured FastAPI applications."""

    @staticmethod
    def create_app() -> FastAPI:
        app = FastAPI(
            title="URL Shortener Service",
            description="API for shortening URLs",
            version="0.1.0",
        )

        AppFactory._register_routers(app)

        AppFactory._configure_middleware(app)
        AppFactory._register_exception_handlers(app)

        logger.info("Shortener service started")
        return app

    @staticmethod
    def _register_routers(app: FastAPI):
        app.include_router(router, prefix="/api/v1", tags=["urls"])

    @staticmethod
    def _configure_middleware(app: FastAPI):
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
