import hashlib
import json

import pytest
from fastapi.testclient import TestClient

import server.main as server
from services.event_store import EventStateStore
from services.firmware_offer import FirmwareOffer
from services.progress_frame import ProgressFramePublisher

BODY = b"\xE9" + b"x" * 32
SHA = hashlib.sha256(BODY).hexdigest()


@pytest.fixture
def firmware_client(monkeypatch, tmp_path):
    image = tmp_path / "firmware.bin"
    image.write_bytes(BODY)
    config = tmp_path / "firmware.json"
    config.write_text(json.dumps({"path": str(image), "version": "round2-r6-2"}))
    offer = FirmwareOffer(config, tmp_path)
    monkeypatch.setattr(server, "firmware_offer", offer)
    return TestClient(server.app), offer


@pytest.fixture
def publication_client(monkeypatch, tmp_path):
    image = tmp_path / "firmware.bin"
    image.write_bytes(BODY)
    config = tmp_path / "firmware.json"
    config.write_text(json.dumps({"path": str(image), "version": "round2-r6-2"}))
    offer = FirmwareOffer(config, tmp_path)
    store = EventStateStore()
    publisher = ProgressFramePublisher(store, "lan")
    monkeypatch.setattr(server, "firmware_offer", offer)
    monkeypatch.setattr(server, "event_store", store)
    monkeypatch.setattr(server, "frame_publisher", publisher)
    return TestClient(server.app), offer


def publish_and_ready(client):
    accepted = client.post("/api/events", json={
        "event_id": "ota-1", "type": "panel.update", "source": "lan",
        "panel": "progress", "occurred_at": "2026-11-07T10:00:00Z",
        "data": {"title": "OTA", "progress": 72, "current_step": "升级",
                 "status": "RUNNING", "description": "固件", "tags": ["a", "b"]},
    })
    assert accepted.json()["accepted"] is True
    frame = client.get("/api/panels/progress/frame")
    assert frame.status_code == 200
    return frame.headers["etag"][1:-1]


def test_firmware_status_has_no_path_or_credentials(firmware_client, tmp_path):
    client, _ = firmware_client
    response = client.get("/api/device/firmware/status")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body == {
        "configured": True, "armed": False, "version": "round2-r6-2",
        "size": len(BODY), "sha256": SHA, "expires_at": None,
        "served_at": None, "device_version": None,
    }
    assert str(tmp_path) not in response.text


def test_manifest_bodies_are_exact(firmware_client):
    client, _ = firmware_client
    response = client.get("/api/device/firmware/manifest")
    assert response.status_code == 200
    assert response.text == '{"armed":false}'
    assert client.post("/api/device/firmware/arm").status_code == 200
    response = client.get("/api/device/firmware/manifest")
    assert response.text == (
        '{"armed":true,"version":"round2-r6-2","size":33,'
        f'"sha256":"{SHA}"}}'
    )


def test_image_is_one_shot_and_matches_manifest(firmware_client):
    client, _ = firmware_client
    assert client.post("/api/device/firmware/arm").status_code == 200
    response = client.get("/api/device/firmware/image")
    assert response.status_code == 200
    assert response.content == BODY
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-length"] == str(len(BODY))
    assert response.headers["x-firmware-version"] == "round2-r6-2"
    assert response.headers["x-firmware-sha256"] == SHA
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/api/device/firmware/image").status_code == 409
    assert client.get("/api/device/firmware/manifest").text == '{"armed":false}'


def test_disarm_and_unconfigured_responses(firmware_client, monkeypatch, tmp_path):
    client, _ = firmware_client
    assert client.post("/api/device/firmware/arm").status_code == 200
    assert client.post("/api/device/firmware/disarm").status_code == 200
    assert client.get("/api/device/firmware/image").status_code == 409

    missing = FirmwareOffer(tmp_path / "missing.json", tmp_path)
    monkeypatch.setattr(server, "firmware_offer", missing)
    assert client.get("/api/device/firmware/manifest").status_code == 503
    assert client.get("/api/device/firmware/image").status_code == 503
    assert client.post("/api/device/firmware/arm").status_code == 503
    assert client.get("/api/device/firmware/status").json()["configured"] is False


def test_valid_device_report_disarms_on_target_version(publication_client):
    client, offer = publication_client
    version = publish_and_ready(client)
    assert client.post("/api/device/firmware/arm").status_code == 200
    rejected = client.post("/api/panels/progress/device-report", json={
        "frame_version": "f" * 64, "firmware_version": "round2-r6-2",
        "refresh_stage": None,
    })
    assert rejected.status_code == 409
    assert offer.status()["armed"] is True
    accepted = client.post("/api/panels/progress/device-report", json={
        "frame_version": version, "firmware_version": "round2-r6-2",
        "refresh_stage": None,
    })
    assert accepted.status_code == 200
    assert offer.status()["armed"] is False
    assert offer.status()["device_version"] == "round2-r6-2"
