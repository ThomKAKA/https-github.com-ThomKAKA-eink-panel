"""Explicit Host page registry; identifiers never come from a filesystem path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from panels.base import BasePanel, create_panel


DEFAULT_PAGE = "progress"


@dataclass(frozen=True)
class PageSpec:
    page_id: str
    title: str
    kind: Literal["event", "file"]
    panel_type: str
    editable: bool = True
    time_sensitive: bool = False


PAGE_REGISTRY: dict[str, PageSpec] = {
    "progress": PageSpec("progress", "Progress", "event", "progress"),
    "memo": PageSpec("memo", "备忘录", "file", "memo"),
    "course": PageSpec("course", "课程表", "file", "course"),
    "weather": PageSpec("weather", "天气", "file", "weather", editable=False),
    "calendar": PageSpec("calendar", "日历", "file", "calendar", editable=False),
    "codex": PageSpec("codex", "Codex 用量", "file", "codex", editable=False),
    "takeout": PageSpec("takeout", "外卖", "file", "takeout", time_sensitive=True),
}
FILE_PAGES = frozenset(page_id for page_id, spec in PAGE_REGISTRY.items() if spec.kind == "file")


def get_page(page_id: str) -> PageSpec:
    try:
        return PAGE_REGISTRY[page_id]
    except (KeyError, TypeError) as error:
        raise ValueError("Unknown page") from error


def create_page_panel(page_id: str) -> BasePanel:
    return create_panel(get_page(page_id).panel_type)
