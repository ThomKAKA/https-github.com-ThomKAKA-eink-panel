"""Codex usage page HTTP surface: read-only document, ingest, preview and frame."""

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


def usage_payload():
    return {
        "today_tokens": 0,
        "week_tokens": 22646123,
        "total_tokens": 132173864,
        "responses": 878,
        "sessions": 6,
        "last_activity": "11-07 15:10",
        "used_percent": 0.0,
        "window_minutes": 43200,
        "resets_at": "12-07",
        "plan": "free",
        "quota_at": "11-07 15:10",
        "days": [{"date": "11-08", "tokens": 0}],
        "source": "codex-sessions",
    }


def test_codex_defaults_to_an_empty_document(client):
    response = client.get("/api/pages/codex")
    assert response.status_code == 200
    body = response.json()
    assert body["revision"] == 1
    assert body["data"] == {}


def test_codex_page_is_read_only(client):
    response = client.put("/api/pages/codex", json={"revision": 1, "data": usage_payload()})
    assert response.status_code == 400
    assert response.json()["detail"] == "Page is read-only"


def test_usage_ingest_stores_a_fresh_document(client):
    ingest = client.post("/api/pages/codex/usage", json=usage_payload())
    assert ingest.status_code == 200
    assert ingest.json()["ok"] is True
    assert ingest.json()["revision"] == 2
    assert ingest.json()["stale"] is False

    document = client.get("/api/pages/codex").json()
    assert document["revision"] == 2
    assert document["data"]["week_tokens"] == 22646123
    assert document["data"]["stale"] is False
    assert document["updated_at"]


def test_usage_ingest_rejects_invalid_numbers(client):
    payload = usage_payload()
    payload["today_tokens"] = -1
    response = client.post("/api/pages/codex/usage", json=payload)
    assert response.status_code == 422
    assert client.get("/api/pages/codex").json()["revision"] == 1


def test_preview_renders_the_stored_document(client):
    client.post("/api/pages/codex/usage", json=usage_payload())
    response = client.post("/api/pages/codex/preview", json={"ignored": True})
    assert response.status_code == 200
    assert Image.open(io.BytesIO(response.content)).size == (400, 300)
    assert response.headers["x-frame-bytes"] == "15000"
    assert response.headers["x-frame-format"] == "epd-t-400x300-mono1-msb-v1"


def test_selecting_codex_serves_the_cached_frame(client):
    client.post("/api/pages/codex/usage", json=usage_payload())
    selected = client.post("/api/pages/codex/select")
    assert selected.status_code == 200
    assert selected.json()["page"] == "codex"

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
    assert status["page"] == "codex"
    assert status["frame_version"] == frame.headers["etag"][1:-1]
    assert status["publish_id"] == "codex-r2"
