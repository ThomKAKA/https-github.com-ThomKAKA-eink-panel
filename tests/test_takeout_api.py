"""HTTP contract for takeout orders, previews and the served frame."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib

import pytest
from fastapi.testclient import TestClient

import server.main as server
from services.event_store import EventStateStore
from services.page_frames import PageFrameService
from services.progress_frame import ProgressFramePublisher


SHANGHAI = timezone(timedelta(hours=8))


@pytest.fixture
def client(monkeypatch):
    store = EventStateStore()
    publisher = ProgressFramePublisher(store, "lan")
    monkeypatch.setattr(server, "event_store", store)
    monkeypatch.setattr(server, "frame_publisher", publisher)
    with TestClient(server.app) as result:
        yield result


def order(identifier: str = "t1", *, status: str = "waiting",
          expected: str | None = "12:30", name: str = "牛肉面") -> dict:
    return {
        "id": identifier,
        "name": name,
        "status": status,
        "expected_at": expected,
    }


def receive(client, payload: dict):
    return client.post("/api/takeout/orders", json=payload)


def save(client, data: dict, revision: int = 1):
    return client.put("/api/pages/takeout", json={"revision": revision, "data": data})


def test_takeout_starts_empty(client):
    body = client.get("/api/pages/takeout")
    assert body.status_code == 200
    assert body.json()["revision"] == 1
    assert body.json()["data"] == {"orders": []}

    listing = client.get("/api/pages")
    assert {"id": "takeout", "title": "外卖", "kind": "file", "revision": 1} in listing.json()["pages"]


def test_takeout_accepts_an_order_and_exposes_it(client):
    response = receive(client, order())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["revision"] == 2
    assert body["order"] == order()

    stored = client.get("/api/pages/takeout").json()
    assert stored["revision"] == 2
    assert stored["data"]["orders"] == [order()]


def test_takeout_status_can_only_move_forward(client):
    assert receive(client, order()).status_code == 200
    delivering = receive(client, order(status="delivering"))
    assert delivering.status_code == 200
    assert delivering.json()["revision"] == 3

    backwards = receive(client, order(status="waiting"))
    assert backwards.status_code == 422
    assert client.get("/api/pages/takeout").json()["revision"] == 3

    arrived = receive(client, order(status="arrived"))
    assert arrived.status_code == 200
    blocked = receive(client, order(status="delivering"))
    assert blocked.status_code == 422
    assert client.get("/api/pages/takeout").json()["revision"] == 4


def test_takeout_same_status_update_is_allowed(client):
    receive(client, order())
    updated = receive(client, {**order(), "note": "放前台", "expected_at": "12:40"})
    assert updated.status_code == 200
    assert updated.json()["order"]["note"] == "放前台"
    assert updated.json()["order"]["expected_at"] == "12:40"


def test_takeout_caps_orders_at_six(client):
    for index in range(6):
        assert receive(client, order(f"t{index}", name=f"单{index}")).status_code == 200

    seventh = receive(client, order("t6", name="第七单"))
    assert seventh.status_code == 422
    assert len(client.get("/api/pages/takeout").json()["data"]["orders"]) == 6


@pytest.mark.parametrize("payload", [
    {**order(), "extra": 1},
    {**order(), "status": "late"},
    {**order(), "expected_at": "24:00"},
    {**order(), "name": ""},
    {**order(), "id": "bad id"},
])
def test_takeout_rejects_invalid_orders(client, payload):
    response = receive(client, payload)
    assert response.status_code == 422
    assert client.get("/api/pages/takeout").json()["revision"] == 1


def test_takeout_can_be_saved_and_previewed(client):
    data = {"orders": [order(), order("t2", status="arrived", expected="12:00", name="水果")]}
    saved = save(client, data)
    assert saved.status_code == 200
    assert saved.json()["revision"] == 2

    preview = client.post("/api/pages/takeout/preview", json=data)
    assert preview.status_code == 200
    assert preview.headers["x-frame-format"] == "epd-t-400x300-mono1-msb-v1"
    assert preview.headers["x-frame-bytes"] == "15000"


def test_takeout_order_without_expected_time_is_accepted(client):
    response = receive(client, order("t1", expected=None))
    assert response.status_code == 200


def test_takeout_frame_crosses_the_expected_minute(client, monkeypatch):
    class Clock:
        value = datetime(2026, 11, 8, 12, 30, tzinfo=SHANGHAI)

        def __call__(self):
            return self.value

    clock = Clock()
    monkeypatch.setattr(
        server,
        "page_frames",
        PageFrameService(server.page_state, lambda: server.frame_publisher, clock=clock),
    )
    assert receive(client, order()).status_code == 200
    assert client.post("/api/pages/takeout/select").status_code == 200

    before = client.get("/api/panels/progress/frame")
    assert before.status_code == 200
    assert len(before.content) == 15000
    assert before.headers["etag"] == '"' + hashlib.sha256(before.content).hexdigest() + '"'

    clock.value = datetime(2026, 11, 8, 12, 31, tzinfo=SHANGHAI)
    after = client.get(
        "/api/panels/progress/frame",
        headers={"If-None-Match": before.headers["etag"]},
    )
    assert after.status_code == 200
    assert after.headers["etag"] != before.headers["etag"]
    assert after.content != before.content

    preview = client.post("/api/pages/takeout/preview", json={"orders": [order()]})
    assert preview.status_code == 200
    assert preview.headers["x-frame-version"] == after.headers["etag"][1:-1]

    status = client.get("/api/pages/status").json()
    assert status["page"] == "takeout"
    assert status["host_stage"] == "FRAME_READY"
    assert status["frame_version"] == after.headers["etag"][1:-1]


def test_takeout_frame_is_stable_within_the_same_minute(client, monkeypatch):
    class Clock:
        value = datetime(2026, 11, 8, 12, 30, 10, tzinfo=SHANGHAI)

        def __call__(self):
            return self.value

    clock = Clock()
    monkeypatch.setattr(
        server,
        "page_frames",
        PageFrameService(server.page_state, lambda: server.frame_publisher, clock=clock),
    )
    assert receive(client, order()).status_code == 200
    client.post("/api/pages/takeout/select")

    first = client.get("/api/panels/progress/frame")
    clock.value = datetime(2026, 11, 8, 12, 30, 55, tzinfo=SHANGHAI)
    second = client.get(
        "/api/panels/progress/frame",
        headers={"If-None-Match": first.headers["etag"]},
    )
    assert second.status_code == 304
    assert second.content == b""
