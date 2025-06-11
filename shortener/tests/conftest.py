from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.objects import Base
from app.grpc.client import AnalyticsClient
from app.repository import SqlAlchemyUrlRepository
from app.service import UrlShortenerService


@pytest.fixture
def mock_analytics_client():
    """Mock analytics client for testing"""
    client = Mock(spec=AnalyticsClient)
    client.record_click.return_value = None
    client.record_click_async.return_value = None
    return client


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

    yield SessionLocal

    engine.dispose()


@pytest.fixture
def db_session(in_memory_db):
    """Create a database session for testing"""
    session = in_memory_db()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def repository(db_session):
    """Create a repository instance for testing without cache"""
    with patch("app.repository.get_settings") as mock_settings:
        mock_settings.return_value.CACHE_ENABLED = False
        return SqlAlchemyUrlRepository(db_session)


@pytest.fixture
def service(repository, mock_analytics_client):
    """Create a service instance for testing"""
    return UrlShortenerService(repository, mock_analytics_client)


@pytest.fixture
def sample_urls():
    """Sample URLs for testing"""
    return [
        "https://www.example.com",
        "https://github.com/user/repo",
        "https://docs.python.org/3/",
        "https://stackoverflow.com/questions/12345",
    ]
