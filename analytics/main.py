import logging
from http import HTTPMethod as Method
from threading import Thread

from app.config import Settings, get_settings
from app.exceptions import (catch_all_exception_handler,
                            internal_server_error_handler)
from app.grpc.server import serve
from app.routes import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


class AppFactory:
    @staticmethod
    def create_app() -> FastAPI:
        app = FastAPI(
            title="Analytics Service",
            description="API for analytics",
            version="0.1.0",
        )

        AppFactory._register_routers(app)

        AppFactory._configure_middleware(app)
        AppFactory._register_exception_handlers(app)

        AppFactory.start_grpc_thread()

        return app

    @staticmethod
    def start_grpc_thread():
        grpc_thread = Thread(target=AppFactory.start_grpc_server, daemon=True)
        grpc_thread.start()

    @staticmethod
    def start_grpc_server():
        config = AppFactory._get_config()
        grpc_port = config.GRPC_PORT
        try:
            from app.db.session import SessionLocal

            grpc_server = serve(SessionLocal, grpc_port)
            grpc_server.wait_for_termination()
        except Exception as e:
            logger.error(f"Error starting gRPC server: {str(e)}")

    @staticmethod
    def _register_routers(app: FastAPI):
        app.include_router(router, prefix="/api/v1", tags=["analytics"])

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

    @staticmethod
    def _get_config() -> Settings:
        return get_settings()
app = AppFactory.create_app()
