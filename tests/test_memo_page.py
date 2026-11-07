"""Deterministic Memo page rendering."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import io

import pytest
from pydantic import ValidationError

from panels.base import DisplayConfig, create_panel
from panels.frame_converter import png_to_logical_raw
from panels.memo import MemoItem, MemoPageData, MemoPanel
from panels.transport_adapter import logical_to_transport


SHANGHAI = timezone(timedelta(hours=8))


def clock_at(hour: int, minute: int = 0, day: int = 8):
    moment = datetime(2026, 11, day, hour, minute, tzinfo=SHANGHAI)
    return lambda: moment


def items(*rows: tuple[str, str, str | None, str]) -> list[dict]:
    return [
        {"id": item_id, "text": text, "due": due, "face": face}
        for item_id, text, due, face in rows
    ]


def test_factory_and_metadata():
    panel = create_panel("memo")
    assert isinstance(panel, MemoPanel)
    assert panel.get_metadata().panel_type == "memo"


def test_eight_items_are_allowed_and_order_is_stable():
    rows = items(*[(f"i{index}", f"事项{index}", None, "todo") for index in range(8)])
    payload = MemoPageData.model_validate({"items": rows})

    assert [item.id for item in payload.items] == [f"i{index}" for index in range(8)]


def test_ninth_item_duplicate_id_and_bad_schedule_are_rejected():
    rows = items(*[(f"i{index}", f"事项{index}", None, "todo") for index in range(8)])
    with pytest.raises(ValidationError):
        MemoPageData.model_validate({"items": rows + [{"id": "i9", "text": "第九项"}]})
    with pytest.raises(ValidationError):
        MemoPageData.model_validate({"items": rows[:1] + rows[:1]})
    with pytest.raises(ValidationError):
        MemoPageData.model_validate(
            {"items": [{"id": "a", "text": "坏时间", "due": "2026-02-30 10:00"}]}
        )
    with pytest.raises(ValidationError):
        MemoPageData.model_validate({"items": [{"id": "a", "text": ""}]})


def test_order_uses_schedule_then_id_not_completion_state():
    panel = MemoPanel(clock=clock_at(9))
    data = {
        "items": items(
            ("done", "已完成", "2026-11-09 10:00", "done"),
            ("later", "以后", "2026-11-10 10:00", "todo"),
            ("now", "今天", "2026-11-08 18:00", "doing"),
            ("none-b", "无截止乙", None, "note"),
            ("none-a", "无截止甲", None, "todo"),
        )
    }

    payload = panel.normalize({**data, "day_key": "2026-11-08"})

    assert [item.id for item in payload.data.items] == ["now", "done", "later", "none-a", "none-b"]


def test_render_is_deterministic_within_one_day():
    data = {
        "items": items(
            ("a", "买牛奶", "2026-11-08 09:30", "todo"),
            ("b", "交报告", "2026-11-09 23:59", "doing"),
        )
    }
    morning = MemoPanel(clock=clock_at(9, 0)).render(data, DisplayConfig(), "eink", strict=True)
    night = MemoPanel(clock=clock_at(23, 59)).render(data, DisplayConfig(), "eink", strict=True)
    first = io.BytesIO()
    second = io.BytesIO()
    morning.save(first, format="PNG")
    night.save(second, format="PNG")

    assert first.getvalue() == second.getvalue()
    assert morning.size == (400, 300) and morning.mode == "1"
    texts = [entry["text"] for entry in morning.info["render_audit"]["texts"]]
    assert "买牛奶" in texts and "交报告" in texts
    assert "TODAY 11-08" in texts and "LATER 11-09" in texts
    assert not any("09:30" in text or "23:59" in text for text in texts)
    assert len(logical_to_transport(png_to_logical_raw(first.getvalue()))) == 15000


def test_crossing_midnight_changes_status_and_pixels():
    data = {"items": items(("a", "交报告", "2026-11-08 23:59", "todo"))}
    today = MemoPanel(clock=clock_at(23, 59, 8)).render(data, DisplayConfig(), "eink", strict=True)
    tomorrow = MemoPanel(clock=clock_at(0, 0, 9)).render(data, DisplayConfig(), "eink", strict=True)

    today_texts = [entry["text"] for entry in today.info["render_audit"]["texts"]]
    tomorrow_texts = [entry["text"] for entry in tomorrow.info["render_audit"]["texts"]]
    assert "TODAY 11-08" in today_texts
    assert "OVERDUE 11-08" in tomorrow_texts
    assert today.tobytes() != tomorrow.tobytes()


def test_empty_page_has_a_stable_hint():
    image = MemoPanel(clock=clock_at(12)).render({"items": []}, DisplayConfig(), "eink", strict=True)
    texts = [entry["text"] for entry in image.info["render_audit"]["texts"]]

    assert "暂无备忘" in texts


def test_overlong_text_is_rejected_instead_of_truncated():
    with pytest.raises(ValueError):
        MemoPanel(clock=clock_at(12)).render(
            {"items": [{"id": "a", "text": "文" * 60}]}, DisplayConfig(), "eink", strict=True
        )


def test_memo_item_keeps_a_narrow_contract():
    assert MemoItem.model_validate({"id": "a_b-1", "text": "ok"}).face == "todo"
    with pytest.raises(ValidationError):
        MemoItem.model_validate({"id": "中文", "text": "ok"})
