from datetime import datetime

import pytest

from panels.base import DisplayConfig, create_panel
from panels.design_system import (
    BORDER_THIN,
    FONT_LG,
    FONT_MD,
    FONT_NUMBER,
    FONT_SM,
    FONT_XL,
    FONT_XS,
    LEFT_COLUMN_RATIO,
    PANEL_PADDING,
    SPACE_1,
    SPACE_2,
    SPACE_3,
    SPACE_4,
    TAG_HEIGHT,
)
from panels.progress import ProgressPanel
from panels.flow import FlowPanel
from panels.stats import StatsPanel


DEFAULT_DATA = {
    "title": "CODING",
    "progress": 72,
    "current_step": "接口改动前",
    "status": "先确认",
    "description": "协议兼容需人工确认",
    "tags": ["观点通过", "暂停继续"],
    "source": "AI Copilot",
}


def fixed_clock() -> datetime:
    return datetime(2026, 8, 31, 12, 34, 56)


def test_design_system_is_phase_one_compact_profile() -> None:
    assert (FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL, FONT_NUMBER) == (
        8,
        10,
        13,
        18,
        24,
        64,
    )
    assert (SPACE_1, SPACE_2, SPACE_3, SPACE_4) == (3, 6, 9, 12)
    assert PANEL_PADDING == 10
    assert BORDER_THIN == 1
    assert TAG_HEIGHT == 20
    assert LEFT_COLUMN_RATIO == pytest.approx(0.38)


@pytest.mark.parametrize("progress", [0, 72, 100])
def test_progress_panel_renders_native_size(progress: int) -> None:
    panel = ProgressPanel(clock=fixed_clock)
    data = {**DEFAULT_DATA, "progress": progress}

    image = panel.render(data, DisplayConfig(), preview_mode="normal")

    assert image.size == (400, 300)
    assert image.mode == "L"
    assert image.getpixel((0, 0)) == 0
    assert image.getpixel((10, 10)) == 0
    assert image.getpixel((154, 10)) == 255


def test_eink_preview_is_one_bit() -> None:
    image = ProgressPanel(clock=fixed_clock).render(
        DEFAULT_DATA,
        DisplayConfig(),
        preview_mode="eink",
    )

    assert image.size == (400, 300)
    assert image.mode == "1"
    assert set(image.getdata()) <= {0, 255}


@pytest.mark.parametrize("updated_at", [None, "", "   "])
def test_missing_updated_at_uses_current_system_time(updated_at: str | None) -> None:
    panel = ProgressPanel(clock=fixed_clock)
    data = {**DEFAULT_DATA, "updated_at": updated_at}

    normalized = panel.normalize(data)

    assert normalized.data.updated_at == "2026-08-31 12:34"


def test_explicit_updated_at_overrides_clock() -> None:
    normalized = ProgressPanel(clock=fixed_clock).normalize(
        {**DEFAULT_DATA, "updated_at": "2030-01-02 03:04:05"}
    )

    assert normalized.data.updated_at == "2030-01-02 03:04:05"


def test_missing_data_renders_waiting_state() -> None:
    panel = ProgressPanel(clock=fixed_clock)

    normalized = panel.normalize({})
    image = panel.render({}, DisplayConfig())

    assert normalized.state == "waiting"
    assert normalized.data.status == "WAITING DATA"
    assert image.size == (400, 300)


def test_invalid_progress_renders_error_state() -> None:
    panel = ProgressPanel(clock=fixed_clock)

    normalized = panel.normalize({**DEFAULT_DATA, "progress": 101})
    image = panel.render({**DEFAULT_DATA, "progress": 101}, DisplayConfig())

    assert normalized.state == "error"
    assert normalized.data.status == "UPDATE FAILED"
    assert image.size == (400, 300)


def test_factory_exposes_all_phase_two_panels() -> None:
    assert isinstance(create_panel("progress"), ProgressPanel)
    assert isinstance(create_panel("stats"), StatsPanel)
    assert isinstance(create_panel("flow"), FlowPanel)
    with pytest.raises(ValueError):
        create_panel("unknown")
