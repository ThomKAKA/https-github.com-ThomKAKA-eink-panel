from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from server.main import app


client = TestClient(app)


def event_payload(
    *,
    event_id: str,
    source: str,
    occurred_at: str = "2026-09-02T12:00:00Z",
    progress: int = 72,
) -> dict:
    return {
        "event_id": event_id,
        "type": "panel.update",
        "source": source,
        "panel": "progress",
        "occurred_at": occurred_at,
        "data": {
            "title": "CODING",
            "progress": progress,
            "status": "RUNNING",
        },
    }


def test_event_api_accepts_and_renders_progress_snapshot() -> None:
    source = "api-render"
    accepted = client.post(
        "/api/events",
        json=event_payload(event_id="api-render-001", source=source),
    )

    assert accepted.status_code == 200
    assert accepted.json()["accepted"] is True

    snapshot = client.get(f"/api/events/snapshots/progress/{source}")
    assert snapshot.status_code == 200
    assert snapshot.json()["data"]["progress"] == 72

    rendered = client.post(
        "/api/panels/progress/render?mode=normal&format=png",
        json=snapshot.json()["data"],
    )
    assert rendered.status_code == 200
    assert Image.open(BytesIO(rendered.content)).size == (400, 300)


def test_event_api_treats_duplicate_as_successful_no_op() -> None:
    payload = event_payload(event_id="api-duplicate-001", source="api-duplicate")
    assert client.post("/api/events", json=payload).status_code == 200

    duplicate = client.post("/api/events", json={**payload, "data": {"progress": 99}})

    assert duplicate.status_code == 200
    assert duplicate.json()["accepted"] is False
    assert duplicate.json()["reason"] == "duplicate"
    assert duplicate.json()["snapshot"]["data"]["progress"] == 72


def test_event_api_rejects_out_of_order_event() -> None:
    source = "api-order"
    newest = event_payload(
        event_id="api-order-new",
        source=source,
        occurred_at="2026-09-02T12:01:00Z",
        progress=81,
    )
    older = event_payload(
        event_id="api-order-old",
        source=source,
        occurred_at="2026-09-02T12:00:00Z",
        progress=20,
    )
    assert client.post("/api/events", json=newest).status_code == 200

    response = client.post("/api/events", json=older)

    assert response.status_code == 409
    assert response.json()["reason"] == "out_of_order"
    assert response.json()["snapshot"]["data"]["progress"] == 81


def test_event_api_rejects_invalid_panel_data_without_snapshot() -> None:
    source = "api-invalid-data"
    payload = event_payload(event_id="api-invalid-001", source=source)
    payload["data"] = {"title": "MISSING PROGRESS"}

    response = client.post("/api/events", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == "Panel data is incomplete or invalid"
    assert client.get(f"/api/events/snapshots/progress/{source}").status_code == 404


def test_event_api_requires_timezone_aware_timestamp() -> None:
    response = client.post(
        "/api/events",
        json=event_payload(
            event_id="api-time-001",
            source="api-time",
            occurred_at="2026-09-02T12:00:00",
        ),
    )

    assert response.status_code == 422


def test_event_api_only_accepts_panel_update_events() -> None:
    payload = event_payload(event_id="api-type-001", source="api-type")
    payload["type"] = "task.started"

    response = client.post("/api/events", json=payload)

    assert response.status_code == 422

    payload.pop("type")
    assert client.post("/api/events", json=payload).status_code == 422
