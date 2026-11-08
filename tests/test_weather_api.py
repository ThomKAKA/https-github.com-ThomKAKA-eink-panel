"""Weather page HTTP surface: four-city document, switching, preview and refresh."""

from __future__ import annotations

import hashlib
import json
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io

import server.main as server


@pytest.fixture
def client():
    with TestClient(server.app) as result:
        yield result


def city(name: str, temp: int, label: str) -> dict:
    return {
        "name": name,
        "current_temp": temp,
        "current_label": label,
        "hourly": [
            {"hour": (14 + index) % 24, "temp": temp - index, "label": label}
            for index in range(8)
        ],
        "daily": [
            {"date": "11-08", "weekday": "周日", "high": temp + 4, "low": temp - 3, "label": "多云"},
            {"date": "11-09", "weekday": "周一", "high": temp + 5, "low": temp - 2, "label": "晴"},
            {"date": "11-10", "weekday": "周二", "high": temp + 3, "low": temp - 4, "label": "阴"},
        ],
    }


def weather_data() -> dict:
    return {
        "current_city": "changsha",
        "cities": {
            "tianjin": city("天津", 9, "晴"),
            "guilin": city("桂林", 22, "多云"),
            "changsha": city("长沙", 16, "毛毛雨"),
            "nanjing": city("南京", 14, "阴"),
        },
        "stale": False,
        "source": "open-meteo",
    }


def test_weather_defaults_to_waiting_document(client):
    response = client.get("/api/pages/weather")
    assert response.status_code == 200
    body = response.json()
    assert body["revision"] == 1
    assert body["data"]["current_city"] == "changsha"
    assert body["data"]["cities"] == {}
    assert body["data"]["stale"] is True


def test_weather_page_is_read_only(client):
    response = client.put(
        "/api/pages/weather", json={"revision": 1, "data": weather_data()}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Page is read-only"


def test_preview_renders_the_stored_document(client):
    server.page_state.save("weather", weather_data(), 1)
    response = client.post("/api/pages/weather/preview", json={"ignored": True})
    assert response.status_code == 200
    assert Image.open(io.BytesIO(response.content)).size == (400, 300)
    assert response.headers["x-frame-bytes"] == "15000"
    assert response.headers["x-frame-format"] == "epd-t-400x300-mono1-msb-v1"


def test_selecting_weather_serves_the_cached_frame(client):
    server.page_state.save("weather", weather_data(), 1)
    selected = client.post("/api/pages/weather/select")
    assert selected.status_code == 200
    assert selected.json()["page"] == "weather"

    frame = client.get("/api/panels/progress/frame")
    assert frame.status_code == 200
    assert len(frame.content) == 15000
    assert frame.headers["etag"] == '"' + hashlib.sha256(frame.content).hexdigest() + '"'
    assert frame.headers["x-frame-format"] == "epd-t-400x300-mono1-msb-v1"

    unchanged = client.get(
        "/api/panels/progress/frame", headers={"If-None-Match": frame.headers["etag"]}
    )
    assert unchanged.status_code == 304
    status = client.get("/api/pages/status").json()
    assert status["page"] == "weather"
    assert status["frame_version"] == frame.headers["etag"][1:-1]


def test_cities_endpoint_lists_the_configured_cities(client):
    response = client.get("/api/pages/weather/cities")
    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["cities"]] == [
        "tianjin",
        "guilin",
        "changsha",
        "nanjing",
    ]
    assert [item["name"] for item in body["cities"]] == ["天津", "桂林", "长沙", "南京"]
    assert body["current_city"] == "changsha"


def test_a_fifth_city_only_needs_a_config_edit(client, tmp_path, monkeypatch):
    config = {
        "enabled": True,
        "cities": [
            {"id": "tianjin", "name": "天津", "latitude": 39.0842, "longitude": 117.2009},
            {"id": "guilin", "name": "桂林", "latitude": 25.2736, "longitude": 110.29},
            {"id": "changsha", "name": "长沙", "latitude": 28.2282, "longitude": 112.9388},
            {"id": "nanjing", "name": "南京", "latitude": 32.0603, "longitude": 118.7969},
            {"id": "shanghai", "name": "上海", "latitude": 31.2222, "longitude": 121.4581},
        ],
        "default_city": "shanghai",
        "url": "https://api.open-meteo.com/v1/forecast",
        "timeout_seconds": 8,
        "interval_minutes": 60,
        "stale_after_minutes": 90,
    }
    path = tmp_path / "weather.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(server, "WEATHER_CONFIG_PATH", path)

    listed = client.get("/api/pages/weather/cities").json()
    assert [item["id"] for item in listed["cities"]][-1] == "shanghai"
    assert listed["cities"][-1]["name"] == "上海"

    switched = client.post("/api/pages/weather/select-city", json={"city": "shanghai"})
    assert switched.status_code == 200
    assert switched.json()["current_city"] == "shanghai"
    assert server.page_state.load("weather").data["current_city"] == "shanghai"


def test_select_city_switches_the_served_frame(client):
    server.page_state.save("weather", weather_data(), 1)
    stored = server.page_state.load("weather").revision
    client.post("/api/pages/weather/select")
    before = client.get("/api/panels/progress/frame")
    assert before.status_code == 200

    switched = client.post("/api/pages/weather/select-city", json={"city": "guilin"})
    assert switched.status_code == 200
    body = switched.json()
    assert body["current_city"] == "guilin"
    assert body["revision"] == stored + 1

    after = client.get("/api/panels/progress/frame")
    assert after.status_code == 200
    assert len(after.content) == 15000
    assert after.headers["etag"] != before.headers["etag"]
    assert server.page_state.load("weather").data["current_city"] == "guilin"

    repeated = client.post("/api/pages/weather/select-city", json={"city": "guilin"})
    assert repeated.status_code == 200
    assert repeated.json()["revision"] == stored + 1


def test_select_city_rejects_unknown_or_missing_city(client):
    server.page_state.save("weather", weather_data(), 1)
    unknown = client.post("/api/pages/weather/select-city", json={"city": "beijing"})
    assert unknown.status_code == 422
    missing = client.post("/api/pages/weather/select-city", json={})
    assert missing.status_code == 422


def test_refresh_uses_the_configured_source(client, monkeypatch):
    source = Mock()
    source.refresh.return_value = {
        "ok": True,
        "stale": False,
        "revision": 2,
        "updated_at": "2026-11-08 14:20",
        "error": None,
    }
    monkeypatch.setattr(server.app.state, "weather_source", source, raising=False)
    response = client.post("/api/pages/weather/refresh")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    source.refresh.assert_called_once_with()


def test_refresh_reports_an_unconfigured_source(client, monkeypatch):
    monkeypatch.setattr(server.app.state, "weather_source", None, raising=False)
    response = client.post("/api/pages/weather/refresh")
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["error"] == "weather source unavailable"
