"""Round 2 in-process software contracts; no LAN listener or physical device."""

from datetime import datetime, timedelta, timezone
import hashlib

import pytest
from fastapi.testclient import TestClient

import server.main as server
import services.progress_frame as frames
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


def publish(client, revision=1, progress=60, **data):
    return client.post("/api/events", json={
        "event_id": f"publish-{revision}", "type": "panel.update", "source": "lan",
        "panel": "progress", "occurred_at": f"2026-10-03T01:00:{revision:02d}Z",
        "data": {"title": "项目", "current_step": "状态验证", "status": "进行中",
                 "progress": progress, "updated_at": "2026-10-03 09:00", **data},
    })


def state(client):
    response = client.get("/api/panels/progress/status")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    return response.json()


def ready(client, revision=1, progress=60):
    assert publish(client, revision, progress).json()["accepted"]
    response = client.get("/api/panels/progress/frame")
    assert response.status_code == 200
    return response.headers["etag"][1:-1]


def report(client, version, stage=None, **fields):
    return client.post("/api/panels/progress/device-report", json={
        "frame_version": version, "firmware_version": "round2-r1a-1",
        "refresh_stage": stage, **fields,
    })


def test_identity_and_real_frame_readiness(client):
    assert state(client) == {
        "publish_id": None, "frame_version": None, "host_stage": None,
        "source": "lan", "frame_format": frames.FRAME_FORMAT,
        "device": {"last_seen": None, "firmware_version": None,
                   "accepted_frame_version": None, "refresh_stage": None},
    }
    accepted = publish(client)
    assert accepted.json()["snapshot"]["event_id"] == "publish-1"
    before = state(client)
    assert before["publish_id"] == "publish-1" and before["host_stage"] == "HOST_ACCEPTED"
    assert before["frame_version"] is None  # Status reads must not trigger rendering.
    image = client.get("/api/panels/progress/frame")
    after = state(client)
    assert after["host_stage"] == "FRAME_READY"
    assert after["frame_version"] == image.headers["etag"][1:-1] == hashlib.sha256(image.content).hexdigest()
    assert publish(client).json()["reason"] == "duplicate"
    assert state(client) == after


def test_device_acceptance_then_software_completion(client):
    version = ready(client)
    assert report(client, version, "DEVICE_REFRESH_FLOW_COMPLETE").status_code == 409
    device = state(client)["device"]
    assert device["accepted_frame_version"] is None and device["refresh_stage"] is None
    start = datetime.now(timezone.utc)
    assert report(client, version, "DEVICE_FRAME_ACCEPTED").status_code == 200
    device = state(client)["device"]
    assert start <= datetime.fromisoformat(device["last_seen"]) <= datetime.now(timezone.utc)
    assert device["firmware_version"] == "round2-r1a-1"
    assert device["accepted_frame_version"] == version
    assert device["refresh_stage"] == "DEVICE_FRAME_ACCEPTED"
    assert report(client, version, "DEVICE_REFRESH_FLOW_COMPLETE").status_code == 200
    assert state(client)["device"]["refresh_stage"] == "DEVICE_REFRESH_FLOW_COMPLETE"
    assert report(client, version, "DEVICE_FRAME_ACCEPTED").status_code == 200
    assert state(client)["device"]["refresh_stage"] == "DEVICE_REFRESH_FLOW_COMPLETE"


@pytest.mark.parametrize("initial_stage", [None, "DEVICE_FRAME_ACCEPTED", "DEVICE_REFRESH_FLOW_COMPLETE"])
def test_304_communication_cannot_manufacture_acceptance_or_completion(client, monkeypatch, initial_stage):
    version = ready(client)
    if initial_stage:
        report(client, version, "DEVICE_FRAME_ACCEPTED")
    if initial_stage == "DEVICE_REFRESH_FLOW_COMPLETE":
        report(client, version, initial_stage)
    before = state(client)["device"]
    unchanged = client.get("/api/panels/progress/frame", headers={"If-None-Match": f'"{version}"'})
    assert unchanged.status_code == 304 and unchanged.content == b""
    assert state(client)["device"] == before  # GET alone is not a device acknowledgement.
    instant = datetime.now(timezone.utc) + timedelta(seconds=1)
    class HostClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant
    monkeypatch.setattr(frames, "datetime", HostClock)
    assert report(client, version).status_code == 200  # Firmware's communication-only POST.
    after = state(client)["device"]
    assert after["last_seen"] == instant.isoformat()
    assert after["accepted_frame_version"] == before["accepted_frame_version"]
    assert after["refresh_stage"] == before["refresh_stage"] == initial_stage


