from datetime import UTC, datetime

from app.models import ClickModel


def test_should_record_click_when_no_existing_analytics(
    repository, sample_clicks, sample_short_links
):
    click = sample_clicks[0]
    short_link = sample_short_links[0]

    result = repository.record_click(click, short_link)

    assert result is not None
    assert result.short_link == short_link
    assert len(result.clicks) == 1
    assert result.clicks[0].ip == click.ip
    assert result.clicks[0].city == click.city
    assert result.clicks[0].country == click.country


def test_should_add_click_to_existing_analytics(
    repository, sample_clicks, sample_short_links
):
    click1 = sample_clicks[0]
    click2 = sample_clicks[1]
    short_link = sample_short_links[0]

    repository.record_click(click1, short_link)
    result = repository.record_click(click2, short_link)

    assert result is not None
    assert result.short_link == short_link
    assert len(result.clicks) == 2
    stored_ips = {click.ip for click in result.clicks}
    assert click1.ip in stored_ips
    assert click2.ip in stored_ips


def test_should_retrieve_analytics_when_exists(
    repository, sample_clicks, sample_short_links
):
    click = sample_clicks[0]
    short_link = sample_short_links[0]

    repository.record_click(click, short_link)
    result = repository.get_analytics_by_short_link(short_link)

    assert result is not None
    assert result.short_link == short_link
    assert len(result.clicks) == 1
    assert result.clicks[0].ip == click.ip


def test_should_return_none_when_analytics_not_found(repository, sample_short_links):
    result = repository.get_analytics_by_short_link(sample_short_links[0])

    assert result is None


def test_should_update_timestamp_when_recording_click(
    repository, sample_clicks, sample_short_links
):
    click1 = sample_clicks[0]
    click2 = sample_clicks[1]
    short_link = sample_short_links[0]

    first_result = repository.record_click(click1, short_link)
    first_timestamp = first_result.updated_at

    second_result = repository.record_click(click2, short_link)
    second_timestamp = second_result.updated_at

    assert second_timestamp >= first_timestamp


def test_should_handle_multiple_short_links_independently(
    repository, sample_clicks, sample_short_links
):
    click1 = sample_clicks[0]
    click2 = sample_clicks[1]
    short_link1 = sample_short_links[0]
    short_link2 = sample_short_links[1]

    repository.record_click(click1, short_link1)
    repository.record_click(click2, short_link2)

    result1 = repository.get_analytics_by_short_link(short_link1)
    result2 = repository.get_analytics_by_short_link(short_link2)

    assert result1 is not None
    assert result2 is not None
    assert result1.short_link == short_link1
    assert result2.short_link == short_link2
    assert len(result1.clicks) == 1
    assert len(result2.clicks) == 1
    assert result1.clicks[0].ip == click1.ip
    assert result2.clicks[0].ip == click2.ip


def test_should_persist_clicks_across_sessions(
    repository, sample_clicks, sample_short_links
):
    click = sample_clicks[0]
    short_link = sample_short_links[0]

    repository.record_click(click, short_link)
    repository.session.commit()
    repository.session.close()

    new_session = repository.session.get_bind().connect()
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=new_session)
    new_session_instance = Session()

    from app.repository import SqlAlchemyAnalyticsRepository

    new_repository = SqlAlchemyAnalyticsRepository(new_session_instance)

    result = new_repository.get_analytics_by_short_link(short_link)

    assert result is not None
    assert result.short_link == short_link
    assert len(result.clicks) == 1

    new_session.close()


def test_should_handle_duplicate_ips_for_same_short_link(
    repository, sample_short_links
):
    click1 = ClickModel(
        ip="192.168.1.1",
        city="SF",
        country="US",
        created_at=datetime(2023, 1, 1, tzinfo=UTC),
    )
    click2 = ClickModel(
        ip="192.168.1.1",
        city="SF",
        country="US",
        created_at=datetime(2023, 1, 2, tzinfo=UTC),
    )
    short_link = sample_short_links[0]

    repository.record_click(click1, short_link)
    result = repository.record_click(click2, short_link)

    assert result is not None
    assert len(result.clicks) == 2
    assert all(click.ip == "192.168.1.1" for click in result.clicks)


def test_should_handle_clicks_with_different_timestamps(repository, sample_short_links):
    clicks = [
        ClickModel(
            ip=f"192.168.1.{i}",
            city="City",
            country="US",
            created_at=datetime(2023, 1, i + 1, tzinfo=UTC),
        )
        for i in range(5)
    ]
    short_link = sample_short_links[0]

    for click in clicks:
        repository.record_click(click, short_link)

    result = repository.get_analytics_by_short_link(short_link)

    assert result is not None
    assert len(result.clicks) == 5
    timestamps = [click.created_at for click in result.clicks]
    assert len(set(timestamps)) == 5


def test_should_handle_large_number_of_clicks(repository, sample_short_links):
    short_link = sample_short_links[0]

    for i in range(50):
        click = ClickModel(ip=f"192.168.1.{i}", city=f"City{i}", country="US")
        repository.record_click(click, short_link)

    result = repository.get_analytics_by_short_link(short_link)

    assert result is not None
    assert len(result.clicks) == 50
    assert all(click.country == "US" for click in result.clicks)

    unique_ips = {click.ip for click in result.clicks}
    assert len(unique_ips) == 50
