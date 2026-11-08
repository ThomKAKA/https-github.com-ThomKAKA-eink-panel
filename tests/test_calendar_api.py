"""Calendar page HTTP surface: read-only document, preview and frame."""

from __future__ import annotations

import hashlib
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import server.main as server


@pytest.fixture
def client():
    with TestClient(server.app) as result:
        yield result


def test_calendar_defaults_to_an_empty_document(client):
    response = client.get("/api/pages/calendar")
    assert response.status_code == 200
    body = response.json()
    assert body["revision"] == 1
    assert body["data"] == {}


def test_calendar_page_is_read_only(client):
    response = client.put(
        "/api/pages/calendar", json={"revision": 1, "data": {"month": "2026-12"}}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Page is read-only"


def test_preview_renders_the_current_month(client):
    response = client.post("/api/pages/calendar/preview", json={"ignored": True})
    assert response.status_code == 200
    assert Image.open(io.BytesIO(response.content)).size == (400, 300)
    assert response.headers["x-frame-bytes"] == "15000"
    assert response.headers["x-frame-format"] == "epd-t-400x300-mono1-msb-v1"


def test_selecting_calendar_serves_the_cached_frame(client):
    selected = client.post("/api/pages/calendar/select")
    assert selected.status_code == 200
    assert selected.json()["page"] == "calendar"

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
    assert status["page"] == "calendar"
    assert status["frame_version"] == frame.headers["etag"][1:-1]
    assert status["publish_id"] == "calendar-r1"
