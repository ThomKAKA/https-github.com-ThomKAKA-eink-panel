"""Receive takeout orders with a forward-only status contract."""

from __future__ import annotations

from threading import Lock
from typing import Any, Mapping

from panels.takeout import TakeoutOrder
from services.page_state import PageRevisionConflict, PageStateStore


ORDER_LIMIT = 6
TRANSITIONS = {
    "waiting": frozenset({"waiting", "delivering", "arrived"}),
    "delivering": frozenset({"delivering", "arrived"}),
    "arrived": frozenset({"arrived"}),
}
_RECEIVE_LOCK = Lock()


def receive_order(state: PageStateStore, payload: Mapping[str, Any]) -> dict:
    """Upsert one order; the status only moves forward (waiting -> delivering -> arrived)."""
    order = TakeoutOrder.model_validate(dict(payload))
    with _RECEIVE_LOCK:
        for attempt in (1, 2):
            document = state.load("takeout")
            existing = [
                TakeoutOrder.model_validate(item)
                for item in document.data.get("orders", [])
            ]
            current = next((item for item in existing if item.id == order.id), None)
            if current is not None and order.status not in TRANSITIONS[current.status]:
                raise ValueError("Invalid takeout status transition")
            if current is None and len(existing) >= ORDER_LIMIT:
                raise ValueError("Takeout order limit reached")

            orders = [
                item.model_dump(exclude_none=True)
                for item in existing
                if item.id != order.id
            ]
            stored = order.model_dump(exclude_none=True)
            orders.append(stored)
            try:
                saved = state.save("takeout", {"orders": orders}, document.revision)
            except PageRevisionConflict:
                if attempt == 2:
                    raise
                continue
            return {
                "ok": True,
                "page": "takeout",
                "revision": saved.revision,
                "updated_at": saved.updated_at,
                "order": stored,
            }
    raise RuntimeError("unreachable")
