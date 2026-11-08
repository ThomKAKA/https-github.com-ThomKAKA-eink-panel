"""Codex usage page renderer."""

from __future__ import annotations

import io

import pytest
from PIL import Image
from pydantic import ValidationError

from panels.codex_usage import CodexPageData, CodexUsagePanel, format_tokens
from services.frame_render import render_assets


def document(**updates):
    data = {
        "revision": 2,
        "updated_at": "2026-11-08 15:20",
        "today_tokens": 0,
        "week_tokens": 22646123,
        "total_tokens": 132173864,
        "responses": 878,
        "sessions": 6,
        "last_activity": "11-07 15:10",
        "used_percent": 0.0,
        "window_minutes": 43200,
        "resets_at": "12-07",
        "plan": "free",
        "quota_at": "11-07 15:10",
        "days": [
            {"date": "11-02", "tokens": 14272697},
            {"date": "11-03", "tokens": 4310029},
            {"date": "11-04", "tokens": 0},
            {"date": "11-05", "tokens": 0},
            {"date": "11-06", "tokens": 3711316},
            {"date": "11-07", "tokens": 352081},
            {"date": "11-08", "tokens": 0},
        ],
        "stale": False,
        "source": "codex-sessions",
    }
    data.update(updates)
    return data


def texts(panel: CodexUsagePanel, data) -> list[str]:
    image = panel.render(data, __import__("panels.base", fromlist=["DisplayConfig"]).DisplayConfig(), strict=True)
    return [entry["text"] for entry in image.info["render_audit"]["texts"]]


def test_empty_document_renders_a_waiting_frame():
    png, frame = render_assets(CodexUsagePanel(), {})
    image = Image.open(io.BytesIO(png))
    assert image.size == (400, 300)
    assert image.mode == "1"
    assert len(frame) == 15000
    assert "等待 Codex 同步" in texts(CodexUsagePanel(), {})


def test_full_document_renders_real_numbers():
    rendered = texts(CodexUsagePanel(), document())
    assert "0" in rendered
    assert "近 7 天 22.6M" in rendered
    assert "累计 132.2M" in rendered
    assert "额度 FREE" in rendered
    assert "0%" in rendered
    assert "30 天窗口" in rendered
    assert "重置 12-07" in rendered
    assert "最后活动 11-07 15:10 · 878 次 · 6 个会话" in rendered
    assert "来源 / codex-sessions" in rendered
    assert "更新 / 2026-11-08 15:20" in rendered


def test_same_document_renders_identically():
    first = render_assets(CodexUsagePanel(), document())[1]
    second = render_assets(CodexUsagePanel(), document())[1]
    assert first == second


def test_stale_marker_changes_the_frame():
    fresh = render_assets(CodexUsagePanel(), document())[1]
    stale = render_assets(CodexUsagePanel(), document(stale=True))[1]
    assert fresh != stale
    assert "STALE" in texts(CodexUsagePanel(), document(stale=True))


def test_zero_today_is_data_not_waiting():
    rendered = texts(CodexUsagePanel(), document(today_tokens=0))
    assert "0" in rendered
    assert "等待 Codex 同步" not in rendered


def test_negative_tokens_are_rejected():
    with pytest.raises(ValidationError):
        CodexPageData.model_validate(document(today_tokens=-1))


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        CodexPageData.model_validate(document(model="gpt-5"))


@pytest.mark.parametrize(
    ("value", "label"),
    [
        (0, "0"),
        (999, "999"),
        (1000, "1.0k"),
        (352081, "352.1k"),
        (22646123, "22.6M"),
        (132173864, "132.2M"),
        (1387112797, "1.39B"),
    ],
)
def test_format_tokens(value, label):
    assert format_tokens(value) == label
