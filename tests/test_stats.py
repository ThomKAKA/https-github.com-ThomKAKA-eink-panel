from datetime import datetime

import pytest

from panels.base import DisplayConfig
from panels.stats import StatsPanel


DEFAULT_DATA = {
    "panel_type": "stats",
    "title": "TODAY TOKEN",
    "primary_value": "258.42M",
    "primary_label": "TODAY TOKEN",
    "secondary_value": "8.51B",
    "secondary_label": "TOTAL TOKEN",
    "cost": "$406.92",
    "breakdown": [
        {"name": "GPT-5.x", "value": 66.7, "unit": "%"},
        {"name": "Claude", "value": 32.7, "unit": "%"},
        {"name": "Other", "value": 0.6, "unit": "%"},
    ],
    "source": "Mock Data",
}


def fixed_clock() -> datetime:
    return datetime(2026, 8, 31, 12, 34, 56)


def test_stats_panel_renders_native_size() -> None:
    image = StatsPanel(clock=fixed_clock).render(DEFAULT_DATA, DisplayConfig())

    assert image.size == (400, 300)
    assert image.mode == "L"
    assert image.getpixel((0, 0)) == 0


def test_stats_panel_eink_is_one_bit() -> None:
    image = StatsPanel(clock=fixed_clock).render(
        DEFAULT_DATA,
        DisplayConfig(),
        preview_mode="eink",
    )

    assert image.mode == "1"
    assert set(image.getdata()) <= {0, 255}


@pytest.mark.parametrize("updated_at", [None, "", "   "])
def test_stats_missing_time_uses_clock(updated_at: str | None) -> None:
    normalized = StatsPanel(clock=fixed_clock).normalize(
        {**DEFAULT_DATA, "updated_at": updated_at}
    )

    assert normalized.data.updated_at == "2026-08-31 12:34"


def test_stats_explicit_time_is_preserved() -> None:
    normalized = StatsPanel(clock=fixed_clock).normalize(
        {**DEFAULT_DATA, "updated_at": "2030-01-02 03:04:05"}
    )

    assert normalized.data.updated_at == "2030-01-02 03:04:05"


def test_stats_missing_primary_value_renders_no_data() -> None:
    panel = StatsPanel(clock=fixed_clock)
    normalized = panel.normalize({})
    image = panel.render({}, DisplayConfig())

    assert normalized.state == "waiting"
    assert normalized.data.primary_value == "NO DATA"
    assert image.size == (400, 300)


def test_stats_invalid_breakdown_renders_error_state() -> None:
    panel = StatsPanel(clock=fixed_clock)
    data = {**DEFAULT_DATA, "breakdown": [{"name": "GPT", "value": "bad"}]}

    assert panel.normalize(data).state == "error"
    assert panel.render(data, DisplayConfig()).size == (400, 300)


@pytest.mark.parametrize("value", [-10, 0, 250])
def test_stats_extreme_breakdown_values_render(value: float) -> None:
    data = {**DEFAULT_DATA, "breakdown": [{"name": "EXTREME", "value": value}]}

    assert StatsPanel(clock=fixed_clock).render(data, DisplayConfig()).size == (400, 300)
