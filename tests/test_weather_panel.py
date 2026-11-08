"""Weather page model and deterministic renderer for four cities."""

from __future__ import annotations

import io

import pytest
from PIL import Image
from pydantic import ValidationError

from panels.weather import WeatherPageData, WeatherPanel
from services.frame_render import render_assets


def city(name="长沙", temp=16, label="毛毛雨", hours=8, days=3):
    return {
        "name": name,
        "current_temp": temp,
        "current_label": label,
        "hourly": [
            {"hour": (14 + index) % 24, "temp": temp - index, "label": label}
            for index in range(hours)
        ],
        "daily": [
            {"date": "11-08", "weekday": "周六", "high": 20, "low": 13, "label": "多云"},
            {"date": "11-09", "weekday": "周日", "high": 21, "low": 14, "label": "晴"},
            {"date": "11-10", "weekday": "周一", "high": 19, "low": 12, "label": "阴"},
        ][:days],
    }


def document(**updates):
    data = {
        "revision": 3,
        "updated_at": "2026-11-08 14:15",
        "day_key": "2026-11-08",
        "current_city": "changsha",
        "cities": {
            "tianjin": city("天津", 9, "晴"),
            "guilin": city("桂林", 22, "多云"),
            "changsha": city("长沙", 16, "毛毛雨"),
            "nanjing": city("南京", 14, "阴"),
        },
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


def test_switching_the_current_city_changes_the_frame():
    changsha = render_assets(WeatherPanel(), document())[1]
    tianjin = render_assets(WeatherPanel(), document(current_city="tianjin"))[1]
    assert changsha != tianjin


def test_a_fifth_city_renders_without_a_panel_change():
    cities = dict(document()["cities"])
    cities["shanghai"] = city("上海", 19, "多云")
    shanghai = document(current_city="shanghai", cities=cities)
    png, frame = render_assets(WeatherPanel(), shanghai)
    assert Image.open(io.BytesIO(png)).size == (400, 300)
    assert len(frame) == 15000
    assert frame != render_assets(WeatherPanel(), document())[1]
    assert WeatherPageData.model_validate(shanghai).current_city == "shanghai"


def test_waiting_city_renders_a_page():
    empty = document(cities={"changsha": {"name": "长沙", "hourly": [], "daily": []}})
    png, frame = render_assets(WeatherPanel(), empty)
    assert Image.open(io.BytesIO(png)).size == (400, 300)
    assert len(frame) == 15000


@pytest.mark.parametrize(
    "updates",
    [
        {"hourly": [{"hour": 0, "temp": 1, "label": "晴"}] * 9},
        {"daily": [{"date": "11-08", "weekday": "周六", "high": 20, "low": 13, "label": "晴"}] * 4},
        {"current_temp": 99},
        {"current_label": "太长天气标签"},
    ],
)
def test_invalid_city_documents_are_rejected(updates):
    payload = document()
    payload["cities"]["changsha"].update(updates)
    with pytest.raises(ValidationError):
        WeatherPageData.model_validate(payload)


def test_unknown_current_city_is_rejected():
    with pytest.raises(ValidationError):
        WeatherPageData.model_validate(document(current_city="beijing"))


def test_long_city_name_is_rejected():
    payload = document()
    payload["cities"]["changsha"]["name"] = "超长城市名字超出限制"
    with pytest.raises(ValidationError):
        WeatherPageData.model_validate(payload)


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        WeatherPageData.model_validate(document(extra="x"))


def test_normalize_is_time_independent():
    panel = WeatherPanel()
    first = panel.normalize(document())
    second = panel.normalize(document())
    assert first.data.model_dump() == second.data.model_dump()
