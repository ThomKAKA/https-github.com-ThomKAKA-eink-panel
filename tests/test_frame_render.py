"""Shared render pipeline and single-device report ledger."""

from __future__ import annotations

from datetime import datetime, timezone
import io

import pytest
from PIL import Image

from panels.base import DisplayConfig
from panels.memo import MemoPanel
from panels.progress import ProgressPanel
from services.device_ledger import apply_report
from services.event_store import EventStateStore, PanelUpdateEvent
from services.frame_render import render_assets
from services.progress_frame import DeviceReport, map_snapshot, render_transport_assets


def progress_data(**updates):
    data = {
        "title": "电子纸项目",
        "progress": 60,
        "current_step": "页面验证",
        "status": "进行中",
        "description": "共享渲染",
        "tags": ["共享"],
        "updated_at": "2026-11-08 09:00",
    }
    data.update(updates)
    return data


def snapshot(**updates):
    store = EventStateStore()
    return store.ingest(PanelUpdateEvent(
        event_id="event-1", type="panel.update", panel="progress", source="lan",
        occurred_at="2026-11-08T01:00:00Z", data=progress_data(**updates),
    )).snapshot


def test_progress_render_assets_match_direct_panel_render():
    data = progress_data()
    panel = ProgressPanel()
    png, transport = render_assets(panel, data)

    image = panel.render(data, DisplayConfig(), "eink", strict=True)
    loaded = Image.open(io.BytesIO(png))
    assert loaded.size == (400, 300) and loaded.mode == "1"
    assert loaded.tobytes() == image.tobytes()
    assert len(transport) == 15000
    for y in range(300):
        for x in range(400):
            bit = bool(transport[y * 50 + x // 8] & (0x80 >> (x % 8)))
            assert bit == bool(image.getpixel((x, 299 - y)))


def test_progress_snapshot_helper_delegates_to_shared_pipeline():
    subject = snapshot()
    expected = render_assets(ProgressPanel(), map_snapshot(subject))

    assert render_transport_assets(subject) == expected


@pytest.mark.parametrize("data", [
    {},
    progress_data(status="WAITING DATA"),
    progress_data(status="UPDATE FAILED"),
])
def test_unavailable_frames_are_rejected(data):
    with pytest.raises(ValueError):
        render_assets(ProgressPanel(), data)


def test_any_panel_can_use_the_shared_pipeline():
    data = {
        "items": [{"id": "a", "text": "共享帧", "due": None, "face": "todo"}],
        "day_key": "2026-11-08",
        "revision": 2,
    }
    png, transport = render_assets(MemoPanel(), data)
    assert len(transport) == 15000
    assert Image.open(io.BytesIO(png)).size == (400, 300)


def device():
    return {
        "last_seen": None,
        "firmware_version": None,
        "accepted_frame_version": None,
        "refresh_stage": None,
        "refresh_count": None,
    }


def report(version="a" * 64, stage=None, firmware="r6-2"):
    return DeviceReport(frame_version=version, firmware_version=firmware, refresh_stage=stage)


def test_communication_only_report_records_contact_and_checks_served_frame():
    ledger = device()
    instant = datetime(2026, 11, 8, 1, 0, tzinfo=timezone.utc)

    assert apply_report(ledger, report(), '"' + "a" * 64 + '"', observed_at=instant) is True
    assert ledger["last_seen"] == instant.isoformat()
    assert ledger["firmware_version"] == "r6-2"
    assert ledger["accepted_frame_version"] is None and ledger["refresh_stage"] is None

    assert apply_report(ledger, report(version="b" * 64), '"' + "a" * 64 + '"') is False
    assert ledger["firmware_version"] == "r6-2"


def test_completion_requires_prior_acceptance_and_never_regresses():
    ledger = device()
    etag = '"' + "a" * 64 + '"'

    assert apply_report(ledger, report(stage="DEVICE_REFRESH_FLOW_COMPLETE"), etag) is False
    assert apply_report(ledger, report(stage="DEVICE_FRAME_ACCEPTED"), etag) is True
    assert ledger["refresh_stage"] == "DEVICE_FRAME_ACCEPTED"
    assert apply_report(ledger, report(stage="DEVICE_REFRESH_FLOW_COMPLETE"), etag) is True
    assert apply_report(ledger, report(stage="DEVICE_FRAME_ACCEPTED"), etag) is True
    assert ledger["refresh_stage"] == "DEVICE_REFRESH_FLOW_COMPLETE"
    assert apply_report(ledger, report(version="b" * 64, stage="DEVICE_FRAME_ACCEPTED"), etag) is False
    assert ledger["accepted_frame_version"] == "a" * 64


def test_no_served_frame_rejects_staged_reports():
    ledger = device()
    assert apply_report(ledger, report(stage="DEVICE_FRAME_ACCEPTED"), None) is False
    assert ledger["accepted_frame_version"] is None
