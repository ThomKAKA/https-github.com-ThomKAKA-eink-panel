"""In-process STEP017B contracts; no listening server or device access."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
import hashlib
from threading import Event

import pytest
from fastapi.testclient import TestClient

import server.main as server
from panels.base import DisplayConfig
from panels.progress import ProgressPanel
from services.event_store import EventStateStore, PanelUpdateEvent
from services.progress_frame import (
    CACHE_CONTROL, FRAME_FORMAT, ProgressFramePublisher, PublishedFrame,
    condition_matches, map_snapshot, page_timestamp, parse_if_none_match, render_transport,
)


def ingest(store, revision=1, *, source="lan", data=None):
    payload = {
        "title": "电子纸项目", "progress": 60, "current_step": "页面验证",
        "status": "进行中", "description": "离线进度页面示例", "tags": ["离线", "示例"],
        "updated_at": "2026-09-13 14:30",
    }
    if data is not None:
        payload.update(data)
    return store.ingest(PanelUpdateEvent(
        event_id=f"event-{revision}", type="panel.update", panel="progress", source=source,
        occurred_at=f"2026-09-13T06:30:{revision:02d}Z", data=payload,
    )).snapshot


@pytest.fixture
def store():
    return EventStateStore()


@pytest.fixture
def client(monkeypatch, store):
    monkeypatch.setattr(server, "event_store", store)
    monkeypatch.setattr(server, "frame_publisher", ProgressFramePublisher(store, "lan"))
    with TestClient(server.app) as result:
        yield result


@pytest.mark.parametrize("source", [None, "", " ", "bad/source", "bad source", "x" * 65, "中文"])
def test_invalid_config_no_fallback(store, source, caplog):
    ingest(store)
    assert ProgressFramePublisher(store, source).current() is None
    assert "configuration missing or invalid" in caplog.text


def test_source_isolation_and_missing_snapshot(store):
    publisher = ProgressFramePublisher(store, "lan", renderer=lambda s: b"\x11" * 15000)
    assert publisher.current() is None
    ingest(store, source="other")
    assert publisher.current() is None
    ingest(store)
    accepted = publisher.current()
    ingest(store, 2, source="other")
    assert publisher.current() is accepted


@pytest.mark.parametrize("value,expected", [
    ("2026-09-13 14:30", "2026-09-13 14:30"),
    ("2026-09-13T06:30:59Z", "2026-09-13 14:30"),
    ("2026-09-13T14:30:00+08:00", "2026-09-13 14:30"),
    ("2026-09-13T23:30:00-02:00", "2026-09-14 09:30"),
    ("2024-02-29T06:30:00.123Z", "2024-02-29 14:30"),
])
def test_timestamp(value, expected):
    assert page_timestamp(value) == expected


@pytest.mark.parametrize("value", [True, 42, "", "now", "2026-02-29 12:00",
                                      "2026-09-13T14:30:00", "2026-09-13T14:30:00+08:99",
                                      "2026-09-13 25:00", "2026-9-13 14:30"])
def test_invalid_timestamp(value):
    with pytest.raises(ValueError):
        page_timestamp(value)


@pytest.mark.parametrize("value", [None, "", "   "])
def test_snapshot_fallback_is_event_time_not_now(store, value):
    snapshot = ingest(store, data={"updated_at": value})
    mapped = map_snapshot(snapshot)
    assert mapped["updated_at"] == "2026-09-13 14:30"
    assert mapped["title"] == "电子纸项目"
    assert mapped["current_step"] == "页面验证"
    assert mapped["source"] == "lan"
    assert snapshot.data["updated_at"] == value


def test_missing_time_key(store):
    snapshot = ingest(store)
    data = dict(snapshot.data)
    del data["updated_at"]
    assert map_snapshot(replace(snapshot, data=data))["updated_at"] == "2026-09-13 14:30"


def test_real_render_pixel_mapping_and_chinese(store):
    snapshot = ingest(store)
    frame = render_transport(snapshot)
    image = ProgressPanel(clock=lambda: pytest.fail("time fallback")).render(
        map_snapshot(snapshot), DisplayConfig(), "eink", strict=True)
    assert image.size == (400, 300) and image.mode == "1"
    assert len(frame) == 15000
    # Independent per-pixel decode, not the production row reversal function.
    for y in range(300):
        for x in range(400):
            bit = bool(frame[y * 50 + x // 8] & (0x80 >> (x % 8)))
            assert bit == bool(image.getpixel((x, 299 - y)))
    texts = [entry["text"] for entry in image.info["render_audit"]["texts"]]
    assert "电子纸项目" in texts and "页面验证" in texts and "进行中" in texts
    assert render_transport(snapshot) == frame


@pytest.mark.parametrize("status", ["WAITING DATA", "UPDATE FAILED"])
def test_reserved_error_pages_rejected(store, status):
    snapshot = ingest(store, data={"status": status})
    with pytest.raises(ValueError):
        render_transport(snapshot)


def test_waiting_and_long_text_rejected(store):
    snapshot = ingest(store)
    with pytest.raises(ValueError):
        render_transport(replace(snapshot, data={"updated_at": "2026-09-13 14:30"}))
    with pytest.raises(ValueError):
        render_transport(replace(snapshot, data={**snapshot.data, "current_step": "超长步骤" * 50}))


def test_cached_version_identical_content_and_changed_content(store):
    calls = []
    def renderer(snapshot):
        calls.append(snapshot.event_id)
        return bytes([snapshot.data["progress"]]) * 15000
    publisher = ProgressFramePublisher(store, "lan", renderer=renderer)
    ingest(store)
    first = publisher.current()
    assert publisher.current() is first
    ingest(store, 2)
    second = publisher.current()
    assert first.etag == second.etag and second.version != first.version
    ingest(store, 3, data={"progress": 61})
    assert publisher.current().etag != second.etag
    assert calls == ["event-1", "event-2", "event-3"]
    with pytest.raises(FrozenInstanceError):
        first.body = b"bad"


@pytest.mark.parametrize("invalid", [b"", b"x" * 14999, b"x" * 15001, bytearray(15000), None])
def test_invalid_candidate_preserves_publication(store, invalid):
    publisher = ProgressFramePublisher(store, "lan", renderer=lambda s: b"x" * 15000)
    ingest(store)
    first = publisher.current()
    publisher._renderer = lambda s: invalid
    ingest(store, 2)
    assert publisher.current() is first


def test_exception_preserves_old_and_no_record_on_first_failure(store):
    def fail(snapshot):
        raise ValueError("private payload must not be logged")
    ingest(store)
    publisher = ProgressFramePublisher(store, "lan", renderer=fail)
    assert publisher.current() is None
    publisher._renderer = lambda s: b"x" * 15000
    first = publisher.current()
    ingest(store, 2)
    publisher._renderer = fail
    assert publisher.current() is first


def test_stale_render_discarded_without_chasing(store):
    entered, release = Event(), Event()
    calls = []
    def renderer(snapshot):
        calls.append(snapshot.event_id)
        if snapshot.event_id == "event-2":
            entered.set()
            assert release.wait(5)
        return bytes([int(snapshot.event_id[-1])]) * 15000
    publisher = ProgressFramePublisher(store, "lan", renderer=renderer)
    ingest(store)
    original = publisher.current()
    ingest(store, 2)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(publisher.current)
        try:
            assert entered.wait(5)
            ingest(store, 3)
        finally:
            release.set()
        assert pending.result(timeout=5) is original
    assert calls == ["event-1", "event-2"]
    current = publisher.current()
    assert current.body == b"\x03" * 15000
    assert current.etag == '"' + hashlib.sha256(current.body).hexdigest() + '"'


def test_parallel_requests_render_once(store):
    calls = []
    def renderer(snapshot):
        calls.append(snapshot)
        return b"x" * 15000
    ingest(store)
    publisher = ProgressFramePublisher(store, "lan", renderer=renderer)
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(lambda _: publisher.current(), range(12)))
    assert len(calls) == 1 and all(r is records[0] for r in records)


def test_store_atomic_callback_and_restart(store):
    snapshot = ingest(store)
    calls = []
    assert store._if_current(snapshot, lambda: calls.append("published"))
    ingest(store, 2)
    assert not store._if_current(snapshot, lambda: calls.append("stale"))
    assert calls == ["published"]
    assert ProgressFramePublisher(EventStateStore(), "lan").current() is None


def test_http_200_and_304(client, store):
    ingest(store)
    response = client.get("/api/panels/progress/frame")
    assert response.status_code == 200 and len(response.content) == 15000
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-length"] == "15000"
    assert response.headers["x-frame-format"] == FRAME_FORMAT
    assert response.headers["cache-control"] == CACHE_CONTROL
    assert "content-encoding" not in response.headers and "transfer-encoding" not in response.headers
    etag = '"' + hashlib.sha256(response.content).hexdigest() + '"'
    assert response.headers["etag"] == etag
    for condition in [etag, "W/" + etag, '"other", W/' + etag, "*", ", " + etag + ","]:
        unchanged = client.get("/api/panels/progress/frame", headers={"If-None-Match": condition})
        assert unchanged.status_code == 304 and unchanged.content == b""
        assert "content-length" not in unchanged.headers
        assert unchanged.headers["etag"] == etag
        assert unchanged.headers["x-frame-format"] == FRAME_FORMAT
        assert unchanged.headers["cache-control"] == CACHE_CONTROL
    assert client.get("/api/panels/progress/frame", headers={"If-None-Match": '"*"'}).status_code == 200
    assert client.get("/api/panels/progress/frame", headers=[("If-None-Match", '"other"'), ("If-None-Match", etag)]).status_code == 304


@pytest.mark.parametrize("header", ["", "garbage", "W/unquoted", '"abc', '"a" "b"', '*, "a"', 'w/"x"'])
def test_malformed_header_400(client, header):
    assert client.get("/api/panels/progress/frame", headers={"If-None-Match": header}).status_code == 400


def test_no_frame_503_and_other_routes_work(client):
    response = client.get("/api/panels/progress/frame", headers={"If-None-Match": "*"})
    assert response.status_code == 503
    assert "etag" not in response.headers and "x-frame-format" not in response.headers
    assert client.get("/api/samples/progress").status_code == 200


def test_invalid_config_route_503(client, monkeypatch, store):
    monkeypatch.setattr(server, "frame_publisher", ProgressFramePublisher(store, None))
    ingest(store)
    assert client.get("/api/panels/progress/frame").status_code == 503
    assert client.get("/api/events/snapshots/progress/lan").status_code == 200


def test_failed_new_snapshot_still_delivers_old_200_304(client, store):
    ingest(store)
    first = client.get("/api/panels/progress/frame")
    ingest(store, 2, data={"updated_at": "not-a-date"})
    old = client.get("/api/panels/progress/frame")
    assert old.status_code == 200 and old.content == first.content
    assert old.headers["etag"] == first.headers["etag"]
    assert client.get("/api/panels/progress/frame", headers={"If-None-Match": first.headers["etag"]}).status_code == 304


def test_existing_post_to_frame_end_to_end(client):
    event = {"event_id": "e2e", "type": "panel.update", "panel": "progress", "source": "lan",
             "occurred_at": "2026-09-13T06:30:00Z", "data": {"title": "项目", "current_step": "验证", "status": "进行中", "progress": 60}}
    accepted = client.post("/api/events", json=event)
    assert accepted.status_code == 200 and accepted.json()["accepted"]
    assert client.get("/api/panels/progress/frame").status_code == 200
    duplicate = client.post("/api/events", json=event)
    assert duplicate.json()["reason"] == "duplicate"


def test_tag_parser_does_not_confuse_quoted_comma_or_star(store):
    snapshot = ingest(store)
    frame = PublishedFrame.create(bytes(15000), snapshot)
    assert parse_if_none_match('"a,b", W/"c"') == ("a,b", "c")
    assert not condition_matches(parse_if_none_match('"*"'), frame)
    assert condition_matches(parse_if_none_match("*"), frame)
    assert not condition_matches(None, frame)
