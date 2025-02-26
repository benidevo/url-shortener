import logging
import os
from threading import Thread

from app.grpc.server import serve
from app.routes import router
from fastapi import FastAPI

logger = logging.getLogger(__name__)


class AppFactory:
    """Factory for creating configured FastAPI applications."""

    @staticmethod
    def create_app() -> FastAPI:
        AppFactory._load_config()

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
        grpc_port = int(os.environ.get("GRPC_PORT", 50051))
        try:
            from app.db.session import SessionLocal

            grpc_server = serve(SessionLocal, grpc_port)
            grpc_server.wait_for_termination()
        except Exception as e:
            logger.error(f"Error starting gRPC server: {str(e)}")


    @staticmethod
    def _load_config():
        """Load application configuration."""
        # Load from environment variables, config files, etc.
        pass

    @staticmethod
    def _register_routers(app: FastAPI):
        """Register all application routers."""
        app.include_router(router, prefix="/api/v1", tags=["analytics"])

    @staticmethod
    def _configure_middleware(app: FastAPI):
        """Set up middleware components."""
        # Add CORS, authentication, etc.
        pass

    @staticmethod
    def _register_exception_handlers(app: FastAPI):
        """Register custom exception handlers."""
        pass


app = AppFactory.create_app()
