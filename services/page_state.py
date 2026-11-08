"""Atomic, single-process page documents for Host-rendered pages."""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Iterable, Mapping


logger = logging.getLogger(__name__)

MAX_DOCUMENT_BYTES = 16 * 1024
PAGE_ID = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")


class PageRevisionConflict(ValueError):
    """The caller edited a stale revision; no bytes were written."""

    def __init__(self, current: "PageDocument") -> None:
        super().__init__("Page revision is stale")
        self.current = current


class PageTooLarge(ValueError):
    """The encoded document exceeds the fixed storage budget."""


@dataclass(frozen=True)
class PageDocument:
    page: str
    revision: int
    updated_at: str | None
    data: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "revision": self.revision,
            "updated_at": self.updated_at,
            "data": deepcopy(self.data),
        }

    def render_data(self) -> dict[str, Any]:
        payload = deepcopy(self.data)
        payload["revision"] = self.revision
        payload["updated_at"] = self.updated_at
        return payload


class PageStateStore:
    """Persist one JSON document per registered file page.

    Page identifiers are checked against the registered set and never joined
    from a request path. Writes use a same-directory temporary file followed by
    ``os.replace`` so readers observe either the old or the new document.
    """

    def __init__(
        self,
        root: Path,
        pages: Iterable[str],
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._root = Path(root)
        self._pages = frozenset(pages)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._lock = Lock()

    @property
    def root(self) -> Path:
        return self._root

    def load(self, page_id: str) -> PageDocument:
        path = self._document_path(page_id)
        with self._lock:
            return self._read(path, page_id)

    def save(self, page_id: str, data: Mapping[str, Any], expected_revision: int) -> PageDocument:
        path = self._document_path(page_id)
        if not isinstance(data, Mapping):
            raise ValueError("Page data must be an object")
        if type(expected_revision) is not int or expected_revision < 1:
            raise ValueError("Page revision must be a positive integer")
        payload = deepcopy(dict(data))
        with self._lock:
            current = self._read(path, page_id)
            if current.revision != expected_revision:
                raise PageRevisionConflict(current)
            document = PageDocument(
                page=page_id,
                revision=current.revision + 1,
                updated_at=self._stamp(),
                data=payload,
            )
            encoded = self._encode(document)
            if len(encoded) > MAX_DOCUMENT_BYTES:
                raise PageTooLarge("Page document exceeds storage budget")
            self._write(path, encoded)
            return document

    def load_selection(self, default: str, allowed: Iterable[str]) -> str:
        allowed = frozenset(allowed)
        if default not in allowed:
            raise ValueError("Default page is not registered")
        path = self._root / "selection.json"
        with self._lock:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                page_id = payload.get("page") if isinstance(payload, dict) else None
                return page_id if page_id in allowed else default
            except (OSError, ValueError):
                return default

    def save_selection(self, page_id: str, allowed: Iterable[str]) -> None:
        if page_id not in frozenset(allowed):
            raise ValueError("Unknown page")
        payload = json.dumps({"page": page_id}, ensure_ascii=True).encode("utf-8")
        with self._lock:
            self._write(self._root / "selection.json", payload)

    def _document_path(self, page_id: str) -> Path:
        if not isinstance(page_id, str) or page_id not in self._pages or not PAGE_ID.fullmatch(page_id):
            raise ValueError("Unknown page")
        return self._root / f"{page_id}.json"

    def _read(self, path: Path, page_id: str) -> PageDocument:
        try:
            if path.stat().st_size > MAX_DOCUMENT_BYTES:
                raise ValueError("Page document exceeds storage budget")
            payload = json.loads(path.read_text(encoding="utf-8"))
            if (
                not isinstance(payload, dict)
                or payload.get("page") != page_id
                or type(payload.get("revision")) is not int
                or payload["revision"] < 1
                or not isinstance(payload.get("data"), dict)
                or not (payload.get("updated_at") is None or isinstance(payload.get("updated_at"), str))
            ):
                raise ValueError("Page document is invalid")
            return PageDocument(
                page=page_id,
                revision=payload["revision"],
                updated_at=payload.get("updated_at"),
                data=deepcopy(payload["data"]),
            )
        except FileNotFoundError:
            return self._default(page_id)
        except (OSError, ValueError) as error:
            logger.warning("Page state reset: page=%s category=%s", page_id, type(error).__name__)
            return self._default(page_id)

    def _default(self, page_id: str) -> PageDocument:
        data: dict[str, Any]
        if page_id == "memo":
            data = {"items": []}
        elif page_id == "course":
            today = self._now().date()
            data = {
                "semester_start": (today - timedelta(days=today.weekday())).isoformat(),
                "total_weeks": 18,
                "courses": [],
                "overrides": [],
            }
        elif page_id == "weather":
            data = {
                "city": "长沙",
                "hourly": [],
                "daily": [],
                "stale": True,
                "source": "open-meteo",
            }
        elif page_id == "calendar":
            data = {}
        elif page_id == "codex":
            data = {}
        elif page_id == "takeout":
            data = {"orders": []}
        else:
            raise ValueError("Unknown page")
        return PageDocument(page=page_id, revision=1, updated_at=None, data=data)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(SHANGHAI)

    def _stamp(self) -> str:
        return self._now().strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _encode(document: PageDocument) -> bytes:
        return (json.dumps(document.as_dict(), ensure_ascii=False, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )

    def _write(self, path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix=f"tmp-{path.stem}-", suffix=".tmp", dir=path.parent
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except BaseException:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise
