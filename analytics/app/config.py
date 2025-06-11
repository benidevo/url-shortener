import logging
import sys
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_env_file() -> str:
    """Get the path to the .env file by searching up the directory tree."""
    current_dir = Path(__file__).parent
    search_dir = current_dir

    for _ in range(10):
        if (search_dir / "docker-compose.yaml").exists() or (
            search_dir / ".env.example"
        ).exists():
            return str(search_dir / ".env")
        parent = search_dir.parent
        if parent == search_dir:
            break
        search_dir = parent

    return ".env"


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    ANALYTICS_DATABASE_URL: str
    DATABASE_URL: str | None = None

    SERVICE_PORT: int = 8000

    ANALYTICS_SERVICE_GRPC: str = "analytics:50051"

    ENVIRONMENT: str = "development"

    GRPC_PORT: int = 50051

    model_config = SettingsConfigDict(
        env_file=_get_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    def __post_init__(self):
        if self.DATABASE_URL is None:
            self.DATABASE_URL = self.ANALYTICS_DATABASE_URL

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
