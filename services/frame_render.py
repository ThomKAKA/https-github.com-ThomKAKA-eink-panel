"""One render path for every Host page: strict audit, PNG preview, T frame."""

from __future__ import annotations

import io
from typing import Any, Mapping

from panels.base import BasePanel, DisplayConfig
from panels.frame_converter import png_to_logical_raw
from panels.transport_adapter import logical_to_transport


DEFAULT_CONFIG = DisplayConfig(400, 300, 0)


def render_assets(
    panel: BasePanel,
    data: Mapping[str, Any],
    *,
    config: DisplayConfig | None = None,
    preview_mode: str = "eink",
    strict: bool = True,
) -> tuple[bytes, bytes]:
    """Return the exact PNG preview and the 15000-byte transport frame it produced."""
    normalized = panel.normalize(data)
    if getattr(normalized, "state", "ok") != "ok":
        raise ValueError("Business frame unavailable")
    if getattr(getattr(normalized, "data", None), "status", None) in {"WAITING DATA", "UPDATE FAILED"}:
        raise ValueError("Business frame unavailable")

    image = panel.render(data, config or DEFAULT_CONFIG, preview_mode, strict=strict)
    audit = image.info.get("render_audit")
    if strict and audit is None:
        raise ValueError("Render audit missing")
    # Preserve the offline path's post-binarization visibility check.
    for entry in (audit or {}).get("texts", []):
        if set(image.crop(entry["bbox"]).getdata()) != {0, 255}:
            raise ValueError("Text has no visible contrast")

    output = io.BytesIO()
    image.save(output, format="PNG")
    png = output.getvalue()
    return png, logical_to_transport(png_to_logical_raw(png))
