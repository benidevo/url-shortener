from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.objects import Base
from app.models import ClickModel
from app.repository import SqlAlchemyAnalyticsRepository
from app.service import AnalyticsService


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield SessionLocal

    engine.dispose()


@pytest.fixture
def db_session(in_memory_db):
    session = in_memory_db()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def repository(db_session):
    return SqlAlchemyAnalyticsRepository(db_session)


@pytest.fixture
def service(repository):
    return AnalyticsService(repository)


@pytest.fixture
def sample_clicks():
    return [
        ClickModel(
            ip="192.168.1.1",
            city="San Francisco",
            country="US",
            created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        ),
        ClickModel(
            ip="10.0.0.1",
            city="New York",
            country="US",
            created_at=datetime(2023, 1, 2, 14, 30, 0, tzinfo=UTC),
        ),
        ClickModel(
            ip="172.16.0.1",
            city="London",
            country="UK",
            created_at=datetime(2023, 1, 3, 16, 45, 0, tzinfo=UTC),
        ),
    ]


@pytest.fixture
def sample_short_links():
    return ["test123", "demo456", "sample78"]
