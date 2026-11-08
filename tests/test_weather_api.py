"""Weather page HTTP surface: read-only document, preview, frame and refresh."""

from __future__ import annotations

import hashlib
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


def weather_data():
    return {
        "city": "长沙",
        "current_temp": 16,
        "current_label": "毛毛雨",
        "hourly": [
            {"hour": (14 + index) % 24, "temp": 16 - index, "label": "毛毛雨"}
            for index in range(8)
        ],
        "daily": [
            {"date": "11-08", "weekday": "周日", "high": 20, "low": 13, "label": "多云"},
            {"date": "11-09", "weekday": "周一", "high": 21, "low": 14, "label": "晴"},
            {"date": "11-10", "weekday": "周二", "high": 19, "low": 12, "label": "阴"},
        ],
        "stale": False,
        "source": "open-meteo",
    }


def test_weather_defaults_to_waiting_document(client):
    response = client.get("/api/pages/weather")
    assert response.status_code == 200
    body = response.json()
    assert body["revision"] == 1
    assert body["data"]["city"] == "长沙"
    assert body["data"]["hourly"] == []
    assert body["data"]["stale"] is True


def test_weather_page_is_read_only(client):
    response = client.put(
        "/api/pages/weather", json={"revision": 1, "data": weather_data()}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Page is read-only"


def test_preview_renders_the_stored_document(client):
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
