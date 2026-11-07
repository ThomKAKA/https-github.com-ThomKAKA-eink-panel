"""Process-local, one-image LAN OTA offer. No path or credential is exposed."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)

MAX_FIRMWARE_BYTES = 1_200_000
ARM_SECONDS = 600
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


@dataclass(frozen=True)
class FirmwareImage:
    version: str
    size: int
    sha256: str
    body: bytes


class FirmwareOffer:
    """One configured image, one one-shot arm, all state process-local."""

    def __init__(self, config_path: Path, root: Path, *, clock=None) -> None:
        self._config_path = Path(config_path)
        self._root = Path(root)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._lock = Lock()
        self._image: FirmwareImage | None = None
        self._armed = False
        self._expires_at: datetime | None = None
        self._served_at: datetime | None = None
        self._device_version: str | None = None
        self._load()

    def _load(self) -> None:
        try:
            payload = json.loads(self._config_path.read_text(encoding="utf-8"))
            version = payload["version"]
            path = Path(payload["path"])
            if not path.is_absolute():
                path = self._root / path
            if not isinstance(version, str) or not _VERSION.fullmatch(version):
                raise ValueError("invalid version")
            if not path.is_file():
                raise ValueError("invalid image path")
            body = path.read_bytes()
            if not 1 <= len(body) <= MAX_FIRMWARE_BYTES:
                raise ValueError("invalid image size")
            image = FirmwareImage(version, len(body), hashlib.sha256(body).hexdigest(), body)
            self._image = image
            logger.info(
                "Firmware offer ready: version=%s size=%d sha256=%s",
                image.version,
                image.size,
                image.sha256[:12],
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            self._image = None
            logger.warning("Firmware offer unavailable; OTA disabled")

    @property
    def configured(self) -> bool:
        return self._image is not None

    def _now(self) -> datetime:
        value = self._clock()
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    def _expire_locked(self, now: datetime) -> None:
        if self._armed and self._expires_at is not None and now >= self._expires_at:
            self._armed = False
            self._expires_at = None

    def status(self) -> dict:
        with self._lock:
            now = self._now()
            self._expire_locked(now)
            image = self._image
            return {
                "configured": image is not None,
                "armed": self._armed,
                "version": image.version if image else None,
                "size": image.size if image else None,
                "sha256": image.sha256 if image else None,
                "expires_at": self._expires_at.isoformat() if self._expires_at else None,
                "served_at": self._served_at.isoformat() if self._served_at else None,
                "device_version": self._device_version,
            }

    def manifest(self) -> dict | None:
        with self._lock:
            image = self._image
            if image is None:
                return None
            now = self._now()
            self._expire_locked(now)
            if not self._armed:
                return {"armed": False}
            return {
                "armed": True,
                "version": image.version,
                "size": image.size,
                "sha256": image.sha256,
            }

    def arm(self) -> bool:
        with self._lock:
            if self._image is None:
                return False
            self._armed = True
            self._expires_at = self._now() + timedelta(seconds=ARM_SECONDS)
            self._served_at = None
            return True

    def disarm(self) -> None:
        with self._lock:
            self._armed = False
            self._expires_at = None

    def take_image(self) -> FirmwareImage | None:
        with self._lock:
            image = self._image
            if image is None:
                return None
            now = self._now()
            self._expire_locked(now)
            if not self._armed:
                return None
            self._armed = False
            self._expires_at = None
            self._served_at = now
            return image

    def observe_device_version(self, version: str) -> None:
        with self._lock:
            self._device_version = version
            if self._image is not None and version == self._image.version:
                self._armed = False
                self._expires_at = None
