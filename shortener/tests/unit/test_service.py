from unittest.mock import Mock, patch

import pytest
from pydantic import HttpUrl

from app.models import UrlModel
from app.service import UrlShortenerService


def test_should_generate_short_url_when_given_valid_url(service, sample_urls):
    url = HttpUrl(sample_urls[0])

    result = service.shorten_url(url)

    assert result is not None
    assert result.link == url
    assert len(result.short_link) == 8
    assert result.created_at is not None


def test_should_return_same_short_url_when_same_url_already_exists(
    service, sample_urls
):
    url = HttpUrl(sample_urls[0])

    first_result = service.shorten_url(url)
    second_result = service.shorten_url(url)

    assert first_result.short_link == second_result.short_link
    assert str(first_result.link) == str(second_result.link)


def test_should_generate_different_short_urls_when_given_different_urls(
    service, sample_urls
):
    url1 = HttpUrl(sample_urls[0])
    url2 = HttpUrl(sample_urls[1])

    result1 = service.shorten_url(url1)
    result2 = service.shorten_url(url2)

    assert result1.short_link != result2.short_link
    assert result1.link != result2.link


def test_should_raise_error_when_max_retries_exceeded(mock_analytics_client):
    mock_repository = Mock()
    mock_repository.find_by_url.return_value = None  # URL doesn't exist yet
    mock_repository.get.return_value = UrlModel(
        link=HttpUrl("https://different.com"), short_link="test1234", created_at=None
    )

    service = UrlShortenerService(mock_repository, mock_analytics_client)

    with pytest.raises(ValueError) as exc_info:
        service.shorten_url(HttpUrl("https://example.com"))

    assert "Failed to generate unique short URL" in str(exc_info.value)


def test_should_return_none_when_url_not_found(service):
    result = service.get_url("missing")

    assert result is None


def test_should_return_url_when_valid_short_code_provided(service, sample_urls):
    url = HttpUrl(sample_urls[0])
    shortened = service.shorten_url(url)

    result = service.get_url(shortened.short_link)

    assert result is not None
    assert result.short_link == shortened.short_link
    assert str(result.link) == str(url)


def test_should_record_analytics_when_url_retrieved(
    service, mock_analytics_client, sample_urls
):
    url = HttpUrl(sample_urls[0])
    shortened = service.shorten_url(url)

    service.get_url(shortened.short_link, "192.168.1.1", "San Francisco", "US")

    assert (
        mock_analytics_client.record_click_async.called
        or mock_analytics_client.record_click.called
    )


def test_should_handle_analytics_error_gracefully(
    service, mock_analytics_client, sample_urls
):
    url = HttpUrl(sample_urls[0])
    shortened = service.shorten_url(url)

    mock_analytics_client.record_click_async.side_effect = Exception("Analytics failed")
    mock_analytics_client.record_click.side_effect = Exception("Analytics failed")

    result = service.get_url(shortened.short_link, "192.168.1.1")

    assert result is not None
    assert result.short_link == shortened.short_link


def test_should_list_all_urls_when_requested(service, sample_urls):
    urls = [HttpUrl(url) for url in sample_urls[:3]]

    for url in urls:
        service.shorten_url(url)

    result = service.get_all_urls()

    assert len(result) >= 3
    stored_links = {str(url_model.link) for url_model in result}
    for original_url in urls:
        assert str(original_url) in stored_links


def test_should_delete_url_when_valid_short_code_provided(service, sample_urls):
    url = HttpUrl(sample_urls[0])
    shortened = service.shorten_url(url)

    service.delete_url(shortened.short_link)
    result = service.get_url(shortened.short_link)

    assert result is None


@patch("app.service.UrlShortenerService._generate_short_url")
def test_should_generate_8_character_short_url(mock_generate, service, sample_urls):
    mock_generate.return_value = "test1234"
    url = HttpUrl(sample_urls[0])

    result = service.shorten_url(url)

    assert len(result.short_link) == 8
    mock_generate.assert_called_once_with(url)
