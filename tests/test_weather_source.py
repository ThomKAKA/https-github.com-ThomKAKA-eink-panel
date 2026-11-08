"""Open-Meteo multi-city parsing, last-known-good cache and stale transition."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from services.page_registry import FILE_PAGES
from services.page_state import PageStateStore
from services.weather_source import WeatherFetchError, WeatherSource, weather_label


FIXTURE = Path(__file__).parent / "fixtures" / "open_meteo_four_cities.json"
CST = timezone(timedelta(hours=8))
PAYLOAD = json.loads(FIXTURE.read_text(encoding="utf-8"))
CONFIG = {
    "cities": [
        {"id": "tianjin", "name": "天津", "latitude": 39.0842, "longitude": 117.2009},
        {"id": "guilin", "name": "桂林", "latitude": 25.2736, "longitude": 110.2900},
        {"id": "changsha", "name": "长沙", "latitude": 28.2282, "longitude": 112.9388},
        {"id": "nanjing", "name": "南京", "latitude": 32.0603, "longitude": 118.7969},
    ],
    "default_city": "changsha",
    "url": "https://api.open-meteo.com/v1/forecast",
    "timeout_seconds": 8,
    "stale_after_minutes": 90,
}


class Clock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


def client_for(payload=PAYLOAD, status=200, captured=None):
    def handler(request):
        if captured is not None:
            captured.append(request.url.params)
        return httpx.Response(status, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


def failing_client(status=503):
    return httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status, text="down")))


def build(tmp_path, clock, client):
    store = PageStateStore(tmp_path / "pages", FILE_PAGES, clock=clock)
    source = WeatherSource(store, CONFIG, client=client, clock=clock)
    return store, source


def test_request_sends_all_four_coordinates(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 21, 20, tzinfo=CST))
    captured = []
    _, source = build(tmp_path, clock, client_for(captured=captured))
    source.fetch_document()

    params = captured[0]
    assert params["latitude"] == "39.0842,25.2736,28.2282,32.0603"
    assert params["longitude"] == "117.2009,110.29,112.9388,118.7969"
    assert params["timezone"] == "Asia/Shanghai"


def test_parses_every_city_and_the_current_hour_window(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 21, 20, tzinfo=CST))
    _, source = build(tmp_path, clock, client_for())
    document = source.fetch_document()

    assert document["current_city"] == "changsha"
    assert list(document["cities"]) == ["tianjin", "guilin", "changsha", "nanjing"]
    assert document["cities"]["tianjin"]["name"] == "天津"
    assert document["cities"]["tianjin"]["current_temp"] == 2
    assert document["cities"]["tianjin"]["current_label"] == "少云"
    assert document["cities"]["changsha"]["current_temp"] == 14
    assert [hour["hour"] for hour in document["cities"]["changsha"]["hourly"]] == [
        21, 22, 23, 0, 1, 2, 3, 4
    ]
    assert [day["date"] for day in document["cities"]["changsha"]["daily"]] == [
        "11-08", "11-09", "11-10"
    ]
    assert document["stale"] is False
    assert document["source"] == "open-meteo"


def test_hourly_window_crosses_midnight(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 21, 30, tzinfo=CST))
    _, source = build(tmp_path, clock, client_for())
    document = source.fetch_document()
    assert [hour["hour"] for hour in document["cities"]["guilin"]["hourly"]] == [
        21, 22, 23, 0, 1, 2, 3, 4
    ]


@pytest.mark.parametrize("code,label", [(0, "晴"), (2, "多云"), (61, "小雨"), (95, "雷雨"), (999, "未知")])
def test_weather_code_labels(code, label):
    assert weather_label(code) == label


def test_refresh_writes_all_cities(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 21, 20, tzinfo=CST))
    store, source = build(tmp_path, clock, client_for())
    result = source.refresh()
    assert result["ok"] is True
    assert result["stale"] is False
    assert result["revision"] == 2
    document = store.load("weather")
    assert document.data["current_city"] == "changsha"
    assert set(document.data["cities"]) == {"tianjin", "guilin", "changsha", "nanjing"}


def test_refresh_keeps_the_selected_city(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 21, 20, tzinfo=CST))
    store, source = build(tmp_path, clock, client_for())
    source.refresh()
    data = store.load("weather").data
    data["current_city"] = "nanjing"
    store.save("weather", data, 2)

    result = source.refresh()
    assert result["ok"] is True
    assert store.load("weather").data["current_city"] == "nanjing"


def test_failure_keeps_last_good_and_marks_stale_once(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 21, 20, tzinfo=CST))
    store, source = build(tmp_path, clock, client_for())
    assert source.refresh()["revision"] == 2

    clock.value = datetime(2026, 11, 8, 21, 30, tzinfo=CST)
    _, failing = build(tmp_path, clock, failing_client())
    result = failing.refresh()
    assert result["ok"] is False and result["stale"] is False
    assert result["revision"] == 2
    assert store.load("weather").data["cities"]["tianjin"]["current_temp"] == 2

    clock.value = datetime(2026, 11, 8, 23, 0, tzinfo=CST)
    stale = failing.refresh()
    assert stale["ok"] is False and stale["stale"] is True
    assert stale["revision"] == 3
    document = store.load("weather")
    assert document.data["stale"] is True
    assert document.data["cities"]["tianjin"]["current_temp"] == 2

    clock.value = datetime(2026, 11, 8, 23, 10, tzinfo=CST)
    repeated = failing.refresh()
    assert repeated["revision"] == 3
    assert store.load("weather").revision == 3

    clock.value = datetime(2026, 11, 8, 23, 20, tzinfo=CST)
    _, healthy = build(tmp_path, clock, client_for())
    recovered = healthy.refresh()
    assert recovered["ok"] is True and recovered["stale"] is False


def test_a_short_response_is_rejected(tmp_path):
    clock = Clock(datetime(2026, 11, 8, 21, 20, tzinfo=CST))
    _, source = build(tmp_path, clock, client_for(PAYLOAD[:3]))
    with pytest.raises(WeatherFetchError):
        source.fetch_document()
