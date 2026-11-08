"""Single-device report facts shared by Progress and file-backed pages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol


class ReportLike(Protocol):
    frame_version: str
    firmware_version: str
    refresh_stage: str | None
    refresh_count: int | None


def apply_report(
    device: dict,
    report: ReportLike,
    current_etag: str | None,
    *,
    observed_at: datetime | None = None,
) -> bool:
    """Record contact and monotonic observations of the frame actually served.

    ``current_etag`` is the quoted Host frame identity, or ``None`` when no frame
    is currently publishable. A communication-only report still proves contact
    but must name that frame. Staged reports are accepted only for the served
    frame, and completion requires a prior acceptance of the same frame.
    """
    instant = observed_at or datetime.now(timezone.utc)
    device["last_seen"] = instant.isoformat()
    if report.refresh_count is not None:
        device["refresh_count"] = report.refresh_count
    served = current_etag[1:-1] if current_etag else None
    if report.refresh_stage is None:
        device["firmware_version"] = report.firmware_version
        return served is not None and report.frame_version == served
    if served is None or report.frame_version != served:
        return False
    same_frame = device["accepted_frame_version"] == report.frame_version
    if report.refresh_stage == "DEVICE_REFRESH_FLOW_COMPLETE" and not same_frame:
        return False
    if same_frame and device["refresh_stage"] == "DEVICE_REFRESH_FLOW_COMPLETE":
        return True  # A duplicate acceptance cannot regress a completed flow.
    device.update(
        firmware_version=report.firmware_version,
        accepted_frame_version=report.frame_version,
        refresh_stage=report.refresh_stage,
    )
    return True
