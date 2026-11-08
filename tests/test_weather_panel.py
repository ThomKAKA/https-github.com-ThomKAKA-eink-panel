"""Weather page model and deterministic renderer."""

from __future__ import annotations

import io

import pytest
from PIL import Image
from pydantic import ValidationError

from panels.weather import WeatherPageData, WeatherPanel
from services.frame_render import render_assets


def document(**updates):
    data = {
        "revision": 3,
        "updated_at": "2026-11-08 14:15",
        "day_key": "2026-11-08",
        "city": "长沙",
        "current_temp": 16,
        "current_label": "毛毛雨",
        "hourly": [
            {"hour": (14 + index) % 24, "temp": 16 - index, "label": "毛毛雨"}
            for index in range(8)
        ],
        "daily": [
            {"date": "11-08", "weekday": "周六", "high": 20, "low": 13, "label": "多云"},
            {"date": "11-09", "weekday": "周日", "high": 21, "low": 14, "label": "晴"},
            {"date": "11-10", "weekday": "周一", "high": 19, "low": 12, "label": "阴"},
        ],
        "stale": False,
        "source": "open-meteo",
    }
    data.update(updates)
    return data


def test_render_produces_the_fixed_device_frame():
    png, frame = render_assets(WeatherPanel(), document())
    image = Image.open(io.BytesIO(png))
    assert image.size == (400, 300)
    assert image.mode == "1"
    assert len(frame) == 15000


def test_same_document_renders_identical_bytes():
    first = render_assets(WeatherPanel(), document())[1]
    second = render_assets(WeatherPanel(), document())[1]
    assert first == second


def test_empty_document_renders_waiting_page():
    png, frame = render_assets(WeatherPanel(), {"day_key": "2026-11-08"})
    assert Image.open(io.BytesIO(png)).size == (400, 300)
    assert len(frame) == 15000


def test_stale_document_changes_the_frame():
    fresh = render_assets(WeatherPanel(), document())[1]
    stale = render_assets(WeatherPanel(), document(stale=True))[1]
    assert fresh != stale


@pytest.mark.parametrize(
    "updates",
    [
        {"hourly": [{"hour": 0, "temp": 1, "label": "晴"}] * 9},
        {"daily": [{"date": "11-08", "weekday": "周六", "high": 20, "low": 13, "label": "晴"}] * 4},
        {"current_temp": 99},
        {"city": "超长城市名字超出限制"},
        {"hourly": [{"hour": 24, "temp": 1, "label": "晴"}]},
        {"current_label": "太长天气标签"},
    ],
)
def test_invalid_documents_are_rejected(updates):
    with pytest.raises(ValidationError):
        WeatherPageData.model_validate(document(**updates))


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        WeatherPageData.model_validate(document(extra="x"))


def test_normalize_is_time_independent():
    panel = WeatherPanel()
    first = panel.normalize(document())
    second = panel.normalize(document())
    assert first.data.model_dump() == second.data.model_dump()
