"""Atomic file-backed state for editable pages."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json

import pytest

from services.page_state import (
    MAX_DOCUMENT_BYTES,
    PageRevisionConflict,
    PageStateStore,
    PageTooLarge,
)


SHANGHAI = timezone(timedelta(hours=8))


class Clock:
    def __init__(self, value: datetime | None = None) -> None:
        self.value = value or datetime(2026, 11, 8, 9, 30, tzinfo=SHANGHAI)

    def __call__(self) -> datetime:
        return self.value


@pytest.fixture
def store(tmp_path):
    return PageStateStore(tmp_path / "pages", {"memo", "course"}, clock=Clock())


def test_missing_file_returns_default_document(store):
    document = store.load("memo")

    assert document.page == "memo"
    assert document.revision == 1
    assert document.updated_at is None
    assert document.data == {"items": []}


def test_save_increments_revision_and_records_stamp(store, tmp_path):
    document = store.save("memo", {"items": [{"id": "a", "text": "买牛奶"}]}, 1)

    assert document.revision == 2
    assert document.updated_at == "2026-11-08 09:30"
    reloaded = store.load("memo")
    assert reloaded == document
    assert (tmp_path / "pages" / "memo.json").is_file()
    assert not list((tmp_path / "pages").glob("*.tmp"))


def test_stale_revision_reports_current_document(store):
    first = store.save("memo", {"items": []}, 1)

    with pytest.raises(PageRevisionConflict) as raised:
        store.save("memo", {"items": [{"id": "a", "text": "late"}]}, 1)

    assert raised.value.current == first
    assert store.load("memo") == first


def test_corrupt_file_falls_back_to_default_without_echoing_content(store, tmp_path, caplog):
    path = tmp_path / "pages" / "memo.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"items": [secret-payload]', encoding="utf-8")

    document = store.load("memo")

    assert document.revision == 1 and document.data == {"items": []}
    assert "secret-payload" not in caplog.text
    assert "Page state reset" in caplog.text


def test_document_over_limit_is_rejected_before_writing(store, tmp_path):
    oversized = {"items": [{"text": "x" * 200} for _ in range(200)]}

    with pytest.raises(PageTooLarge):
        store.save("memo", oversized, 1)

    assert not (tmp_path / "pages" / "memo.json").exists()
    assert MAX_DOCUMENT_BYTES < len(json.dumps(oversized, ensure_ascii=False).encode())


@pytest.mark.parametrize("page_id", ["../memo", "memo/../course", "MEMO", "", "memo.json", "unknown"])
def test_unknown_or_unsafe_page_ids_are_rejected(store, page_id):
    with pytest.raises(ValueError):
        store.load(page_id)
    with pytest.raises(ValueError):
        store.save(page_id, {"items": []}, 1)


def test_selection_is_persisted_and_falls_back(store, tmp_path):
    assert store.load_selection("progress", {"progress", "memo", "course"}) == "progress"

    store.save_selection("memo", {"progress", "memo", "course"})
    assert store.load_selection("progress", {"progress", "memo", "course"}) == "memo"

    (tmp_path / "pages" / "selection.json").write_text('{"page": "deleted"}', encoding="utf-8")
    assert store.load_selection("progress", {"progress", "memo", "course"}) == "progress"

    (tmp_path / "pages" / "selection.json").write_text("not-json", encoding="utf-8")
    assert store.load_selection("progress", {"progress", "memo", "course"}) == "progress"


def test_concurrent_saves_allow_exactly_one_winner(store):
    def attempt(_):
        try:
            return store.save("memo", {"items": [{"id": "x", "text": "并发"}]}, 1)
        except PageRevisionConflict:
            return None

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(attempt, range(6)))

    winners = [result for result in results if result is not None]
    assert len(winners) == 1
    assert store.load("memo").revision == 2
