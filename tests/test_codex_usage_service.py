"""Host-side ingestion and stale marking for the Codex usage page."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.codex_usage import CodexUsageService
from services.page_state import PageStateStore


SHANGHAI = timezone(timedelta(hours=8))


class Clock:
    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment


class FakeThread:
    def __init__(self, *, target, name, daemon):
        self.target = target
        self.name = name
        self.daemon = daemon
        self.started = False
        self.join_timeout = None

    def start(self) -> None:
        self.started = True

    def join(self, timeout=None) -> None:
        self.join_timeout = timeout


def payload(**updates):
    data = {
        "today_tokens": 0,
        "week_tokens": 22646123,
        "total_tokens": 132173864,
        "responses": 878,
        "sessions": 6,
        "last_activity": "11-07 15:10",
        "used_percent": 0.0,
        "window_minutes": 43200,
        "resets_at": "12-07",
        "plan": "free",
        "quota_at": "11-07 15:10",
        "days": [{"date": "11-08", "tokens": 0}],
        "source": "codex-sessions",
    }
    data.update(updates)
    return data


def make(state, clock=None, **options):
    return CodexUsageService(state, clock=clock, **options)


@pytest.fixture
def clock():
    return Clock(datetime(2026, 11, 8, 15, 0, tzinfo=SHANGHAI))


@pytest.fixture
def state(tmp_path, clock):
    return PageStateStore(tmp_path / "pages", {"codex"}, clock=clock)


def test_ingest_stores_a_fresh_document(state):
    service = make(state)
    result = service.ingest(payload())

    document = state.load("codex")
    assert result == {"ok": True, "revision": 2, "stale": False, "updated_at": "2026-11-08 15:00"}
    assert document.revision == 2
    assert document.updated_at == "2026-11-08 15:00"
    assert document.data["today_tokens"] == 0
    assert document.data["stale"] is False


def test_ingest_rejects_invalid_payload_without_writing(state):
    service = make(state)
    with pytest.raises(ValueError):
        service.ingest(payload(today_tokens=-5))
    assert state.load("codex").revision == 1


def test_fresh_document_does_not_become_stale(state, clock):
    service = make(state, clock=clock)
    service.ingest(payload())

    clock.moment = datetime(2026, 11, 8, 15, 14, tzinfo=SHANGHAI)
    assert service.mark_stale_if_aged() is False
    assert state.load("codex").data["stale"] is False
    assert state.load("codex").revision == 2


def test_aged_document_is_marked_stale_exactly_once(state, clock):
    service = make(state, clock=clock)
    service.ingest(payload())

    clock.moment = datetime(2026, 11, 8, 15, 16, tzinfo=SHANGHAI)
    assert service.mark_stale_if_aged() is True
    document = state.load("codex")
    assert document.data["stale"] is True
    assert document.revision == 3

    clock.moment = datetime(2026, 11, 8, 15, 40, tzinfo=SHANGHAI)
    assert service.mark_stale_if_aged() is False
    assert state.load("codex").revision == 3


def test_empty_document_is_left_alone(state, clock):
    service = make(state, clock=clock)
    clock.moment = datetime(2026, 11, 8, 18, 0, tzinfo=SHANGHAI)
    assert service.mark_stale_if_aged() is False
    assert state.load("codex").revision == 1


def test_ingest_after_stale_recovers(state, clock):
    service = make(state, clock=clock)
    service.ingest(payload())
    clock.moment = datetime(2026, 11, 8, 15, 20, tzinfo=SHANGHAI)
    assert service.mark_stale_if_aged() is True

    result = service.ingest(payload(today_tokens=1500))
    document = state.load("codex")
    assert result["stale"] is False
    assert document.data["stale"] is False
    assert document.data["today_tokens"] == 1500
    assert document.revision == 4


def test_watchdog_thread_starts_and_closes_cleanly(state, clock):
    threads = []

    def factory(**kwargs):
        thread = FakeThread(**kwargs)
        threads.append(thread)
        return thread

    service = make(state, clock=clock, thread_factory=factory)
    service.start()
    service.start()
    assert len(threads) == 1
    assert threads[0].started is True
    assert threads[0].name == "eink-codex-watchdog"

    service.close()
    assert service._stop.is_set()
    assert threads[0].join_timeout is not None
    service.close()
