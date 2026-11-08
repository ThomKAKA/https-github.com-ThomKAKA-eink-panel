"""Registry and Host-side page selection/frame facade."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib

import pytest

from services.page_frames import PageFrameService
from services.page_registry import (
    DEFAULT_PAGE,
    FILE_PAGES,
    PAGE_REGISTRY,
    PageSpec,
    create_page_panel,
)
from services.page_state import PageStateStore
from services.progress_frame import FRAME_FORMAT, DeviceReport, PublishedFrame


SHANGHAI = timezone(timedelta(hours=8))


class Clock:
    def __init__(self, value: datetime | None = None) -> None:
        self.value = value or datetime(2026, 11, 8, 9, 0, tzinfo=SHANGHAI)

    def __call__(self) -> datetime:
        return self.value


class FakeProgress:
    def __init__(self) -> None:
        self.frame = None
        self.reports = []

    def current(self):
        return self.frame

    def report(self, report):
        self.reports.append(report)
        return True

    def status(self):
        return {
            "publish_id": "event-9",
            "frame_version": "f" * 64,
            "host_stage": "FRAME_READY",
            "source": "lan",
            "frame_format": FRAME_FORMAT,
            "device": {
                "last_seen": None,
                "firmware_version": None,
                "accepted_frame_version": None,
                "refresh_stage": None,
            },
        }


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def store(tmp_path, clock):
    return PageStateStore(tmp_path / "pages", FILE_PAGES, clock=clock)


@pytest.fixture
def progress():
    return FakeProgress()


@pytest.fixture
def service(store, progress, clock):
    return PageFrameService(store, lambda: progress, clock=clock)


def report(version: str, stage: str | None = None) -> DeviceReport:
    return DeviceReport(frame_version=version, firmware_version="r6-2", refresh_stage=stage)


def test_registry_is_explicit_and_factory_is_registered():
    assert DEFAULT_PAGE == "progress"
    assert FILE_PAGES == frozenset({"memo", "course", "weather", "calendar"})
    assert set(PAGE_REGISTRY) == {"progress", "memo", "course", "weather", "calendar"}
    assert PAGE_REGISTRY["memo"] == PageSpec("memo", "备忘录", "file", "memo")
    assert PAGE_REGISTRY["progress"].kind == "event"
    assert create_page_panel("course").get_metadata().panel_type == "course"
    with pytest.raises(ValueError):
        create_page_panel("unknown")


def test_default_selection_and_legacy_status(service, progress):
    assert service.current_page == "progress"
    assert service.legacy_status() == progress.status()
    assert service.status()["page"] == "progress"
    assert service.status()["pages"] == [
        {"id": "progress", "title": "Progress", "kind": "event", "revision": None},
        {"id": "memo", "title": "备忘录", "kind": "file", "revision": 1},
        {"id": "course", "title": "课程表", "kind": "file", "revision": 1},
        {"id": "weather", "title": "天气", "kind": "file", "revision": 1},
        {"id": "calendar", "title": "日历", "kind": "file", "revision": 1},
    ]


def test_file_page_renders_once_and_caches_by_revision_and_day(service):
    assert service.select_page("memo")["page"] == "memo"
    assert service.status()["frame_version"] is None  # Reading status never renders.

    first = service.current()
    assert first is not None and len(first.body) == 15000
    assert first.etag == '"' + hashlib.sha256(first.body).hexdigest() + '"'
    assert service.current() is first
    assert service.status()["frame_version"] == first.etag[1:-1]
    assert service.status()["host_stage"] == "FRAME_READY"
    assert service.status()["publish_id"] == "memo-r1"


def test_saving_invalidates_the_served_revision(service, store):
    service.select_page("memo")
    first = service.current()
    saved = store.save("memo", {"items": [{"id": "a", "text": "买牛奶"}]}, 1)

    assert saved.revision == 2
    assert service.status()["frame_version"] is None
    second = service.current()
    assert second is not None and second.etag != first.etag
    assert service.status()["publish_id"] == "memo-r2"


def test_day_change_rerenders_a_file_page(service, store, clock):
    service.select_page("memo")
    store.save("memo", {"items": [{"id": "a", "text": "交报告", "due": "2026-11-08 23:00"}]}, 1)
    today = service.current()

    clock.value = datetime(2026, 11, 9, 0, 1, tzinfo=SHANGHAI)
    tomorrow = service.current()

    assert today is not None and tomorrow is not None
    assert today.etag != tomorrow.etag


def test_selection_is_persisted_and_reloaded(store, progress, clock, tmp_path):
    service = PageFrameService(store, lambda: progress, clock=clock)
    service.select_page("course")

    assert store.load_selection("progress", {"progress", "memo", "course"}) == "course"
    restored = PageFrameService(store, lambda: progress, clock=clock)
    assert restored.current_page == "course"
    assert (tmp_path / "pages" / "selection.json").is_file()
    with pytest.raises(ValueError):
        service.select_page("unknown")


def test_progress_page_delegates_current_report_and_legacy_status(service, progress):
    frame = PublishedFrame(b"t" * 15000, '"' + "a" * 64 + '"', ("lan", "event-9", "2026-11-08T01:00:00Z"))
    progress.frame = frame

    assert service.current() is frame
    assert service.report(report("a" * 64, "DEVICE_FRAME_ACCEPTED")) is True
    assert progress.reports[-1].frame_version == "a" * 64
    assert service.legacy_status() == progress.status()
    assert service.status()["page"] == "progress"
    assert service.status()["device"] == progress.status()["device"]


def test_file_page_reports_follow_the_served_frame(service):
    service.select_page("memo")
    frame = service.current()
    assert frame is not None

    assert service.report(report("b" * 64)) is False
    assert service.report(report(frame.etag[1:-1])) is True
    assert service.report(report(frame.etag[1:-1], "DEVICE_FRAME_ACCEPTED")) is True
    assert service.report(report(frame.etag[1:-1], "DEVICE_REFRESH_FLOW_COMPLETE")) is True
    device = service.status()["device"]
    assert device["accepted_frame_version"] == frame.etag[1:-1]
    assert device["refresh_stage"] == "DEVICE_REFRESH_FLOW_COMPLETE"
    assert device["firmware_version"] == "r6-2"


def test_switching_pages_drops_the_old_served_frame(service):
    service.select_page("memo")
    old = service.current()
    assert old is not None
    service.select_page("course")

    assert service.report(report(old.etag[1:-1])) is False
    assert service.status()["frame_version"] is None
    assert service.status()["publish_id"] == "course-r1"


def test_switching_pages_clears_acceptance_but_not_contact(service):
    service.select_page("memo")
    frame = service.current()
    assert frame is not None
    service.report(report(frame.etag[1:-1], "DEVICE_FRAME_ACCEPTED"))
    service.report(report(frame.etag[1:-1], "DEVICE_REFRESH_FLOW_COMPLETE"))
    assert service.status()["device"]["refresh_stage"] == "DEVICE_REFRESH_FLOW_COMPLETE"

    service.select_page("course")
    device = service.status()["device"]
    assert device["accepted_frame_version"] is None
    assert device["refresh_stage"] is None
    assert device["firmware_version"] == "r6-2"
    assert device["last_seen"] is not None


def test_render_failure_keeps_the_previous_frame(service, store, progress, clock, tmp_path):
    service.select_page("memo")
    first = service.current()
    assert first is not None

    service._renderer = lambda panel, data: (_ for _ in ()).throw(ValueError("private payload"))
    store.save("memo", {"items": [{"id": "a", "text": "新内容"}]}, 1)

    assert service.current() is first
    assert service.status()["frame_version"] is None
    assert service.report(report(first.etag[1:-1])) is True


def test_status_does_not_render_and_reports_are_isolated_from_progress(service, progress):
    service.select_page("memo")
    before = service.status()

    assert before["publish_id"] == "memo-r1" and before["frame_version"] is None
    assert before["source"] == "memo" and before["frame_format"] == FRAME_FORMAT
    assert progress.reports == []
