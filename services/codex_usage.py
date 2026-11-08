"""Store synced Codex usage and flag it stale when syncing stops."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

from panels.codex_usage import CodexPageData
from services.page_state import PageStateStore


logger = logging.getLogger(__name__)
SHANGHAI = timezone(timedelta(hours=8))
STALE_AFTER = timedelta(minutes=15)
WATCH_INTERVAL_SECONDS = 60.0


class CodexUsageService:
    """Accept the sync payload and keep the stored document fresh."""

    def __init__(
        self,
        state: PageStateStore,
        *,
        clock: Callable[[], datetime] | None = None,
        stale_after: timedelta = STALE_AFTER,
        interval: float = WATCH_INTERVAL_SECONDS,
        thread_factory: Callable[..., Any] = threading.Thread,
    ) -> None:
        self._state = state
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._stale_after = stale_after
        self._interval = interval
        self._thread_factory = thread_factory
        self._stop = threading.Event()
        self._thread = None
        self._warning_logged = False

    def ingest(self, data: Mapping[str, Any]) -> dict[str, Any]:
        payload = CodexPageData.model_validate({**dict(data), "stale": False})
        stored = payload.model_dump(exclude={"revision", "updated_at", "day_key"})
        current = self._state.load("codex")
        document = self._state.save("codex", stored, current.revision)
        self._warning_logged = False
        return {
            "ok": True,
            "revision": document.revision,
            "stale": False,
            "updated_at": document.updated_at,
        }

    def mark_stale_if_aged(self) -> bool:
        document = self._state.load("codex")
        data = document.data
        if not data or data.get("stale") is True:
            return False
        if data.get("today_tokens") is None or document.updated_at is None:
            return False
        age = self._now() - self._stamp_time(document.updated_at)
        if age <= self._stale_after:
            return False
        self._state.save("codex", {**data, "stale": True}, document.revision)
        if not self._warning_logged:
            self._warning_logged = True
            logger.warning(
                "Codex usage marked stale: no sync for %s minutes",
                int(age.total_seconds() // 60),
            )
        return True

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = self._thread_factory(
            target=self._watch, name="eink-codex-watchdog", daemon=True
        )
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=2.0)

    def _watch(self) -> None:
        while not self._stop.wait(self._interval):
            try:
                self.mark_stale_if_aged()
            except Exception:
                logger.warning("Codex usage watchdog failed", exc_info=True)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(SHANGHAI)

    @staticmethod
    def _stamp_time(stamp: str) -> datetime:
        return datetime.strptime(stamp, "%Y-%m-%d %H:%M").replace(tzinfo=SHANGHAI)
