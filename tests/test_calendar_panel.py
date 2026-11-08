"""Calendar month grid renderer."""

from __future__ import annotations

import io

import pytest
from PIL import Image
from pydantic import ValidationError

from panels.calendar import CalendarPageData, CalendarPanel
from services.frame_render import render_assets


def document(day="2026-11-08", **updates):
    data = {
        "revision": 4,
        "updated_at": "2026-11-08 14:00",
        "day_key": day,
    }
    data.update(updates)
    return data


def test_render_produces_the_fixed_device_frame():
    png, frame = render_assets(CalendarPanel(), document())
    image = Image.open(io.BytesIO(png))
    assert image.size == (400, 300)
    assert image.mode == "1"
    assert len(frame) == 15000


def test_same_month_and_day_render_identically():
    first = render_assets(CalendarPanel(), document())[1]
    second = render_assets(CalendarPanel(), document())[1]
    assert first == second


def test_new_month_changes_the_frame():
    november = render_assets(CalendarPanel(), document("2026-11-08"))[1]
    december = render_assets(CalendarPanel(), document("2026-12-01"))[1]
    assert november != december


def test_today_highlight_changes_the_frame():
    first = render_assets(CalendarPanel(), document("2026-11-08"))[1]
    other = render_assets(CalendarPanel(), document("2026-11-09"))[1]
    assert first != other


def test_new_year_month_renders():
    png, frame = render_assets(CalendarPanel(), document("2026-02-17"))
    assert len(frame) == 15000
    assert Image.open(io.BytesIO(png)).size == (400, 300)


def test_day_key_is_required():
    with pytest.raises(ValueError):
        render_assets(CalendarPanel(), {"revision": 1, "updated_at": None})


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        CalendarPageData.model_validate(document(month="2026-12"))


def test_invalid_day_key_is_rejected():
    with pytest.raises(ValidationError):
        CalendarPageData.model_validate(document("2026-13-01"))
