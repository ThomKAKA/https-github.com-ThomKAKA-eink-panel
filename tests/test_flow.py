from datetime import datetime

import pytest

from panels.base import DisplayConfig
from panels.flow import FlowPanel


DEFAULT_DATA = {
    "panel_type": "flow",
    "title": "正在送达",
    "category": "DELIVERY",
    "eta": "18",
    "eta_unit": "分钟",
    "distance": "1.6km",
    "description": "骑手已取餐",
    "current_stage": 1,
    "stages": [
        {"name": "商家", "status": "done"},
        {"name": "骑手", "status": "active"},
        {"name": "门口", "status": "pending"},
    ],
    "source": "Mock Data",
}


def fixed_clock() -> datetime:
    return datetime(2026, 8, 31, 12, 34, 56)


def test_flow_panel_renders_native_size() -> None:
    image = FlowPanel(clock=fixed_clock).render(DEFAULT_DATA, DisplayConfig())

    assert image.size == (400, 300)
    assert image.mode == "L"
    assert image.getpixel((10, 10)) == 0


def test_flow_panel_eink_is_one_bit() -> None:
    image = FlowPanel(clock=fixed_clock).render(
        DEFAULT_DATA,
        DisplayConfig(),
        preview_mode="eink",
    )

    assert image.mode == "1"
    assert set(image.getdata()) <= {0, 255}


@pytest.mark.parametrize("updated_at", [None, "", "   "])
def test_flow_missing_time_uses_clock(updated_at: str | None) -> None:
    normalized = FlowPanel(clock=fixed_clock).normalize(
        {**DEFAULT_DATA, "updated_at": updated_at}
    )

    assert normalized.data.updated_at == "2026-08-31 12:34"


def test_flow_explicit_time_is_preserved() -> None:
    normalized = FlowPanel(clock=fixed_clock).normalize(
        {**DEFAULT_DATA, "updated_at": "2030-01-02 03:04"}
    )

    assert normalized.data.updated_at == "2030-01-02 03:04"


def test_flow_missing_data_renders_waiting_state() -> None:
    panel = FlowPanel(clock=fixed_clock)
    normalized = panel.normalize({})

    assert normalized.state == "waiting"
    assert normalized.message == "WAITING FLOW DATA"
    assert panel.render({}, DisplayConfig()).size == (400, 300)


def test_flow_invalid_data_renders_error_state() -> None:
    panel = FlowPanel(clock=fixed_clock)
    data = {**DEFAULT_DATA, "current_stage": -1}

    assert panel.normalize(data).state == "error"
    assert panel.render(data, DisplayConfig()).size == (400, 300)


def test_flow_error_stage_renders() -> None:
    data = {
        **DEFAULT_DATA,
        "stages": [{"name": "骑手", "status": "error"}],
    }

    assert FlowPanel(clock=fixed_clock).render(data, DisplayConfig()).size == (400, 300)


def test_flow_numeric_eta_is_normalized() -> None:
    normalized = FlowPanel(clock=fixed_clock).normalize({**DEFAULT_DATA, "eta": 18})

    assert normalized.data.eta == "18"
