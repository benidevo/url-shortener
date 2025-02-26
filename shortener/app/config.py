from functools import lru_cache
from typing import Optional
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


class Settings(BaseSettings):
    """Application settings configured from environment variables."""

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: str = "logs"

    DATABASE_URL: PostgresDsn

    BASE_URL: str = "http://localhost:8000"
    SERVICE_PORT: int = 8000

    ANALYTICS_SERVICE_GRPC: str = "analytics:50051"

    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def configure_logging(self):
        """Configure logging based on settings."""

        numeric_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)

        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        if root_logger.handlers:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))

        root_logger.addHandler(console_handler)

        # Reduce noise from third-party libraries
        # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        # logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

        logging.info("Logging configured with level: %s", self.LOG_LEVEL)


@lru_cache()
def get_settings() -> Settings:
    """Create and return a cached Settings instance."""
    settings = Settings()
    settings.configure_logging()
    return settings
