import logging
import sys
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    DATABASE_URL: str

    SERVICE_PORT: int = 8000

    ANALYTICS_SERVICE_GRPC: str = "analytics:50051"

    ENVIRONMENT: str = "development"

    CACHE_ENABLED: bool = True
    CACHE_MAX_SIZE: int = 1000
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_CONNECTION_POOL_SIZE: int = 10
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_TIMEOUT: int = 5

    model_config = SettingsConfigDict(
        case_sensitive=True,
    )

    def configure_logging(self):
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

        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

        logging.info("Logging configured with level: %s", self.LOG_LEVEL)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[call-arg]
    settings.configure_logging()
    return settings
