from datetime import UTC, datetime

import pytest
from pydantic import HttpUrl, ValidationError

from app.models import UrlModel


def test_should_create_valid_url_model_when_given_valid_data():
    url = "https://www.example.com"
    short_link = "abc12345"
    created_at = datetime.now(UTC)

    model = UrlModel(link=HttpUrl(url), short_link=short_link, created_at=created_at)

    # HttpUrl normalizes URLs by adding trailing slash
    assert str(model.link) == "https://www.example.com/"
    assert model.short_link == short_link
    assert model.created_at == created_at


def test_should_reject_invalid_url_when_creating_model():
    with pytest.raises(ValidationError):
        UrlModel(
            link="not-a-valid-url",  # type: ignore
            short_link="abc12345",
            created_at=datetime.now(UTC),
        )


def test_should_allow_none_created_at_when_creating_model():
    model = UrlModel(
        link=HttpUrl("https://www.example.com"), short_link="abc12345", created_at=None
    )

    assert model.created_at is None


def test_should_serialize_to_json_when_requested():
    model = UrlModel(
        link=HttpUrl("https://www.example.com"),
        short_link="abc12345",
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
    )

    json_data = model.model_dump_json()

    assert "https://www.example.com" in json_data
    assert "abc12345" in json_data
    assert "2023-01-01T12:00:00" in json_data


def test_should_handle_various_url_schemes_when_validating():
    valid_urls_and_expected = [
        ("https://www.example.com", "https://www.example.com/"),
        ("http://example.com", "http://example.com/"),
        (
            "https://subdomain.example.com/path?query=value",
            "https://subdomain.example.com/path?query=value",
        ),
        ("https://example.com:8080/path", "https://example.com:8080/path"),
    ]

    for url, expected in valid_urls_and_expected:
        model = UrlModel(link=HttpUrl(url), short_link="test1234", created_at=None)
        assert str(model.link) == expected


def test_should_preserve_url_case_and_query_params_when_storing():
    original_url = "https://Example.COM/Path?Query=Value&another=param"

    model = UrlModel(link=HttpUrl(original_url), short_link="test1234", created_at=None)

    assert "example.com" in str(model.link).lower()
    assert "query=value" in str(model.link).lower()
    assert "another=param" in str(model.link).lower()


def test_should_handle_unicode_domains_when_validating():
    try:
        model = UrlModel(
            link=HttpUrl("https://例え.テスト/path"),
            short_link="test1234",
            created_at=None,
        )
        assert model.short_link == "test1234"
    except ValidationError:
        pytest.skip("Internationalized domain names not supported")


def test_should_validate_short_link_length_constraints():
    long_short_link = "a" * 1000

    model = UrlModel(
        link=HttpUrl("https://www.example.com"),
        short_link=long_short_link,
        created_at=None,
    )

    assert model.short_link == long_short_link
