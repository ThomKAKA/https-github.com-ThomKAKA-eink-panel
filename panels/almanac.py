"""Chinese lunar calendar and 24 solar terms, computed for UTC+8.

The lunar month that contains the December solstice is month 11; a 13-month
year takes the first month without a major solar term as the leap month. New
moons and the solar longitude use the truncated Meeus series, which is well
inside one day for the years this product displays.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from math import floor, radians, sin


CST = timezone(timedelta(hours=8))
J2000 = 2451545.0
DELTA_T_SECONDS = 69.0

TERM_NAMES = (
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑",
    "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
)
TERM_LONGITUDES = tuple((285 + 15 * index) % 360 for index in range(24))
MAJOR_TERM_INDEXES = tuple(
    index for index, degree in enumerate(TERM_LONGITUDES) if degree % 30 == 0
)

LUNAR_DAYS = (
    "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十",
)
LUNAR_MONTHS = {
    1: "正月", 2: "二月", 3: "三月", 4: "四月", 5: "五月", 6: "六月",
    7: "七月", 8: "八月", 9: "九月", 10: "十月", 11: "冬月", 12: "腊月",
}
SOLAR_FESTIVALS = {(1, 1): "元旦", (5, 1): "劳动节", (10, 1): "国庆节"}
LUNAR_FESTIVALS = {
    (1, 1): "春节", (1, 15): "元宵", (5, 5): "端午", (7, 7): "七夕",
    (8, 15): "中秋", (9, 9): "重阳", (12, 8): "腊八",
}


def _jd(moment: datetime) -> float:
    return moment.timestamp() / 86400.0 + 2440587.5


def _datetime_from_jd(value: float) -> datetime:
    return datetime.fromtimestamp((value - 2440587.5) * 86400.0, tz=timezone.utc)


def _sun_longitude(jd: float) -> float:
    t = (jd - J2000) / 36525.0
    mean_longitude = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    mean_anomaly = radians((357.52911 + 35999.05029 * t - 0.0001537 * t * t) % 360)
    center = (
        (1.914602 - 0.004817 * t - 0.000014 * t * t) * sin(mean_anomaly)
        + (0.019993 - 0.000101 * t) * sin(2 * mean_anomaly)
        + 0.000289 * sin(3 * mean_anomaly)
    )
    omega = radians(125.04 - 1934.136 * t)
    return (mean_longitude + center - 0.00569 - 0.00478 * sin(omega)) % 360.0


@lru_cache(maxsize=128)
def term_datetime(year: int, index: int) -> datetime:
    target = TERM_LONGITUDES[index]
    offset = ((target - 280.0) % 360.0) / 0.98565
    guess = datetime(year, 1, 1, tzinfo=CST) + timedelta(days=offset)

    def difference(jd: float) -> float:
        return ((_sun_longitude(jd) - target + 180.0) % 360.0) - 180.0

    low = _jd(guess - timedelta(days=6))
    high = _jd(guess + timedelta(days=6))
    for _ in range(48):
        middle = (low + high) / 2
        if difference(middle) < 0:
            low = middle
        else:
            high = middle
    return _datetime_from_jd((low + high) / 2).astimezone(CST)


@lru_cache(maxsize=64)
def solar_terms(year: int) -> dict[date, str]:
    return {
        term_datetime(year, index).date(): TERM_NAMES[index]
        for index in range(24)
    }


def _new_moon_jde(k: int) -> float:
    t = k / 1236.85
    jde = (
        2451550.09766 + 29.530588861 * k + 0.00015437 * t * t
        - 0.00000015 * t ** 3 + 0.00000000073 * t ** 4
    )
    e = 1 - 0.002516 * t - 0.0000074 * t * t
    m = radians(2.5534 + 29.10535670 * k - 0.0000014 * t * t - 0.00000011 * t ** 3)
    mp = radians(
        201.5643 + 385.81693528 * k + 0.0107582 * t * t
        + 0.00001238 * t ** 3 - 0.000000058 * t ** 4
    )
    f = radians(
        160.7108 + 390.67050284 * k - 0.0016118 * t * t
        - 0.00000227 * t ** 3 + 0.000000011 * t ** 4
    )
    omega = radians(124.7746 - 1.56375588 * k + 0.0020672 * t * t + 0.00000215 * t ** 3)
    correction = (
        -0.40720 * sin(mp)
        + 0.17241 * e * sin(m)
        + 0.01608 * sin(2 * mp)
        + 0.01039 * sin(2 * f)
        + 0.00739 * e * sin(mp - m)
        - 0.00514 * e * sin(mp + m)
        + 0.00208 * e * e * sin(2 * m)
        - 0.00111 * sin(mp - 2 * f)
        - 0.00057 * sin(mp + 2 * f)
        + 0.00056 * e * sin(2 * mp + m)
        - 0.00042 * sin(3 * mp)
        + 0.00042 * e * sin(m + 2 * f)
        + 0.00038 * e * sin(m - 2 * f)
        - 0.00024 * e * sin(2 * mp - m)
        - 0.00017 * sin(omega)
        - 0.00007 * sin(mp + 2 * m)
        + 0.00004 * sin(2 * mp - 2 * f)
        + 0.00004 * sin(3 * m)
        + 0.00003 * sin(mp + m - 2 * f)
        + 0.00003 * sin(2 * mp + 2 * f)
        - 0.00003 * sin(mp + m + 2 * f)
        + 0.00003 * sin(mp - m + 2 * f)
        - 0.00002 * sin(mp - m - 2 * f)
        - 0.00002 * sin(3 * mp + m)
        + 0.00002 * sin(4 * mp)
    )
    return jde + correction


def _new_moon_date(k: int) -> date:
    jd_ut = _new_moon_jde(k) - DELTA_T_SECONDS / 86400.0
    return _datetime_from_jd(jd_ut).astimezone(CST).date()


@dataclass(frozen=True)
class LunarMonth:
    start: date
    end: date
    number: int
    leap: bool


def _has_major_term(start: date, end: date) -> bool:
    for year in {start.year, end.year}:
        for index in MAJOR_TERM_INDEXES:
            moment = term_datetime(year, index).date()
            if start <= moment < end:
                return True
    return False


@lru_cache(maxsize=8)
def _months_for_year(year: int) -> tuple[LunarMonth, ...]:
    """Months from the month 11 before this year's spring to the next month 11."""

    winter_before = term_datetime(year - 1, 23).date()
    winter_this = term_datetime(year, 23).date()
    anchor = _jd(datetime.combine(winter_before, datetime.min.time(), tzinfo=CST))
    first_k = floor((anchor - 2451550.09766) / 29.530588861) - 2
    starts: list[date] = []
    for k in range(first_k, first_k + 17):
        candidate = _new_moon_date(k)
        if candidate > winter_this + timedelta(days=40):
            break
        starts.append(candidate)
    begin = max(index for index, value in enumerate(starts) if value <= winter_before)
    finish = max(index for index, value in enumerate(starts) if value <= winter_this)
    # Keep the month 11 after this solstice whole so December dates resolve.
    starts = starts[begin:finish + 2]

    spans = [(starts[index], starts[index + 1]) for index in range(len(starts) - 1)]
    leap_index = None
    if len(spans) - 1 == 13:
        for index, (start, end) in enumerate(spans[:-1]):
            if not _has_major_term(start, end):
                leap_index = index
                break

    months: list[LunarMonth] = []
    previous = 11
    for index, (start, end) in enumerate(spans):
        if index == leap_index:
            number, leap = previous, True
        elif index == 0:
            number, leap = 11, False
        else:
            number, leap = previous % 12 + 1, False
        months.append(LunarMonth(start, end, number, leap))
        previous = number
    return tuple(months)


