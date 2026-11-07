from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import server.main as server_main
from server.main import app
from services.event_store import EventStateStore
from services.progress_frame import FRAME_FORMAT, ProgressFramePublisher


client = TestClient(app)


def draft_event(
    *,
    event_id: str = "web-manage-001",
    source: str = "web-manage-test",
    occurred_at: str = "2026-11-07T10:00:00Z",
    data: dict | None = None,
) -> dict:
    return {
        "event_id": event_id,
        "type": "panel.update",
        "source": source,
        "panel": "progress",
        "occurred_at": occurred_at,
        "data": data
        if data is not None
        else {
            "title": "R4 WEB",
            "progress": 42,
            "current_step": "发布预览",
            "status": "RUNNING",
            "description": "管理页测试",
            "tags": ["a", "b"],
            "source": "Local Web",
        },
    }


@pytest.fixture
def isolated_progress(monkeypatch):
    store = EventStateStore()
    publisher = ProgressFramePublisher(store, "web-manage-test")
    monkeypatch.setattr(server_main, "event_store", store)
    monkeypatch.setattr(server_main, "frame_publisher", publisher)
    return store, publisher


def test_management_page_loads() -> None:
    response = client.get("/manage")

    assert response.status_code == 200
    for marker in (
        "Progress 管理",
        'id="progress-form"',
        'id="preview"',
        'id="publish"',
        'id="status-report"',
        "/static/manage.js",
    ):
        assert marker in response.text


def test_management_status_exposes_source_and_frame_format(isolated_progress) -> None:
    body = client.get("/api/panels/progress/status").json()

    assert body["source"] == "web-manage-test"
    assert body["frame_format"] == FRAME_FORMAT


def test_progress_preview_matches_published_frame(isolated_progress) -> None:
    event = draft_event()

    preview = client.post("/api/panels/progress/preview", json=event)

    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/png"
    assert preview.headers["x-frame-format"] == FRAME_FORMAT
    assert preview.headers["x-frame-bytes"] == "15000"
    version = preview.headers["x-frame-version"]
    assert len(version) == 64
    assert all(character in "0123456789abcdef" for character in version)
    image = Image.open(BytesIO(preview.content))
    assert image.size == (400, 300)

    accepted = client.post("/api/events", json=event)
    assert accepted.status_code == 200
    assert accepted.json()["accepted"] is True

    frame = client.get("/api/panels/progress/frame")
    assert frame.status_code == 200
    assert len(frame.content) == 15000
    assert frame.headers["etag"] == f'"{version}"'


def test_progress_preview_is_side_effect_free(isolated_progress) -> None:
    store, publisher = isolated_progress
    event = draft_event()

    response = client.post("/api/panels/progress/preview", json=event)

    assert response.status_code == 200
    assert store.get_snapshot("progress", event["source"]) is None
    assert publisher.status()["publish_id"] is None
    assert client.get("/api/panels/progress/frame").status_code == 503


def test_progress_preview_rejects_invalid_data() -> None:
    event = draft_event(data={"title": "MISSING PROGRESS"})

    response = client.post("/api/panels/progress/preview", json=event)

    assert response.status_code == 422


def test_progress_preview_rejects_malformed_event() -> None:
    event = draft_event()
    event.pop("occurred_at")

    response = client.post("/api/panels/progress/preview", json=event)

    assert response.status_code == 422


def test_simulator_links_to_management_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert 'href="/manage"' in response.text
