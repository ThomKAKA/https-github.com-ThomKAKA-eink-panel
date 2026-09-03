"""Lightweight in-memory state snapshots for external panel update events."""

from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from panels.base import create_panel


logger = logging.getLogger(__name__)
Clock = Callable[[], datetime]
PanelType = Literal["progress", "stats", "flow"]
IngestReason = Literal["accepted", "duplicate", "out_of_order"]


class PanelUpdateEvent(BaseModel):
    """Narrow event contract for replacing one source's panel snapshot."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    type: Literal["panel.update"]
    source: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    panel: PanelType
    occurred_at: AwareDatetime
    data: dict[str, Any]


@dataclass(frozen=True)
class PanelSnapshot:
    event_id: str
    type: str
    source: str
    panel: str
    occurred_at: str
    received_at: str
    data: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return deepcopy(asdict(self))


@dataclass(frozen=True)
class EventIngestOutcome:
    accepted: bool
    reason: IngestReason
    snapshot: PanelSnapshot

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "snapshot": self.snapshot.as_dict(),
        }


class InvalidPanelData(ValueError):
    """Raised when an event payload cannot produce a usable panel state."""


class EventStateStore:
    """Keep the latest valid event for each panel and source in this process."""

    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._snapshots: dict[tuple[str, str], PanelSnapshot] = {}
        self._lock = Lock()

    def ingest(self, event: PanelUpdateEvent) -> EventIngestOutcome:
        occurred_at = event.occurred_at.astimezone(timezone.utc).isoformat()
        panel_data = deepcopy(event.data)
        panel_data.setdefault("source", event.source)
        panel_data.setdefault("updated_at", occurred_at)
        normalized = create_panel(event.panel).normalize(panel_data)
        if getattr(normalized, "state", None) != "ok":
            logger.warning(
                "Event Rejected: panel=%s source=%s category=invalid_data",
                event.panel,
                event.source,
            )
            raise InvalidPanelData("Panel data is incomplete or invalid")

        key = (event.panel, event.source)
        with self._lock:
            current = self._snapshots.get(key)
            if current is not None and event.event_id == current.event_id:
                logger.info(
                    "Event Duplicate: panel=%s source=%s event_id=%s",
                    event.panel,
                    event.source,
                    event.event_id,
                )
                return EventIngestOutcome(
                    accepted=False,
                    reason="duplicate",
                    snapshot=self._copy_snapshot(current),
                )

            if current is not None and event.occurred_at <= datetime.fromisoformat(
                current.occurred_at
            ):
                logger.warning(
                    "Event Rejected: panel=%s source=%s category=out_of_order",
                    event.panel,
                    event.source,
                )
                return EventIngestOutcome(
                    accepted=False,
                    reason="out_of_order",
                    snapshot=self._copy_snapshot(current),
                )

            snapshot = PanelSnapshot(
                event_id=event.event_id,
                type=event.type,
                source=event.source,
                panel=event.panel,
                occurred_at=occurred_at,
                received_at=self._format_received_at(self._clock()),
                data=panel_data,
            )
            self._snapshots[key] = snapshot

        logger.info(
            "Event Accepted: panel=%s source=%s event_id=%s",
            event.panel,
            event.source,
            event.event_id,
        )
        return EventIngestOutcome(
            accepted=True,
            reason="accepted",
            snapshot=self._copy_snapshot(snapshot),
        )

    def get_snapshot(self, panel: str, source: str) -> PanelSnapshot | None:
        with self._lock:
            snapshot = self._snapshots.get((panel, source))
            return self._copy_snapshot(snapshot) if snapshot is not None else None

    @staticmethod
    def _copy_snapshot(snapshot: PanelSnapshot) -> PanelSnapshot:
        return PanelSnapshot(**snapshot.as_dict())

    @staticmethod
    def _format_received_at(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
