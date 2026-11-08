"""Pet interactions: each action rebases daily decay and writes one revision."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

from panels.pet import PetPageData, pet_state
from services.page_state import PageRevisionConflict, PageStateStore


SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")
ACTIONS = frozenset({"feed", "pet", "play"})
_INTERACT_LOCK = Lock()


def _payload(document) -> PetPageData:
    return PetPageData.model_validate(
        {
            **document.data,
            "revision": document.revision,
            "updated_at": document.updated_at,
        }
    )


def pet_state_view(state: PageStateStore, now: datetime) -> dict[str, Any]:
    document = state.load("pet")
    payload = _payload(document)
    day = now.astimezone(SHANGHAI).date().isoformat()
    current = pet_state(payload, day)
    return {
        "page": "pet",
        "revision": document.revision,
        "updated_at": document.updated_at,
        "day_key": day,
        "name": payload.name,
        "satiety": current.satiety,
        "mood": current.mood,
        "affinity": current.affinity,
        "level": current.level,
        "fed_today": current.fed_today,
        "satiety_label": current.satiety_label,
        "mood_label": current.mood_label,
        "last_fed": payload.last_fed,
        "last_interaction": payload.last_interaction,
    }


def interact(state: PageStateStore, action: str, now: datetime) -> dict[str, Any]:
    if action not in ACTIONS:
        raise ValueError("Invalid pet action")
    day = now.astimezone(SHANGHAI).date().isoformat()
    minute = now.astimezone(SHANGHAI).strftime("%Y-%m-%d %H:%M")
    with _INTERACT_LOCK:
        for attempt in (1, 2):
            document = state.load("pet")
            payload = _payload(document)
            current = pet_state(payload, day)
            satiety, mood, affinity = current.satiety, current.mood, current.affinity
            last_fed = payload.last_fed
            if action == "feed":
                satiety = min(100, satiety + 30)
                affinity = min(999, affinity + 2)
                last_fed = day
            elif action == "pet":
                mood = min(100, mood + 12)
                affinity = min(999, affinity + 1)
            else:
                mood = min(100, mood + 20)
                satiety = max(0, satiety - 10)
                affinity = min(999, affinity + 3)
            data = {
                "name": payload.name,
                "satiety": satiety,
                "mood": mood,
                "affinity": affinity,
                "last_fed": last_fed,
                "last_interaction": minute,
            }
            try:
                saved = state.save("pet", data, document.revision)
            except PageRevisionConflict:
                if attempt == 2:
                    raise
                continue
            return {
                "ok": True,
                "page": "pet",
                "revision": saved.revision,
                "updated_at": saved.updated_at,
                "action": action,
                "state": pet_state_view(state, now),
            }
    raise RuntimeError("unreachable")
