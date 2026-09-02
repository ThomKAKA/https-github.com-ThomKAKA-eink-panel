"""Data refresh orchestration with in-memory Last Known Good fallback."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Callable

import httpx

from adapters import create_adapter
from adapters.base import format_timestamp
from panels.base import create_panel


logger = logging.getLogger(__name__)
Clock = Callable[[], datetime]


@dataclass(frozen=True)
class RefreshOutcome:
    source_id: str
    panel_type: str
    success: bool
    status: str
    data: dict[str, Any]
    source: str
    fetched_at: str
    source_updated_at: str | None
    last_success: str | None
    next_refresh: str | None
    stale: bool
    error: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RefreshManager:
    def __init__(
        self,
        config_path: Path,
        *,
        root: Path | None = None,
        clock: Clock | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.config_path = config_path.resolve()
        self.root = (root or self.config_path.parents[1]).resolve()
        self._clock = clock or datetime.now
        self._http_client = http_client
        self._sources = self._load_sources()
        self._last_good: dict[str, dict[str, Any]] = {}
        self._states: dict[str, dict[str, Any]] = {}
        self._lock = Lock()
        self._source_locks = {source_id: Lock() for source_id in self._sources}

    def _load_sources(self) -> dict[str, dict[str, Any]]:
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        sources = payload.get("sources")
        if not isinstance(sources, dict):
            raise ValueError("data_sources.json must contain a sources object")
        return {str(key): dict(value) for key, value in sources.items()}

    def list_sources(self, panel_type: str) -> list[dict[str, Any]]:
        compatible: list[dict[str, Any]] = []
        with self._lock:
            for source_id, config in self._sources.items():
                if config.get("panel") != panel_type or not config.get("enabled", True):
                    continue
                state = self._states.get(source_id, {})
                compatible.append(
                    {
                        "id": source_id,
                        "label": str(config.get("label") or source_id),
                        "type": str(config.get("type") or ""),
                        "panel": panel_type,
                        "default": bool(config.get("default", False)),
                        "status": state.get("status", "IDLE"),
                        "last_success": state.get("last_success"),
                        "last_fetch": state.get("last_fetch"),
                        "error": state.get("error"),
                    }
                )
        return compatible

    def refresh(
        self,
        source_id: str,
        *,
        sample_id: str | None = None,
        interval_seconds: int | None = None,
    ) -> RefreshOutcome:
        configured = self._sources.get(source_id)
        if configured is None:
            raise KeyError(source_id)
        if not configured.get("enabled", True):
            raise ValueError("Data source is disabled")

        with self._source_locks[source_id]:
            return self._refresh_locked(
                source_id,
                configured,
                sample_id=sample_id,
                interval_seconds=interval_seconds,
            )

    def _refresh_locked(
        self,
        source_id: str,
        configured: dict[str, Any],
        *,
        sample_id: str | None,
        interval_seconds: int | None,
    ) -> RefreshOutcome:
        source_config = dict(configured)
        if source_config.get("type") == "mock" and sample_id:
            source_config["sample_id"] = sample_id

        logger.info("Adapter Fetch: %s", source_id)
        try:
            adapter = create_adapter(
                source_config,
                root=self.root,
                clock=self._clock,
                http_client=self._http_client,
            )
            result = adapter.fetch()
        except Exception as exc:  # Defensive boundary for configuration/factory errors.
            logger.exception("Fetch Failed: %s", source_id)
            fetched_at = format_timestamp(self._clock)
            result_data = None
            result_success = False
            result_source = str(source_config.get("label") or source_id)
            source_updated_at = None
            error = str(exc)
        else:
            fetched_at = result.fetched_at
            result_data = result.data
            result_success = result.success
            result_source = result.source
            source_updated_at = result.source_updated_at
            error = result.error

        invalid_payload = False
        if result_success and result_data is not None:
            try:
                normalized = create_panel(str(source_config.get("panel") or "")).normalize(
                    result_data
                )
            except Exception:
                normalized = None
            if normalized is None or getattr(normalized, "state", None) != "ok":
                result_success = False
                invalid_payload = True
                source_updated_at = None
                error = "Panel data is incomplete or invalid"

        next_refresh = self._next_refresh(interval_seconds)
        with self._lock:
            previous = self._states.get(source_id, {})
            if result_success and result_data is not None:
                cached = deepcopy(result_data)
                self._last_good[source_id] = cached
                last_success = fetched_at
                status = "ONLINE"
                data = cached
                stale = False
                error = None
                logger.info("Fetch Success: %s", source_id)
            else:
                cached = self._last_good.get(source_id)
                last_success = previous.get("last_success")
                status = (
                    "ERROR"
                    if invalid_payload
                    else "OFFLINE"
                    if source_config.get("type") == "http_json"
                    else "ERROR"
                )
                data = deepcopy(cached) if cached is not None else {}
                stale = cached is not None
                logger.warning("Fetch Failed: %s: %s", source_id, error)

            self._states[source_id] = {
                "status": status,
                "last_success": last_success,
                "last_fetch": fetched_at,
                "next_refresh": next_refresh,
                "error": error,
                "stale": stale,
            }

        logger.info("Refresh: %s status=%s stale=%s", source_id, status, stale)
        return RefreshOutcome(
            source_id=source_id,
            panel_type=str(source_config.get("panel") or ""),
            success=result_success,
            status=status,
            data=data,
            source=result_source,
            fetched_at=fetched_at,
            source_updated_at=source_updated_at,
            last_success=last_success,
            next_refresh=next_refresh,
            stale=stale,
            error=error,
        )

    def _next_refresh(self, interval_seconds: int | None) -> str | None:
        if interval_seconds is None or interval_seconds <= 0:
            return None
        return (self._clock().astimezone() + timedelta(seconds=interval_seconds)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
