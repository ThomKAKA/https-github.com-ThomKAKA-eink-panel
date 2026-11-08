"""HTTP contract for the pet page, its state view and interactions."""

from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient

import server.main as server
from services.event_store import EventStateStore
from services.progress_frame import ProgressFramePublisher


@pytest.fixture
def client(monkeypatch):
    store = EventStateStore()
    publisher = ProgressFramePublisher(store, "lan")
    monkeypatch.setattr(server, "event_store", store)
    monkeypatch.setattr(server, "frame_publisher", publisher)
    with TestClient(server.app) as result:
        yield result


def interact(client, action: str):
    return client.post("/api/pet/interact", json={"action": action})


def test_pet_is_a_registered_read_only_page(client):
    listing = client.get("/api/pages").json()
    assert {"id": "pet", "title": "宠物", "kind": "file", "revision": 1} in listing["pages"]
    status = client.get("/api/pages/status").json()
    assert "pet" in [page["id"] for page in status["pages"]]

    body = client.get("/api/pages/pet")
    assert body.status_code == 200
    assert body.json()["data"] == {
        "name": "大肥鱼",
        "satiety": 50,
        "mood": 60,
        "affinity": 0,
    }


def test_pet_page_rejects_writes(client):
    response = client.put("/api/pages/pet", json={"revision": 1, "data": {"satiety": 80}})

    assert response.status_code == 400
    assert response.json()["detail"] == "Page is read-only"


def test_pet_state_view_reports_today(client):
    response = client.get("/api/pet/state")

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == "pet"
    assert body["revision"] == 1
    assert body["name"] == "大肥鱼"
    assert (body["satiety"], body["mood"], body["affinity"], body["level"]) == (50, 60, 0, 1)
    assert body["fed_today"] is False
    assert body["satiety_label"] == "正常"
    assert body["mood_label"] == "一般"


def test_feed_advances_the_revision_and_the_state(client):
    response = interact(client, "feed")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["revision"] == 2
    assert body["action"] == "feed"
    assert body["state"]["satiety"] == 80
    assert body["state"]["affinity"] == 2
    assert body["state"]["fed_today"] is True

    stored = client.get("/api/pages/pet").json()
    assert stored["revision"] == 2
    assert stored["data"]["satiety"] == 80
    assert stored["data"]["last_fed"] is not None


def test_unknown_action_is_rejected(client):
    assert interact(client, "sleep").status_code == 422
    assert client.post("/api/pet/interact", json={}).status_code == 422


def test_pet_preview_matches_the_served_frame(client):
    preview = client.post("/api/pages/pet/preview")
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/png"
    assert preview.headers["X-Frame-Format"] == "epd-t-400x300-mono1-msb-v1"
    assert preview.headers["X-Frame-Bytes"] == "15000"

    assert client.post("/api/pages/pet/select").status_code == 200
    frame = client.get("/api/panels/progress/frame")
    assert frame.status_code == 200
    assert len(frame.content) == 15000
    assert frame.headers["X-Frame-Format"] == "epd-t-400x300-mono1-msb-v1"
    etag = frame.headers["ETag"].strip('"')
    assert etag == hashlib.sha256(frame.content).hexdigest()
    assert preview.headers["X-Frame-Version"] == etag


def test_interaction_produces_a_new_frame(client):
    client.post("/api/pages/pet/select")
    first = client.get("/api/panels/progress/frame")
    assert first.status_code == 200

    assert interact(client, "play").status_code == 200
    changed = client.get(
        "/api/panels/progress/frame",
        headers={"If-None-Match": first.headers["ETag"]},
    )
    assert changed.status_code == 200
    assert changed.headers["ETag"] != first.headers["ETag"]

    unchanged = client.get(
        "/api/panels/progress/frame",
        headers={"If-None-Match": changed.headers["ETag"]},
    )
    assert unchanged.status_code == 304
