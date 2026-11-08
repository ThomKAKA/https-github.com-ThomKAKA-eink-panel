"""Lunar dates, leap months, solar terms and festival labels."""

from __future__ import annotations

from datetime import date

import pytest

from panels.almanac import cell_label, festival, lunar_date, solar_terms


@pytest.mark.parametrize(
    "day",
    ["2024-02-10", "2025-01-29", "2026-02-17", "2027-02-06", "2028-01-26"],
)
def test_lunar_new_year_is_month_one_day_one(day):
    assert lunar_date(date.fromisoformat(day))[:3] == (1, False, 1)


def test_leap_months_take_the_previous_number():
    assert lunar_date(date(2023, 3, 22))[:3] == (2, True, 1)
    assert lunar_date(date(2025, 7, 25))[:3] == (6, True, 1)
    assert lunar_date(date(2025, 7, 24))[0] == 6
    assert lunar_date(date(2025, 7, 24))[1] is False
    assert cell_label(date(2025, 7, 25)) == "闰六月"


def test_mid_autumn_and_new_year_eve():
    assert lunar_date(date(2026, 9, 25))[:3] == (8, False, 15)
    assert lunar_date(date(2025, 10, 6))[:3] == (8, False, 15)
    assert lunar_date(date(2026, 2, 16))[:3] == (12, False, 29)
    assert cell_label(date(2026, 2, 16)) == "除夕"


def test_2026_solar_terms():
    terms = solar_terms(2026)
    assert len(terms) == 24
    assert terms[date(2026, 2, 4)] == "立春"
    assert terms[date(2026, 4, 5)] == "清明"
    assert terms[date(2026, 6, 21)] == "夏至"
    assert terms[date(2026, 11, 7)] == "立冬"
    assert terms[date(2026, 12, 22)] == "冬至"


def test_festival_priority_and_labels():
    assert cell_label(date(2026, 2, 17)) == "春节"
    assert cell_label(date(2026, 6, 19)) == "端午"
    assert cell_label(date(2026, 9, 25)) == "中秋"
    assert cell_label(date(2026, 10, 1)) == "国庆节"
    assert cell_label(date(2026, 4, 5)) == "清明"
    assert cell_label(date(2026, 9, 26)) == "十六"


def test_first_lunar_day_shows_the_month_name():
    assert cell_label(date(2026, 2, 17)) == "春节"
    _, _, number, _, month_name = lunar_date(date(2026, 2, 17))
    assert number == 1 and month_name == "正月"
    assert lunar_date(date(2026, 3, 19))[0] == 2
    assert cell_label(date(2026, 3, 19)) == "二月"


def test_term_festival_is_reported_once():
    assert festival(date(2026, 4, 5)) == "清明"
    assert festival(date(2026, 4, 6)) is None
