"""HTTP surface for page selection, editing and preview."""

from __future__ import annotations

import hashlib
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import server.main as server
from services.event_store import EventStateStore
from services.progress_frame import FRAME_FORMAT, ProgressFramePublisher


LEGACY_KEYS = {"publish_id", "frame_version", "host_stage", "source", "frame_format", "device"}


@pytest.fixture
def client(monkeypatch):
    store = EventStateStore()
    publisher = ProgressFramePublisher(store, "lan")
    monkeypatch.setattr(server, "event_store", store)
    monkeypatch.setattr(server, "frame_publisher", publisher)
    with TestClient(server.app) as result:
        yield result


def memo_data(*texts: str) -> dict:
    return {
        "items": [
            {"id": f"i{index}", "text": text, "face": "todo"}
            for index, text in enumerate(texts or ("买牛奶",))
        ]
    }


def course_data() -> dict:
    return {
        "semester_start": "2026-09-07",
        "total_weeks": 18,
        "courses": [
            {"id": "a", "name": "高等数学", "weekday": 7, "weeks": [9],
             "period": 1, "room": "A-101"},
        ],
        "overrides": [],
    }


def save(client, page: str, data: dict, revision: int = 1):
    return client.put(f"/api/pages/{page}", json={"revision": revision, "data": data})


def test_page_list_and_page_aware_status(client):
    listing = client.get("/api/pages")
    assert listing.status_code == 200
    assert listing.headers["cache-control"] == "no-store"
    assert listing.json()["current"] == "progress"
    assert [page["id"] for page in listing.json()["pages"]] == [
        "progress",
        "memo",
        "course",
        "weather",
        "calendar",
        "codex",
        "takeout",
        "pet",
    ]
    assert [page["kind"] for page in listing.json()["pages"]] == [
        "event",
        "file",
        "file",
        "file",
        "file",
        "file",
        "file",
        "file",
    ]

    status = client.get("/api/pages/status")
    assert status.status_code == 200
    body = status.json()
    assert LEGACY_KEYS <= set(body)
    assert body["page"] == "progress"
    assert body["frame_version"] is None  # Status must not render.
    assert body["pages"][1] == {"id": "memo", "title": "备忘录", "kind": "file", "revision": 1}


def test_memo_defaults_save_and_stale_revision(client):
    default = client.get("/api/pages/memo")
    assert default.status_code == 200
    assert default.json()["revision"] == 1
    assert default.json()["data"] == {"items": []}

    saved = save(client, "memo", memo_data("买牛奶", "交报告"))
    assert saved.status_code == 200
    assert saved.json()["revision"] == 2
    assert saved.json()["updated_at"]
    assert saved.json()["data"]["items"][0]["text"] == "买牛奶"

    reloaded = client.get("/api/pages/memo").json()
    assert reloaded == saved.json()

    stale = save(client, "memo", memo_data("迟到的修改"))
    assert stale.status_code == 409
    assert stale.json()["revision"] == 2
    assert stale.json()["data"]["items"][0]["text"] == "买牛奶"


@pytest.mark.parametrize("page,data", [
    ("memo", {"items": [{"id": f"i{index}", "text": "x"} for index in range(9)]}),
    ("memo", {"items": [{"id": "a", "text": "文" * 60}]}),
    ("memo", {"items": [{"id": "a", "text": "ok", "due": "2026-02-30 10:00"}]}),
    ("course", {"total_weeks": 18, "courses": [], "overrides": []}),
    ("course", {"semester_start": "not-a-date", "total_weeks": 18, "courses": [], "overrides": []}),
])
def test_invalid_or_unrenderable_documents_are_rejected(client, page, data):
    response = save(client, page, data)
    assert response.status_code == 422
    assert client.get(f"/api/pages/{page}").json()["revision"] == 1


def test_course_duplicate_slot_is_rejected_at_write_time(client):
    nine_monday = [
        {"id": f"m{index}", "name": "课", "weekday": 1, "weeks": [1],
         "period": 1, "room": "A-1"}
        for index in range(9)
    ]
    data = {**course_data(), "courses": nine_monday}
    assert save(client, "course", data).status_code == 422
    assert client.get("/api/pages/course").json()["revision"] == 1

    spread = [
        {**row, "weekday": index + 1}
        for index, row in enumerate(nine_monday[:7])
    ]
    assert save(client, "course", {**course_data(), "courses": spread}).status_code == 200


def test_course_added_class_round_trips(client):
    data = {
        **course_data(),
        "overrides": [
            {"date": "2026-11-08", "course_id": "extra-1", "action": "add",
             "name": "临时讲座", "period": 3, "room": "报告厅"},
        ],
    }
    saved = save(client, "course", data)
    assert saved.status_code == 200
    assert saved.json()["data"]["overrides"][0]["action"] == "add"
    preview = client.post("/api/pages/course/preview", json=data)
    assert preview.status_code == 200
    assert preview.headers["x-frame-bytes"] == "15000"


def test_progress_is_not_an_editable_page(client):
    assert client.get("/api/pages/progress").status_code == 404
    assert client.put("/api/pages/progress", json={"revision": 1, "data": {}}).status_code == 404
    assert client.post("/api/pages/progress/preview", json={}).status_code == 404
    assert client.get("/api/pages/unknown").status_code == 404
    assert client.post("/api/pages/unknown/select").status_code == 404


