"""Process-local, on-demand publication of complete Progress T frames."""

from __future__ import annotations

import hashlib
import io
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Callable

from panels.base import DisplayConfig
from panels.frame_converter import png_to_logical_raw
from panels.progress import ProgressPanel
from panels.transport_adapter import logical_to_transport
from services.event_store import EventStateStore, PanelSnapshot


logger = logging.getLogger(__name__)
FRAME_FORMAT = "epd-t-400x300-mono1-msb-v1"
CACHE_CONTROL = "no-cache, no-transform"
FRAME_BYTES = 15000
# The product's snapshot wall-clock convention is UTC+08:00, not host local time.
SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")
_SOURCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_LOCAL_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")
_ISO_TIME = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}"
    r"(?::[0-9]{2}(?:\.[0-9]+)?)?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
)
_ENTITY_TAG = re.compile(r'(?:W/)?"([\x21\x23-\x7e\x80-\xff]*)"')


def page_timestamp(value: object) -> str:
    """Accept local minute snapshots or timezone-aware ISO timestamps only."""
    if not isinstance(value, str):
        raise ValueError("Invalid snapshot time")
    value = value.strip()
    if _LOCAL_TIME.fullmatch(value):
        instant = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=SHANGHAI)
    elif _ISO_TIME.fullmatch(value):
        instant = datetime.fromisoformat(value).astimezone(SHANGHAI)
    else:
        raise ValueError("Invalid snapshot time")
    return f"{instant.year:04d}-{instant.month:02d}-{instant.day:02d} {instant.hour:02d}:{instant.minute:02d}"


def map_snapshot(snapshot: PanelSnapshot) -> dict:
    if snapshot.panel != "progress":
        raise ValueError("Progress snapshot required")
    data = dict(snapshot.data)
    stamp = data.get("updated_at")
    if stamp is None or (isinstance(stamp, str) and not stamp.strip()):
        stamp = snapshot.occurred_at
    data["updated_at"] = page_timestamp(stamp)
    if not data.get("source"):
        data["source"] = snapshot.source
    return data


def render_transport(snapshot: PanelSnapshot) -> bytes:
    data = map_snapshot(snapshot)
    panel = ProgressPanel()
    normalized = panel.normalize(data)
    if normalized.state != "ok" or normalized.data.status in {"WAITING DATA", "UPDATE FAILED"}:
        raise ValueError("Business frame unavailable")
    image = panel.render(data, DisplayConfig(400, 300, 0), "eink", strict=True)
    # Preserve the offline path's post-binarization visibility check.
    for entry in image.info["render_audit"]["texts"]:
        if set(image.crop(entry["bbox"]).getdata()) != {0, 255}:
            raise ValueError("Text has no visible contrast")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return logical_to_transport(png_to_logical_raw(output.getvalue()))


@dataclass(frozen=True)
class PublishedFrame:
    body: bytes
    etag: str
    version: tuple[str, str, str]
    format: str = FRAME_FORMAT

    @classmethod
    def create(cls, body: bytes, snapshot: PanelSnapshot) -> PublishedFrame:
        if type(body) is not bytes or len(body) != FRAME_BYTES:
            raise ValueError("Complete immutable T frame required")
        return cls(body, '"' + hashlib.sha256(body).hexdigest() + '"',
                   (snapshot.source, snapshot.event_id, snapshot.occurred_at))


class ProgressFramePublisher:
    def __init__(self, store: EventStateStore, source: str | None,
                 *, renderer: Callable[[PanelSnapshot], bytes] = render_transport) -> None:
        self._store = store
        self._source = source if isinstance(source, str) and _SOURCE.fullmatch(source) else None
        self._renderer = renderer
        self._render_lock = Lock()
        self._published: PublishedFrame | None = None
        if self._source is None:
            # Do not echo configuration, business payloads or exception messages.
            logger.error("Progress frame configuration missing or invalid: EINK_PROGRESS_SOURCE")

    def current(self) -> PublishedFrame | None:
        if self._source is None:
            return None
        with self._render_lock:
            snapshot = self._store.get_snapshot("progress", self._source)
            if snapshot is None:
                return self._published
            version = (snapshot.source, snapshot.event_id, snapshot.occurred_at)
            if self._published is not None and self._published.version == version:
                return self._published
            try:
                candidate = PublishedFrame.create(self._renderer(snapshot), snapshot)
            except Exception as error:
                logger.warning("Progress publication rejected: %s", type(error).__name__)
                return self._published
            # Only reference assignment under the store lock: no rendering or I/O.
            self._store._if_current(snapshot, lambda: self._install(candidate))
            return self._published

    def _install(self, candidate: PublishedFrame) -> None:
        self._published = candidate


def parse_if_none_match(value: str | None) -> tuple[str, ...] | str | None:
    """Return opaque tags (weak comparison); None means absent, '*' wildcard."""
    if value is None:
        return None
    value = value.strip(" \t")
    if value == "*":
        return "*"
    tags = []
    position = 0
    # HTTP list syntax permits empty list members; quoted commas belong to tags.
    while position < len(value):
        if value[position] in " \t,":
            position += 1
            continue
        match = _ENTITY_TAG.match(value, position)
        if match is None:
            raise ValueError("Malformed If-None-Match")
        tags.append(match.group(1))
        position = match.end()
        while position < len(value) and value[position] in " \t":
            position += 1
        if position < len(value) and value[position] != ",":
            raise ValueError("Malformed If-None-Match")
    if not tags:
        raise ValueError("Malformed If-None-Match")
    return tuple(tags)


def condition_matches(tags: tuple[str, ...] | str | None, frame: PublishedFrame) -> bool:
    return tags is not None and (tags == "*" or frame.etag[1:-1] in tags)