@lru_cache(maxsize=4096)
def lunar_date(day: date) -> tuple[int, bool, int, str, str]:
    """Return (month number, leap, day number, lunar day label, month name)."""

    months = _months_for_year(day.year)
    for month in months:
        if month.start <= day < month.end:
            number = (day - month.start).days + 1
            if not 1 <= number <= 30:
                raise ValueError("Lunar day outside month")
            return (
                month.number,
                month.leap,
                number,
                LUNAR_DAYS[number - 1],
                LUNAR_MONTHS[month.number],
            )
    raise ValueError("Date outside computed lunar year")


def festival(day: date) -> str | None:
    if (day.month, day.day) in SOLAR_FESTIVALS:
        return SOLAR_FESTIVALS[(day.month, day.day)]
    term = solar_terms(day.year).get(day)
    if term == "清明":
        return term
    month, leap, number, _, _ = lunar_date(day)
    if not leap:
        label = LUNAR_FESTIVALS.get((month, number))
        if label:
            return label
        if month == 12:
            next_month, next_leap, next_number, _, _ = lunar_date(day + timedelta(days=1))
            if next_month == 1 and not next_leap and next_number == 1:
                return "除夕"
    return None


def cell_label(day: date) -> str:
    """Small label under a day number: festival, solar term, or lunar day."""

    label = festival(day)
    if label:
        return label
    term = solar_terms(day.year).get(day)
    if term:
        return term
    month, leap, number, day_label, month_name = lunar_date(day)
    if number == 1:
        return ("闰" if leap else "") + month_name
    return day_label
