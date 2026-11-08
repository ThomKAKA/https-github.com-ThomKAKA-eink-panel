"""Pet interactions rebase daily decay and stay revision-safe."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.page_registry import FILE_PAGES
from services.page_state import PageRevisionConflict, PageStateStore
from services.pet import ACTIONS, interact, pet_state_view


SHANGHAI = timezone(timedelta(hours=8))


def at(day: int, hour: int = 20, minute: int = 30) -> datetime:
    return datetime(2026, 11, day, hour, minute, tzinfo=SHANGHAI)


def make_store(tmp_path, now: datetime) -> PageStateStore:
    return PageStateStore(tmp_path / "pages", FILE_PAGES, clock=lambda: now)


def test_actions_are_the_three_buttons():
    assert ACTIONS == frozenset({"feed", "pet", "play"})


def test_default_state_view_reports_unfed_pet(tmp_path):
    now = at(8)
    view = pet_state_view(make_store(tmp_path, now), now)

    assert view["page"] == "pet"
    assert view["revision"] == 1
    assert view["day_key"] == "2026-11-08"
    assert (view["satiety"], view["mood"], view["affinity"]) == (50, 60, 0)
    assert view["level"] == 1
    assert view["fed_today"] is False
    assert view["satiety_label"] == "正常"
    assert view["mood_label"] == "一般"


def test_feed_adds_satiety_affinity_and_marks_the_day(tmp_path):
    now = at(8)
    store = make_store(tmp_path, now)
    result = interact(store, "feed", now)

    assert result["ok"] is True
    assert result["revision"] == 2
    assert result["updated_at"] == "2026-11-08 20:30"
    assert result["action"] == "feed"
    assert result["state"]["satiety"] == 80
    assert result["state"]["affinity"] == 2
    assert result["state"]["fed_today"] is True
    assert store.load("pet").data == {
        "name": "大肥鱼",
        "satiety": 80,
        "mood": 60,
        "affinity": 2,
        "last_fed": "2026-11-08",
        "last_interaction": "2026-11-08 20:30",
    }


def test_pet_and_play_change_mood_and_satiety(tmp_path):
    now = at(8)
    petted = interact(make_store(tmp_path / "a", now), "pet", now)
    played = interact(make_store(tmp_path / "b", now), "play", now)

    assert (petted["state"]["mood"], petted["state"]["affinity"]) == (72, 1)
    assert (played["state"]["mood"], played["state"]["satiety"], played["state"]["affinity"]) == (80, 40, 3)


def test_values_are_clamped(tmp_path):
    now = at(8)
    store = make_store(tmp_path, now)
    store.save(
        "pet",
        {"name": "大肥鱼", "satiety": 95, "mood": 95, "affinity": 998},
        1,
    )
    fed = interact(store, "feed", now)
    played = interact(store, "play", now)

    assert (fed["state"]["satiety"], fed["state"]["affinity"]) == (100, 999)
    assert (played["state"]["mood"], played["state"]["satiety"], played["state"]["affinity"]) == (100, 90, 999)


def test_a_starved_pet_is_rebased_before_the_action(tmp_path):
    first_day = at(8)
    store = make_store(tmp_path, first_day)
    store.save("pet", {"name": "大肥鱼", "satiety": 50, "mood": 60, "affinity": 0}, 1)

    later = at(11)
    store = PageStateStore(tmp_path / "pages", FILE_PAGES, clock=lambda: later)
    result = interact(store, "feed", later)

    assert result["state"]["satiety"] == 30
    assert store.load("pet").data["satiety"] == 30
    assert store.load("pet").data["last_fed"] == "2026-11-11"


def test_a_stale_revision_is_retried_once(tmp_path, monkeypatch):
    now = at(8)
    store = make_store(tmp_path, now)
    original = store.save
    calls = {"count": 0}

    def flaky(page_id, data, revision):
        calls["count"] += 1
        if calls["count"] == 1:
            raise PageRevisionConflict(store.load(page_id))
        return original(page_id, data, revision)

    monkeypatch.setattr(store, "save", flaky)
    result = interact(store, "feed", now)

    assert calls["count"] == 2
    assert result["revision"] == 2


def test_two_conflicts_are_not_swallowed(tmp_path, monkeypatch):
    now = at(8)
    store = make_store(tmp_path, now)

    def always_conflict(page_id, data, revision):
        raise PageRevisionConflict(store.load(page_id))

    monkeypatch.setattr(store, "save", always_conflict)
    with pytest.raises(PageRevisionConflict):
        interact(store, "feed", now)


def test_unknown_action_is_rejected(tmp_path):
    now = at(8)
    with pytest.raises(ValueError):
        interact(make_store(tmp_path, now), "sleep", now)
