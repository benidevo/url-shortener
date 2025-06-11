from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models import AnalyticsModel, ClickModel, ResponseModel


def test_should_create_valid_click_model_when_given_valid_data():
    ip = "192.168.1.1"
    city = "San Francisco"
    country = "US"
    created_at = datetime.now(UTC)

    click = ClickModel(ip=ip, city=city, country=country, created_at=created_at)

    assert click.ip == ip
    assert click.city == city
    assert click.country == country
    assert click.created_at == created_at


def test_should_use_default_created_at_when_not_provided():
    click = ClickModel(ip="192.168.1.1", city="San Francisco", country="US")

    assert click.created_at is not None
    assert isinstance(click.created_at, datetime)


def test_should_reject_missing_required_fields_when_creating_click():
    with pytest.raises(ValidationError):
        ClickModel()


def test_should_create_valid_analytics_model_when_given_valid_data():
    short_link = "test1234"
    clicks = [
        ClickModel(ip="192.168.1.1", city="SF", country="US"),
        ClickModel(ip="10.0.0.1", city="NYC", country="US"),
    ]
    updated_at = datetime.now()

    analytics = AnalyticsModel(
        short_link=short_link, clicks=clicks, updated_at=updated_at
    )

    assert analytics.short_link == short_link
    assert len(analytics.clicks) == 2
    assert analytics.updated_at == updated_at


def test_should_handle_empty_clicks_list():
    analytics = AnalyticsModel(short_link="test1234", clicks=[])

    assert len(analytics.clicks) == 0
    assert analytics.clicks == []


def test_should_reject_invalid_clicks_when_creating_analytics():
    with pytest.raises(ValidationError):
        AnalyticsModel(short_link="test1234", clicks=["invalid_click"])  # type: ignore


def test_should_create_valid_response_model_with_analytics_data():
    analytics = AnalyticsModel(short_link="test1234", clicks=[])

    response = ResponseModel(success=True, data=analytics)

    assert response.success is True
    assert response.data == analytics


def test_should_create_valid_response_model_with_analytics_list():
    analytics_list = [
        AnalyticsModel(short_link="test1234", clicks=[]),
        AnalyticsModel(short_link="demo5678", clicks=[]),
    ]

    response = ResponseModel(success=True, data=analytics_list)

    assert response.success is True
    assert response.data == analytics_list
    assert len(response.data) == 2  # type: ignore


def test_should_use_default_values_when_creating_response():
    response = ResponseModel()

    assert response.success is True
    assert response.data is None


def test_should_serialize_models_to_json():
    click = ClickModel(
        ip="192.168.1.1",
        city="San Francisco",
        country="US",
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
    )

    analytics = AnalyticsModel(
        short_link="test1234",
        clicks=[click],
        updated_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
    )

    json_data = analytics.model_dump_json()

    assert "test1234" in json_data
    assert "192.168.1.1" in json_data
    assert "San Francisco" in json_data
    assert "2023-01-01T12:00:00" in json_data


def test_should_handle_large_click_lists():
    clicks = [
        ClickModel(ip=f"192.168.1.{i}", city="City", country="US") for i in range(100)
    ]

    analytics = AnalyticsModel(short_link="test1234", clicks=clicks)

    assert len(analytics.clicks) == 100
    assert all(isinstance(click, ClickModel) for click in analytics.clicks)
