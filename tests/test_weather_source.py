"""Open-Meteo parsing, last-known-good cache and stale transition."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from services.page_registry import FILE_PAGES
from services.page_state import PageStateStore
from services.weather_source import WeatherFetchError, WeatherSource, weather_label


FIXTURE = Path(__file__).parent / "fixtures" / "open_meteo_changsha.json"
CST = timezone(timedelta(hours=8))
PAYLOAD = json.loads(FIXTURE.read_text(encoding="utf-8"))
CONFIG = {
    "city": "长沙",
    "url": "https://api.open-meteo.com/v1/forecast",
    "latitude": 28.2282,
    "longitude": 112.9388,
    "timeout_seconds": 8,
    "stale_after_minutes": 90,
}


class Clock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


def client_for(payload=PAYLOAD, status=200):
    return httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status, json=payload)))


def failing_client(status=503):
    return httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status, text="down")))


def build(tmp_path, clock, client):
    store = PageStateStore(tmp_path / "pages", FILE_PAGES, clock=clock)
    source = WeatherSource(store, CONFIG, client=client, clock=clock)
    return store, source


def test_parses_current_hourly_window_and_daily(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 14, 20, tzinfo=CST))
    _, source = build(tmp_path, clock, client_for())
    document = source.fetch_document()
    assert document["city"] == "长沙"
    assert document["current_temp"] == 15
    assert document["current_label"] == "毛毛雨"
    assert [hour["hour"] for hour in document["hourly"]] == [14, 15, 16, 17, 18, 19, 20, 21]
    assert document["hourly"][0]["temp"] == 15
    assert [day["date"] for day in document["daily"]] == ["11-08", "11-09", "11-10"]
    assert document["daily"][0]["weekday"] == "周日"
    assert document["stale"] is False
    assert document["source"] == "open-meteo"


def test_hourly_window_crosses_midnight(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 23, 30, tzinfo=CST))
    _, source = build(tmp_path, clock, client_for())
    document = source.fetch_document()
    assert [hour["hour"] for hour in document["hourly"]] == [23, 0, 1, 2, 3, 4, 5, 6]


@pytest.mark.parametrize("code,label", [(0, "晴"), (2, "多云"), (61, "小雨"), (95, "雷雨"), (999, "未知")])
def test_weather_code_labels(code, label):
    assert weather_label(code) == label


def test_refresh_writes_the_document(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 14, 20, tzinfo=CST))
    store, source = build(tmp_path, clock, client_for())
    result = source.refresh()
    assert result["ok"] is True
    assert result["stale"] is False
    assert result["revision"] == 2
    assert result["error"] is None
    document = store.load("weather")
    assert document.revision == 2
    assert document.data["current_temp"] == 15


def test_failure_keeps_last_good_and_marks_stale_once(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 14, 20, tzinfo=CST))
    store, source = build(tmp_path, clock, client_for())
    assert source.refresh()["revision"] == 2

    clock.value = datetime(2026, 11, 8, 14, 30, tzinfo=CST)
    _, failing = build(tmp_path, clock, failing_client())
    result = failing.refresh()
    assert result["ok"] is False and result["stale"] is False
    assert result["revision"] == 2
    assert store.load("weather").data["current_temp"] == 15

    clock.value = datetime(2026, 11, 8, 16, 0, tzinfo=CST)
    stale = failing.refresh()
    assert stale["ok"] is False and stale["stale"] is True
    assert stale["revision"] == 3
    document = store.load("weather")
    assert document.data["stale"] is True
    assert document.data["current_temp"] == 15

    clock.value = datetime(2026, 11, 8, 16, 10, tzinfo=CST)
    repeated = failing.refresh()
    assert repeated["revision"] == 3
    assert store.load("weather").revision == 3

    clock.value = datetime(2026, 11, 8, 16, 20, tzinfo=CST)
    _, healthy = build(tmp_path, clock, client_for())
    recovered = healthy.refresh()
    assert recovered["ok"] is True and recovered["stale"] is False
    assert recovered["revision"] == 4


def test_failure_without_any_data_does_not_write(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 14, 20, tzinfo=CST))
    store, source = build(tmp_path, clock, failing_client())
    result = source.refresh()
    assert result["ok"] is False and result["stale"] is True
    assert result["revision"] == 1
    assert store.load("weather").revision == 1


def test_invalid_payload_is_a_fetch_error(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 14, 20, tzinfo=CST))
    _, source = build(tmp_path, clock, client_for(payload={"current": {}}))
    with pytest.raises(WeatherFetchError):
        source.fetch_document()
