"""Serve the selected page through the unchanged device frame endpoint."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any, Callable, Iterable, Mapping

from panels.base import BasePanel
from services.device_ledger import apply_report
from services.frame_render import render_assets
from services.page_registry import DEFAULT_PAGE, PAGE_REGISTRY, create_page_panel, get_page
from services.page_state import PageStateStore
from services.progress_frame import FRAME_BYTES, FRAME_FORMAT, PublishedFrame


logger = logging.getLogger(__name__)
SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")
Renderer = Callable[[BasePanel, Mapping[str, Any]], tuple[bytes, bytes]]
ProgressProvider = Callable[[], Any]


class PageFrameService:
    """Publish the selected page while preserving the legacy Progress contract."""

    def __init__(
        self,
        state: PageStateStore,
        progress_provider: ProgressProvider,
        *,
        clock: Callable[[], datetime] | None = None,
        renderer: Renderer = render_assets,
        pages: Iterable[str] | None = None,
    ) -> None:
        self._state = state
        self._progress_provider = progress_provider
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._renderer = renderer
        self._allowed = frozenset(PAGE_REGISTRY if pages is None else pages)
        if not self._allowed <= set(PAGE_REGISTRY) or DEFAULT_PAGE not in self._allowed:
            raise ValueError("Registered pages required")
        self._lock = RLock()
        self._current = state.load_selection(DEFAULT_PAGE, self._allowed)
        self._published: PublishedFrame | None = None
        self._published_key: tuple[str, int, str] | None = None
        self._device: dict = {
            "last_seen": None,
            "firmware_version": None,
            "accepted_frame_version": None,
            "refresh_stage": None,
            "refresh_count": None,
        }

    @property
    def current_page(self) -> str:
        with self._lock:
            return self._current

    def day_key(self) -> str:
        return self._now().date().isoformat()

    def current(self) -> PublishedFrame | None:
        with self._lock:
            page_id = self._current
            if get_page(page_id).kind == "event":
                return self._progress_provider().current()

            document = self._state.load(page_id)
            day_key = self._now().date().isoformat()
            key = (page_id, document.revision, day_key)
            if self._published is not None and self._published_key == key:
                return self._published

            data = document.render_data()
            data["day_key"] = day_key
            try:
                _, body = self._renderer(create_page_panel(page_id), data)
                if type(body) is not bytes or len(body) != FRAME_BYTES:
                    raise ValueError("Complete immutable T frame required")
                candidate = PublishedFrame(
                    body=body,
                    etag='"' + hashlib.sha256(body).hexdigest() + '"',
                    version=(page_id, f"r{document.revision}", day_key),
                )
            except Exception as error:
                logger.warning(
                    "Page publication rejected: page=%s category=%s",
                    page_id,
                    type(error).__name__,
                )
                return self._published if self._published_key and self._published_key[0] == page_id else None
            self._published = candidate
            self._published_key = key
            return candidate

    def legacy_status(self) -> dict:
        """Return the untouched Progress status dictionary for exact-key clients."""
        return self._progress_provider().status()

    def status(self) -> dict:
        with self._lock:
            page_id = self._current
            spec = get_page(page_id)
            entries = self._page_entries()
            if spec.kind == "event":
                payload = dict(self.legacy_status())
                payload["page"] = page_id
                payload["pages"] = entries
                return payload

            document = self._state.load(page_id)
            ready = (
                self._published is not None
                and self._published_key == (page_id, document.revision, self._now().date().isoformat())
            )
            return {
                "publish_id": f"{page_id}-r{document.revision}",
                "frame_version": self._published.etag[1:-1] if ready and self._published else None,
                "host_stage": "FRAME_READY" if ready else "HOST_ACCEPTED",
                "source": page_id,
                "frame_format": FRAME_FORMAT,
                "device": dict(self._device),
                "page": page_id,
                "pages": entries,
            }

    def report(self, report) -> bool:
        with self._lock:
            page_id = self._current
            if get_page(page_id).kind == "event":
                return self._progress_provider().report(report)
            etag = self._published.etag if self._published is not None else None
            return apply_report(
                self._device,
                report,
                etag,
                observed_at=self._now().astimezone(timezone.utc),
            )

    def select_page(self, page_id: str) -> dict:
        with self._lock:
            spec = get_page(page_id)
            if page_id not in self._allowed:
                raise ValueError("Unknown page")
            self._current = page_id
            self._published = None
            self._published_key = None
            # Acceptance facts belong to the previously served page; contact facts do not.
            self._device["accepted_frame_version"] = None
            self._device["refresh_stage"] = None
            self._state.save_selection(page_id, self._allowed)
            return self.status()

    def _page_entries(self) -> list[dict]:
        entries = []
        for page_id, spec in PAGE_REGISTRY.items():
            if page_id not in self._allowed:
                continue
            revision = None
            if spec.kind == "file":
                revision = self._state.load(page_id).revision
            entries.append(
                {
                    "id": page_id,
                    "title": spec.title,
                    "kind": spec.kind,
                    "revision": revision,
                }
            )
        return entries

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(SHANGHAI)
