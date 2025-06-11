from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from app.models import AnalyticsModel
from app.service import AnalyticsService


def test_should_retrieve_analytics_when_short_link_exists(
    sample_clicks, sample_short_links
):
    mock_repository = Mock()
    expected_analytics = AnalyticsModel(
        short_link=sample_short_links[0],
        clicks=sample_clicks,
        updated_at=datetime.now(UTC),
    )
    mock_repository.get_analytics_by_short_link.return_value = expected_analytics

    service = AnalyticsService(mock_repository)

    result = service.retrieve_analytics(sample_short_links[0])

    assert result is not None
    assert result.short_link == sample_short_links[0]
    assert len(result.clicks) == len(sample_clicks)
    mock_repository.get_analytics_by_short_link.assert_called_once_with(
        sample_short_links[0]
    )


def test_should_return_none_when_short_link_not_found(sample_short_links):
    mock_repository = Mock()
    mock_repository.get_analytics_by_short_link.return_value = None

    service = AnalyticsService(mock_repository)

    result = service.retrieve_analytics(sample_short_links[0])

    assert result is None
    mock_repository.get_analytics_by_short_link.assert_called_once_with(
        sample_short_links[0]
    )


def test_should_handle_empty_short_link_gracefully():
    mock_repository = Mock()
    mock_repository.get_analytics_by_short_link.return_value = None

    service = AnalyticsService(mock_repository)

    result = service.retrieve_analytics("")

    assert result is None
    mock_repository.get_analytics_by_short_link.assert_called_once_with("")


def test_should_handle_repository_error_gracefully(sample_short_links):
    mock_repository = Mock()
    mock_repository.get_analytics_by_short_link.side_effect = Exception(
        "Database error"
    )

    service = AnalyticsService(mock_repository)

    with pytest.raises(Exception):  # noqa: B017
        service.retrieve_analytics(sample_short_links[0])

    mock_repository.get_analytics_by_short_link.assert_called_once_with(
        sample_short_links[0]
    )


def test_should_pass_through_repository_result_unchanged(
    sample_clicks, sample_short_links
):
    mock_repository = Mock()
    expected_analytics = AnalyticsModel(
        short_link=sample_short_links[0],
        clicks=sample_clicks[:2],
        updated_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    mock_repository.get_analytics_by_short_link.return_value = expected_analytics

    service = AnalyticsService(mock_repository)

    result = service.retrieve_analytics(sample_short_links[0])

    assert result == expected_analytics
    assert result.short_link == expected_analytics.short_link
    assert result.clicks == expected_analytics.clicks
    assert result.updated_at == expected_analytics.updated_at
