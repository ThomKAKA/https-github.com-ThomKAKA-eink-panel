"""Deterministic Takeout page rendering and automatic overdue state."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import io

import pytest
from pydantic import ValidationError

from panels.base import DisplayConfig
from panels.takeout import (
    STATUS_LABELS,
    TakeoutOrder,
    TakeoutPageData,
    TakeoutPanel,
    effective_status,
)
from panels.frame_converter import png_to_logical_raw
from panels.transport_adapter import logical_to_transport


SHANGHAI = timezone(timedelta(hours=8))


def clock_at(hour: int, minute: int) -> datetime:
    return datetime(2026, 11, 8, hour, minute, tzinfo=SHANGHAI)


def order(identifier: str, name: str = "楼下快餐", status: str = "waiting",
          expected: str | None = "12:30", note: str | None = None) -> dict:
    return {
        "id": identifier,
        "name": name,
        "status": status,
        "expected_at": expected,
        "note": note,
    }


def document(orders: list[dict] | None = None, *, now: str | None = "12:00") -> dict:
    return {
        "revision": 3,
        "updated_at": "2026-11-08 12:05",
        "day_key": "2026-11-08",
        "now": now,
        "orders": orders if orders is not None else [order("t1")],
    }


def texts_of(image) -> list[str]:
    return [entry["text"] for entry in image.info["render_audit"]["texts"]]


def sizes_of(image) -> dict[str, int]:
    return {entry["text"]: entry["size"] for entry in image.info["render_audit"]["texts"]}


def test_status_labels_are_the_four_page_states():
    assert STATUS_LABELS == {
        "waiting": "待取",
        "delivering": "配送中",
        "arrived": "已到",
        "late": "超时",
    }


def test_empty_document_renders_the_empty_state():
    image = TakeoutPanel(clock=lambda: clock_at(12, 0)).render(
        {"revision": 1, "updated_at": None, "day_key": "2026-11-08", "now": "12:00",
         "orders": []},
        DisplayConfig(),
        "eink",
        strict=True,
    )
    texts = texts_of(image)

    assert "暂无外卖订单" in texts
    assert "在 /manage 添加外卖单" in texts
    assert "0单" in texts
    assert "来源 / takeout r1" in texts
    assert "更新 / --" in texts
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    assert len(logical_to_transport(png_to_logical_raw(stream.getvalue()))) == 15000


def test_full_document_renders_status_time_name_and_note():
    image = TakeoutPanel(clock=lambda: clock_at(12, 20)).render(
        document([
            order("t1", "牛肉面", "waiting", "12:40"),
            order("t2", "咖啡", "delivering", "12:30", note="放前台"),
            order("t3", "水果", "arrived", "12:10"),
        ], now="12:20"),
        DisplayConfig(),
        "eink",
        strict=True,
    )
    texts = texts_of(image)

    assert "3单" in texts
    assert "待取 · 预计 12:40" in texts
    assert "配送中 · 预计 12:30" in texts
    assert "已到 · 12:10" in texts
    assert "牛肉面" in texts and "咖啡" in texts and "水果" in texts
    assert "放前台" in texts
    assert "来源 / takeout r3" in texts
    assert "更新 / 2026-11-08 12:05" in texts


def test_overdue_is_derived_from_the_expected_minute():
    order_row = order("t1", "牛肉面", "delivering", "12:30")

    early = TakeoutPanel().render(
        document([order_row], now="12:30"), DisplayConfig(), "eink", strict=True
    )
    late = TakeoutPanel().render(
        document([order_row], now="12:31"), DisplayConfig(), "eink", strict=True
    )

    assert "配送中 · 预计 12:30" in texts_of(early)
    assert "超时 · 预计 12:30" in texts_of(late)
    assert early.tobytes() != late.tobytes()


def test_arrived_is_never_overdue():
    image = TakeoutPanel().render(
        document([order("t1", "水果", "arrived", "11:00")], now="23:59"),
        DisplayConfig(),
        "eink",
        strict=True,
    )
    assert "已到 · 11:00" in texts_of(image)
    assert "超时 · 预计 11:00" not in texts_of(image)


def test_order_without_expected_time_cannot_be_overdue():
    image = TakeoutPanel().render(
        document([order("t1", "面包", "waiting", None)], now="23:59"),
        DisplayConfig(),
        "eink",
        strict=True,
    )
    texts = texts_of(image)
    assert "待取" in texts
    assert all(not text.startswith("超时") for text in texts)


def test_effective_status_contract():
    assert effective_status(TakeoutOrder(id="a", name="x", status="waiting",
                                         expected_at="12:30"), "12:30") == "waiting"
    assert effective_status(TakeoutOrder(id="a", name="x", status="waiting",
                                         expected_at="12:30"), "12:31") == "late"
    assert effective_status(TakeoutOrder(id="a", name="x", status="delivering",
                                         expected_at=None), "23:59") == "delivering"
    assert effective_status(TakeoutOrder(id="a", name="x", status="arrived",
                                         expected_at="01:00"), "23:59") == "arrived"


def test_active_orders_come_first_in_status_order():
    image = TakeoutPanel().render(
        document([
            order("t1", "已到单", "arrived", "11:00"),
            order("t2", "待取单", "waiting", "12:40"),
            order("t3", "配送单", "delivering", "12:10"),
            order("t4", "超时单", "waiting", "11:30"),
        ], now="12:20"),
        DisplayConfig(),
        "eink",
        strict=True,
    )
    names = texts_of(image)

    assert names.index("超时单") < names.index("配送单")
    assert names.index("配送单") < names.index("待取单")
    assert names.index("待取单") < names.index("已到单")


@pytest.mark.parametrize("payload", [
    {"orders": [{"id": "a", "name": "x", "status": "waiting", "extra": 1}]},
    {"orders": [{"id": "a", "name": "x", "status": "late"}]},
    {"orders": [{"id": "a", "name": "x", "expected_at": "24:00"}]},
    {"orders": [{"id": "a", "name": "x"}, {"id": "a", "name": "y"}]},
    {"orders": [{"id": f"o{index}", "name": "x"} for index in range(7)]},
    {"orders": [{"id": "a", "name": "x" * 21}]},
    {"orders": [{"id": "a", "name": "x", "note": "x" * 9}]},
    {"orders": [{"id": "", "name": "x"}]},
    {"now": "9:00"},
    {"day_key": "2026-13-01"},
])
def test_invalid_documents_are_rejected(payload):
    with pytest.raises(ValidationError):
        TakeoutPageData.model_validate(payload)


def test_render_is_deterministic_and_depends_only_on_injected_now():
    data = document([order("t1", "牛肉面", "delivering", "12:30")], now="12:31")

    first = TakeoutPanel().render(data, DisplayConfig(), "eink", strict=True)
    second = TakeoutPanel().render(data, DisplayConfig(), "eink", strict=True)
    assert first.tobytes() == second.tobytes()


def test_six_orders_fit_and_a_long_name_is_fitted():
    orders = [
        order(f"t{index}", "很长的外卖订单名称" * 2, "waiting", f"12:{index:02d}")
        for index in range(6)
    ]
    image = TakeoutPanel().render(document(orders, now="12:00"),
                                  DisplayConfig(), "eink", strict=True)
    texts = texts_of(image)

    assert "6单" in texts
    assert "来源 / takeout r3" in texts
    for index in range(6):
        assert f"待取 · 预计 12:{index:02d}" in texts


def test_key_labels_are_thirteen_pixels_and_notes_ten():
    image = TakeoutPanel().render(
        document([order("t1", "牛肉面", "delivering", "12:30", note="放前台")], now="12:31"),
        DisplayConfig(),
        "eink",
        strict=True,
    )
    sizes = sizes_of(image)

    assert sizes["1单"] == 13
    assert sizes["超时 · 预计 12:30"] == 13
    assert sizes["牛肉面"] == 13
    assert sizes["放前台"] == 10
    assert sizes["来源 / takeout r3"] == 10


def test_day_line_shows_the_weekday():
    image = TakeoutPanel(clock=lambda: clock_at(12, 0)).render(
        document([]), DisplayConfig(), "eink", strict=True
    )
    assert "2026-11-08 周日" in texts_of(image)
