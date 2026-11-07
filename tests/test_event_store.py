from datetime import datetime, timezone
from threading import Barrier, Thread

import pytest

from services.event_store import (
    EventStateStore,
    InvalidPanelData,
    PanelUpdateEvent,
)


def fixed_clock() -> datetime:
    return datetime(2026, 9, 2, 12, 0, 5, tzinfo=timezone.utc)


def progress_event(
    *,
    event_id: str = "evt-001",
    source: str = "codex",
    occurred_at: str = "2026-09-02T12:00:00Z",
    progress: int = 72,
) -> PanelUpdateEvent:
    return PanelUpdateEvent.model_validate(
        {
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
    )


def test_valid_event_creates_snapshot() -> None:
    store = EventStateStore(clock=fixed_clock)

    outcome = store.ingest(progress_event())
    snapshot = store.get_snapshot("progress", "codex")

    assert outcome.accepted is True
    assert outcome.reason == "accepted"
    assert snapshot is not None
    assert snapshot.event_id == "evt-001"
    assert snapshot.data["progress"] == 72
    assert snapshot.data["source"] == "codex"
    assert snapshot.data["updated_at"] == "2026-09-02T12:00:00+00:00"
    assert snapshot.received_at == "2026-09-02T12:00:05+00:00"


def test_later_event_replaces_snapshot() -> None:
    store = EventStateStore(clock=fixed_clock)
    store.ingest(progress_event())

    outcome = store.ingest(
        progress_event(
            event_id="evt-002",
            occurred_at="2026-09-02T12:00:01Z",
            progress=81,
        )
    )

    assert outcome.accepted is True
    assert outcome.snapshot.data["progress"] == 81


def test_duplicate_event_is_idempotent() -> None:
    store = EventStateStore(clock=fixed_clock)
    store.ingest(progress_event())

    duplicate = store.ingest(progress_event(progress=99))

    assert duplicate.accepted is False
    assert duplicate.reason == "duplicate"
    assert duplicate.snapshot.data["progress"] == 72


def test_older_event_does_not_replace_snapshot() -> None:
    store = EventStateStore(clock=fixed_clock)
    store.ingest(
        progress_event(
            event_id="evt-new",
            occurred_at="2026-09-02T12:01:00Z",
            progress=81,
        )
    )

    older = store.ingest(
        progress_event(
            event_id="evt-old",
            occurred_at="2026-09-02T12:00:00Z",
            progress=20,
        )
    )

    assert older.accepted is False
    assert older.reason == "out_of_order"
    assert older.snapshot.data["progress"] == 81


def test_invalid_panel_data_does_not_replace_snapshot() -> None:
    store = EventStateStore(clock=fixed_clock)
    store.ingest(progress_event())
    invalid = progress_event().model_copy(update={"data": {"title": "MISSING"}})

    with pytest.raises(InvalidPanelData, match="incomplete or invalid"):
        store.ingest(invalid)

    assert store.get_snapshot("progress", "codex").data["progress"] == 72


def test_sources_have_independent_snapshots() -> None:
    store = EventStateStore(clock=fixed_clock)

    store.ingest(progress_event(source="codex", progress=72))
    store.ingest(progress_event(source="build-agent", progress=40))

    assert store.get_snapshot("progress", "codex").data["progress"] == 72
    assert store.get_snapshot("progress", "build-agent").data["progress"] == 40


def test_new_store_starts_without_snapshots() -> None:
    first_process = EventStateStore(clock=fixed_clock)
    first_process.ingest(progress_event())

    restarted_process = EventStateStore(clock=fixed_clock)

    assert restarted_process.get_snapshot("progress", "codex") is None


def test_concurrent_events_keep_the_newest_snapshot() -> None:
    store = EventStateStore(clock=fixed_clock)
    start = Barrier(2)
    events = [
        progress_event(
            event_id="evt-old",
            occurred_at="2026-09-02T12:00:00Z",
            progress=20,
        ),
        progress_event(
            event_id="evt-new",
            occurred_at="2026-09-02T12:01:00Z",
            progress=81,
        ),
    ]

    def ingest(event: PanelUpdateEvent) -> None:
        start.wait(2)
        store.ingest(event)

    threads = [Thread(target=ingest, args=(event,)) for event in events]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(2)

    assert all(thread.is_alive() is False for thread in threads)
    assert store.get_snapshot("progress", "codex").data["progress"] == 81
