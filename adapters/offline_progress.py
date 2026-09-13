"""Strict STEP016 offline input; deliberately separate from LocalJSONAdapter."""

import json
import re
from datetime import datetime

from panels.progress import ProgressPanelData


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_offline_progress(content: bytes) -> ProgressPanelData:
    """Decode UTF-8 and validate before any ordinary adapter time fallback."""
    raw = json.loads(content.decode("utf-8"), object_pairs_hook=_unique_object)
    required = {"project", "step", "progress", "status", "timestamp"}
    if not isinstance(raw, dict) or not required <= raw.keys():
        raise ValueError("Expected object with all required offline fields")
    if raw.keys() - required - {"description", "tags"}:
        raise ValueError("Unknown offline field")
    for key in ("project", "step", "status", "description"):
        value = raw.get(key, "")
        if not isinstance(value, str) or (key != "description" and not value.strip()):
            raise ValueError(f"Invalid text: {key}")
        raw[key] = value.strip()
    progress = raw["progress"]
    if type(progress) is not int or not 0 <= progress <= 100:
        raise ValueError("progress must be an integer from 0 to 100")
    timestamp = raw["timestamp"]
    if not isinstance(timestamp, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}", timestamp):
        raise ValueError("timestamp must be YYYY-MM-DD HH:mm (Asia/Shanghai)")
    datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
    tags = raw.get("tags", [])
    if not isinstance(tags, list) or len(tags) > 2 or any(
        not isinstance(tag, str) or not tag.strip() for tag in tags
    ):
        raise ValueError("tags must contain at most two nonempty strings")
    return ProgressPanelData(
        title=raw["project"], current_step=raw["step"], progress=progress,
        status=raw["status"], updated_at=timestamp, description=raw["description"],
        tags=[tag.strip() for tag in tags], source="Local JSON",
    )