def test_select_memo_serves_15000_byte_frame_and_304(client):
    saved = save(client, "memo", memo_data("买牛奶"))
    assert saved.status_code == 200
    selected = client.post("/api/pages/memo/select")
    assert selected.status_code == 200
    assert selected.json()["page"] == "memo"
    assert selected.json()["publish_id"] == "memo-r2"
    assert selected.json()["frame_version"] is None

    frame = client.get("/api/panels/progress/frame")
    assert frame.status_code == 200
    assert len(frame.content) == 15000
    assert frame.headers["x-frame-format"] == FRAME_FORMAT
    etag = '"' + hashlib.sha256(frame.content).hexdigest() + '"'
    assert frame.headers["etag"] == etag
    assert client.get("/api/panels/progress/frame", headers={"If-None-Match": etag}).status_code == 304

    legacy = client.get("/api/panels/progress/status").json()
    assert set(legacy) == LEGACY_KEYS  # The legacy route stays Progress-only.
    assert legacy["source"] == "lan" and legacy["frame_version"] is None

    aware = client.get("/api/pages/status").json()
    assert aware["page"] == "memo"
    assert aware["frame_version"] == etag[1:-1]
    assert aware["host_stage"] == "FRAME_READY"


def test_preview_matches_the_served_frame_and_has_no_side_effect(client):
    assert save(client, "memo", memo_data("买牛奶")).status_code == 200
    assert client.post("/api/pages/memo/select").status_code == 200
    document = client.get("/api/pages/memo").json()

    preview = client.post("/api/pages/memo/preview", json=document["data"])
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/png"
    assert preview.headers["x-frame-bytes"] == "15000"
    assert preview.headers["x-frame-format"] == FRAME_FORMAT
    version = preview.headers["x-frame-version"]
    assert len(version) == 64
    assert Image.open(io.BytesIO(preview.content)).size == (400, 300)
    assert client.get("/api/pages/memo").json()["revision"] == document["revision"]

    frame = client.get("/api/panels/progress/frame")
    assert frame.headers["etag"] == f'"{version}"'


def test_course_save_preview_and_switch(client):
    saved = save(client, "course", course_data())
    assert saved.status_code == 200
    assert saved.json()["revision"] == 2
    assert client.post("/api/pages/course/select").status_code == 200
    document = client.get("/api/pages/course").json()

    preview = client.post("/api/pages/course/preview", json=document["data"])
    frame = client.get("/api/panels/progress/frame")
    assert preview.status_code == 200
    assert frame.status_code == 200 and len(frame.content) == 15000
    assert frame.headers["etag"] == f'"{preview.headers["x-frame-version"]}"'
    assert client.post("/api/pages/memo/select").json()["page"] == "memo"
    assert client.get("/api/pages/status").json()["publish_id"] == "memo-r1"


def test_device_report_follows_the_selected_file_page(client):
    save(client, "memo", memo_data("买牛奶"))
    client.post("/api/pages/memo/select")
    version = client.get("/api/panels/progress/frame").headers["etag"][1:-1]

    assert client.post("/api/panels/progress/device-report", json={
        "frame_version": "0" * 64, "firmware_version": "r6-2",
    }).status_code == 409
    for stage in [None, "DEVICE_FRAME_ACCEPTED", "DEVICE_REFRESH_FLOW_COMPLETE"]:
        assert client.post("/api/panels/progress/device-report", json={
            "frame_version": version, "firmware_version": "r6-2", "refresh_stage": stage,
        }).status_code == 200
    device = client.get("/api/pages/status").json()["device"]
    assert device["accepted_frame_version"] == version
    assert device["refresh_stage"] == "DEVICE_REFRESH_FLOW_COMPLETE"


def test_old_page_report_is_rejected_after_switching(client):
    save(client, "memo", memo_data("买牛奶"))
    client.post("/api/pages/memo/select")
    old = client.get("/api/panels/progress/frame").headers["etag"][1:-1]
    client.post("/api/pages/course/select")

    rejected = client.post("/api/panels/progress/device-report", json={
        "frame_version": old, "firmware_version": "r6-2", "refresh_stage": "DEVICE_FRAME_ACCEPTED",
    })
    assert rejected.status_code == 409


def test_progress_remains_publishable_and_device_addressable(client):
    event = {
        "event_id": "api-progress", "type": "panel.update", "panel": "progress", "source": "lan",
        "occurred_at": "2026-11-08T01:00:00Z",
        "data": {"title": "项目", "progress": 60, "current_step": "验证",
                 "status": "进行中", "updated_at": "2026-11-08 09:00"},
    }
    assert client.post("/api/events", json=event).json()["accepted"] is True
    frame = client.get("/api/panels/progress/frame")
    assert frame.status_code == 200 and len(frame.content) == 15000
    status = client.get("/api/panels/progress/status").json()
    assert set(status) == LEGACY_KEYS
    aware = client.get("/api/pages/status").json()
    assert aware["page"] == "progress" and aware["frame_version"] == frame.headers["etag"][1:-1]