def test_communication_only_report_accepts_the_served_frame(client):
    version = ready(client)
    assert server.frame_publisher.report(frames.DeviceReport(
        frame_version=version, firmware_version="round2-r6-2")) is True
    device = state(client)["device"]
    assert device["last_seen"] is not None
    assert device["firmware_version"] == "round2-r6-2"
    assert device["accepted_frame_version"] is None and device["refresh_stage"] is None


def test_communication_only_report_rejects_unknown_frame_but_still_records_contact(client):
    stale = ready(client)
    served = ready(client, 2, 61)
    assert stale != served
    start = datetime.now(timezone.utc)
    for rejected in [stale, "0" * 64]:
        assert server.frame_publisher.report(frames.DeviceReport(
            frame_version=rejected, firmware_version="round2-r6-2")) is False
        device = state(client)["device"]
        assert start <= datetime.fromisoformat(device["last_seen"]) <= datetime.now(timezone.utc)
        assert device["firmware_version"] == "round2-r6-2"
        assert device["accepted_frame_version"] is None and device["refresh_stage"] is None
    assert report(client, stale).status_code == 409  # The device-facing result of False.


@pytest.mark.parametrize("stage", ["DEVICE_FRAME_ACCEPTED", "DEVICE_REFRESH_FLOW_COMPLETE"])
def test_unknown_or_stale_frame_reports_do_not_replace_newer_frame(client, stage):
    old = ready(client)
    report(client, old, "DEVICE_FRAME_ACCEPTED")
    report(client, old, "DEVICE_REFRESH_FLOW_COMPLETE")
    new = ready(client, 2, 61)
    assert old != new
    assert report(client, new, "DEVICE_REFRESH_FLOW_COMPLETE").status_code == 409
    report(client, new, "DEVICE_FRAME_ACCEPTED")
    current = state(client)["device"]
    for rejected in [old, "0" * 64]:
        assert report(client, rejected, stage).status_code == 409
        after = state(client)["device"]
        assert after["accepted_frame_version"] == current["accepted_frame_version"] == new
        assert after["refresh_stage"] == current["refresh_stage"] == "DEVICE_FRAME_ACCEPTED"


def test_rejected_new_host_render_preserves_old_frame_without_claiming_new_ready(client):
    old = ready(client)
    report(client, old, "DEVICE_FRAME_ACCEPTED")
    report(client, old, "DEVICE_REFRESH_FLOW_COMPLETE")
    before = state(client)["device"]
    assert publish(client, 2, updated_at="invalid-date").json()["accepted"]
    still_old = client.get("/api/panels/progress/frame")
    assert still_old.headers["etag"][1:-1] == old
    current = state(client)
    assert current["publish_id"] == "publish-2" and current["host_stage"] == "HOST_ACCEPTED"
    assert current["frame_version"] is None
    assert current["device"] == before


def test_new_publish_with_same_pixels_keeps_existing_frame_identity(client):
    version = ready(client)
    report(client, version, "DEVICE_FRAME_ACCEPTED")
    report(client, version, "DEVICE_REFRESH_FLOW_COMPLETE")
    before = state(client)["device"]
    assert publish(client, 2).json()["accepted"]
    unchanged = client.get("/api/panels/progress/frame", headers={"If-None-Match": f'"{version}"'})
    assert unchanged.status_code == 304
    current = state(client)
    assert current["publish_id"] == "publish-2" and current["frame_version"] == version
    assert current["host_stage"] == "FRAME_READY" and current["device"] == before


@pytest.mark.parametrize("fields", [
    {"frame_version": "truncated"}, {"frame_version": "A" * 64},
    {"refresh_stage": "PHYSICAL_DISPLAY_SUCCESS"}, {"refresh_stage": "SCREEN_UPDATED"},
    {"refresh_stage": "DISPLAY_CONFIRMED"}, {"last_seen": "2026-10-03T00:00:00Z"},
])
def test_report_schema_rejection_does_not_mutate_device_state(client, fields):
    version = ready(client)
    report(client, version, "DEVICE_FRAME_ACCEPTED")
    before = state(client)["device"]
    assert report(client, version, **fields).status_code == 422
    assert state(client)["device"] == before


def test_restart_and_source_isolation(client, monkeypatch):
    version = ready(client)
    report(client, version, "DEVICE_FRAME_ACCEPTED")
    other = publish(client, 2).json()["snapshot"]
    other.update(event_id="another-source", source="other", occurred_at="2026-10-03T02:00:00Z")
    other.pop("received_at")
    assert client.post("/api/events", json=other).json()["accepted"]
    assert state(client)["publish_id"] == "publish-2"
    monkeypatch.setattr(server, "frame_publisher", ProgressFramePublisher(EventStateStore(), "lan"))
    reset = state(client)
    assert reset["publish_id"] is None and reset["device"]["accepted_frame_version"] is None
    assert report(client, version, "DEVICE_FRAME_ACCEPTED").status_code == 409
