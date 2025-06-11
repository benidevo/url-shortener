from unittest.mock import patch

import pytest
from pydantic import HttpUrl
from sqlalchemy.exc import IntegrityError


def test_should_create_url_when_given_valid_data(repository, sample_urls):
    url = HttpUrl(sample_urls[0])
    short_link = "test1234"

    result = repository.create(short_link, url)

    assert result is not None
    assert result.short_link == short_link
    assert str(result.link) == str(url)
    assert result.created_at is not None


def test_should_retrieve_url_when_exists_in_database(repository, sample_urls):
    url = HttpUrl(sample_urls[0])
    short_link = "test1234"

    repository.create(short_link, url)
    result = repository.get(short_link)

    assert result is not None
    assert result.short_link == short_link
    assert str(result.link) == str(url)


def test_should_return_none_when_url_not_in_database(repository):
    result = repository.get("missing")

    assert result is None


def test_should_return_same_url_when_creating_duplicate(repository, sample_urls):
    url = HttpUrl(sample_urls[0])
    short_link = "test1234"

    first = repository.create(short_link, url)
    second = repository.create(short_link, url)

    assert first.short_link == second.short_link
    assert str(first.link) == str(second.link)


def test_should_raise_error_when_short_link_collision_occurs(repository, sample_urls):
    url1 = HttpUrl(sample_urls[0])
    url2 = HttpUrl(sample_urls[1])
    short_link = "test1234"

    repository.create(short_link, url1)

    with pytest.raises(IntegrityError):
        repository.create(short_link, url2)


def test_should_list_all_urls_when_multiple_exist(repository, sample_urls):
    urls = [HttpUrl(url) for url in sample_urls[:3]]
    short_links = ["test001", "test002", "test003"]

    for url, short_link in zip(urls, short_links, strict=False):
        repository.create(short_link, url)

    result = repository.list()

    assert len(result) >= 3
    stored_links = {str(url_model.link) for url_model in result}
    for original_url in urls:
        assert str(original_url) in stored_links


def test_should_delete_url_when_exists(repository, sample_urls):
    url = HttpUrl(sample_urls[0])
    short_link = "test1234"

    repository.create(short_link, url)
    repository.delete(short_link)
    result = repository.get(short_link)

    assert result is None


def test_should_handle_delete_when_url_not_exists(repository):
    repository.delete("missing")


@patch("app.repository.get_settings")
def test_should_use_cache_when_enabled(mock_settings, repository, sample_urls):
    mock_settings.return_value.CACHE_ENABLED = True
    mock_settings.return_value.CACHE_TTL_SECONDS = 300

    url = HttpUrl(sample_urls[0])
    short_link = "test1234"

    repository.create(short_link, url)

    result1 = repository.get(short_link)
    result2 = repository.get(short_link)

    assert result1 is not None
    assert result2 is not None
    assert result1.short_link == result2.short_link
    assert str(result1.link) == str(result2.link)


def test_should_handle_database_transaction_rollback(repository, sample_urls):
    url = HttpUrl(sample_urls[0])
    short_link = "test1234"

    repository.create(short_link, url)

    with pytest.raises(IntegrityError):
        repository.create(short_link, HttpUrl(sample_urls[1]))

    result = repository.get(short_link)
    assert result is not None
    assert str(result.link) == str(url)


def test_should_handle_multiple_concurrent_operations(repository, sample_urls):
    urls = [HttpUrl(url) for url in sample_urls]
    short_links = [f"test{i:03d}" for i in range(len(urls))]

    for url, short_link in zip(urls, short_links, strict=False):
        repository.create(short_link, url)

    for short_link in short_links:
        result = repository.get(short_link)
        assert result is not None

    all_urls = repository.list()
    assert len(all_urls) >= len(urls)

    for i in range(0, len(short_links), 2):
        repository.delete(short_links[i])

    for i in range(0, len(short_links), 2):
        result = repository.get(short_links[i])
        assert result is None

    for i in range(1, len(short_links), 2):
        result = repository.get(short_links[i])
        assert result is not None
