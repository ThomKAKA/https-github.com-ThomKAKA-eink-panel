"""Keep each test's page selection and documents off the real data directory."""

from __future__ import annotations

import sys

import pytest


@pytest.fixture(autouse=True)
def isolated_page_state(monkeypatch, tmp_path):
    monkeypatch.setenv("EINK_WEATHER", "0")
    monkeypatch.setenv("EINK_CODEX", "0")
    server = sys.modules.get("server.main")
    if server is None or not hasattr(server, "page_frames"):
        return
    from services.page_frames import PageFrameService
    from services.page_registry import FILE_PAGES
    from services.page_state import PageStateStore

    state = PageStateStore(tmp_path / "pages", FILE_PAGES)
    monkeypatch.setattr(server, "page_state", state)
    monkeypatch.setattr(
        server,
        "page_frames",
        PageFrameService(state, lambda: server.frame_publisher),
    )
