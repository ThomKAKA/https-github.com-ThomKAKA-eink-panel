"""Refresh the weather page at startup and at the top of each hour."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
import threading
from typing import Callable


logger = logging.getLogger(__name__)


class WeatherScheduler:
    def __init__(
        self,
        source,
        *,
        clock: Callable[[], datetime] | None = None,
        thread_factory=threading.Thread,
    ) -> None:
        self._source = source
        self._clock = clock or (lambda: datetime.now())
        self._thread_factory = thread_factory
        self._thread = None
        self._stop = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop = threading.Event()
        self._thread = self._thread_factory(target=self._run, name="eink-weather", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self._source.refresh()
            except Exception:
                logger.warning("Weather refresh failed; keeping the cached frame", exc_info=True)
            if self._stop.wait(self.delay_seconds()):
                return

    def delay_seconds(self) -> float:
        now = self._clock()
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return max(60.0, (next_hour - now).total_seconds() + 5)

    def close(self) -> None:
        thread = self._thread
        if thread is None:
            return
        self._stop.set()
        self._thread = None
        thread.join(timeout=2.0)
        self._stop = None
