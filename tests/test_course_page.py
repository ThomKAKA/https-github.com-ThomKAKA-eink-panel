"""Deterministic Course page rendering and schedule rules."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import io

import pytest
from pydantic import ValidationError

from panels.base import DisplayConfig, create_panel
from panels.course import (
    Course,
    CourseOverride,
    CoursePageData,
    CoursePanel,
    course_week,
    day_courses,
    parse_weeks,
)
from panels.frame_converter import png_to_logical_raw
from panels.transport_adapter import logical_to_transport


SHANGHAI = timezone(timedelta(hours=8))
SEMESTER = "2026-09-07"


def clock_at(hour: int, minute: int = 0, day: int = 8, month: int = 11):
    moment = datetime(2026, month, day, hour, minute, tzinfo=SHANGHAI)
    return lambda: moment


def document(**updates) -> dict:
    payload = {
        "semester_start": SEMESTER,
        "total_weeks": 18,
        "courses": [
            {"id": "a", "name": "高等数学", "weekday": 7, "weeks": [9],
             "start": "08:00", "end": "09:40", "room": "A-101"},
            {"id": "b", "name": "大学英语", "weekday": 7, "weeks": [8, 9, 10],
             "start": "10:00", "end": "11:40", "room": "B-202"},
        ],
        "overrides": [],
    }
    payload.update(updates)
    return payload


@pytest.mark.parametrize("text,expected", [
    ("1-8,10", [1, 2, 3, 4, 5, 6, 7, 8, 10]),
    (" 3, 5-6 ", [3, 5, 6]),
    ("18", [18]),
])
def test_parse_weeks(text, expected):
    assert parse_weeks(text, 18) == expected


@pytest.mark.parametrize("text", ["", "0", "1-", "-3", "9-7", "1,,2", "19", "1-3,2", "abc"])
def test_parse_weeks_rejects_invalid_input(text):
    with pytest.raises(ValueError):
        parse_weeks(text, 18)


def test_course_week_boundaries():
    assert course_week(SEMESTER, 18, "2026-09-07") == 1
    assert course_week(SEMESTER, 18, "2026-09-13") == 1
    assert course_week(SEMESTER, 18, "2026-09-14") == 2
    assert course_week(SEMESTER, 18, "2026-11-08") == 9
    assert course_week(SEMESTER, 18, "2027-01-11") is None
    assert course_week(SEMESTER, 18, "2026-09-06") is None


def test_day_courses_filter_sort_and_overrides():
    payload = CoursePageData.model_validate(document(overrides=[
        {"date": "2026-11-08", "course_id": "b", "action": "cancel"},
        {"date": "2026-11-08", "course_id": "a", "action": "move_room", "room": "C-303"},
    ]))

    effective = day_courses(payload, "2026-11-08")

    assert [(course.id, course.start, course.end, course.room) for course in effective] == [
        ("a", "08:00", "09:40", "C-303"),
    ]


def test_move_time_changes_order():
    payload = CoursePageData.model_validate(document(overrides=[
        {"date": "2026-11-08", "course_id": "a", "action": "move_time",
         "start": "13:00", "end": "14:40"},
    ]))

    effective = day_courses(payload, "2026-11-08")

    assert [course.id for course in effective] == ["b", "a"]
    assert effective[1].start == "13:00" and effective[1].end == "14:40"


def test_override_on_another_day_or_unknown_course_is_ignored():
    payload = CoursePageData.model_validate(document(overrides=[
        {"date": "2026-11-09", "course_id": "a", "action": "cancel"},
        {"date": "2026-11-08", "course_id": "missing", "action": "cancel"},
    ]))

    assert [course.id for course in day_courses(payload, "2026-11-08")] == ["a", "b"]
    assert [course.id for course in day_courses(payload, "2026-11-09")] == []


def test_one_weekday_is_capped_per_week_not_across_semester():
    nine_monday = [
        {"id": f"m{index}", "name": "课", "weekday": 1, "weeks": [1],
         "start": "08:00", "end": "09:00", "room": "A-1"}
        for index in range(9)
    ]
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(courses=nine_monday))

    spread = [{**row, "weekday": (index % 7) + 1}
              for index, row in enumerate(nine_monday)]
    assert len(CoursePageData.model_validate(document(courses=spread)).courses) == 9

    alternating = [
        {**row, "weeks": [1, 3, 5, 7, 9] if index < 5 else [2, 4, 6, 8, 10]}
        for index, row in enumerate(nine_monday)
    ]
    assert len(CoursePageData.model_validate(document(courses=alternating)).courses) == 9


def test_eight_rows_fit_above_the_footer():
    rows = [
        {"id": f"r{index}", "name": f"课{index}", "weekday": 7, "weeks": [9],
         "start": f"{8 + index:02d}:00", "end": f"{8 + index:02d}:30", "room": f"A-{index + 1}"}
        for index in range(8)
    ]
    image = CoursePanel(clock=clock_at(8, 0)).render(
        document(courses=rows), DisplayConfig(), "eink", strict=True
    )
    texts = [entry["text"] for entry in image.info["render_audit"]["texts"]]

    assert "课7" in texts and "A-8" in texts


def test_course_document_rejects_unsafe_or_ambiguous_input():
    rows = document()["courses"]
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(courses=rows + [
            {"id": f"x{index}", "name": "课", "weekday": 1, "weeks": [1],
             "start": "08:00", "end": "09:00", "room": "A-1"} for index in range(11)
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(courses=[rows[0], rows[0]]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(courses=[
            {**rows[0], "weeks": [19]},
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(overrides=[
            {"date": "2026-11-08", "course_id": "a", "action": "cancel"},
            {"date": "2026-11-08", "course_id": "a", "action": "cancel"},
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(overrides=[
            {"date": "2026-11-08", "course_id": "a", "action": "move_room"},
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(overrides=[
            {"date": "2026-11-08", "course_id": "a", "action": "cancel", "room": "A-1"},
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(semester_start="2026-02-30"))


def test_render_is_deterministic_and_contains_daily_courses():
    data = document()
    morning = CoursePanel(clock=clock_at(8, 0)).render(data, DisplayConfig(), "eink", strict=True)
    night = CoursePanel(clock=clock_at(22, 0)).render(data, DisplayConfig(), "eink", strict=True)
    first = io.BytesIO()
    second = io.BytesIO()
    morning.save(first, format="PNG")
    night.save(second, format="PNG")

    assert first.getvalue() == second.getvalue()
    assert morning.size == (400, 300) and morning.mode == "1"
    texts = [entry["text"] for entry in morning.info["render_audit"]["texts"]]
    assert "第 9 周" in texts and "2026-11-08 周日" in texts
    assert "08:00-09:40" in texts and "10:00-11:40" in texts
    assert "高等数学" in texts and "A-101" in texts
    assert len(logical_to_transport(png_to_logical_raw(first.getvalue()))) == 15000


def test_crossing_to_another_day_changes_courses():
    data = document()
    sunday = CoursePanel(clock=clock_at(8, 0, 8)).render(data, DisplayConfig(), "eink", strict=True)
    monday = CoursePanel(clock=clock_at(8, 0, 9)).render(data, DisplayConfig(), "eink", strict=True)

    sunday_texts = [entry["text"] for entry in sunday.info["render_audit"]["texts"]]
    monday_texts = [entry["text"] for entry in monday.info["render_audit"]["texts"]]
    assert "高等数学" in sunday_texts and "高等数学" not in monday_texts
    assert "今天没有课" in monday_texts
    assert sunday.tobytes() != monday.tobytes()


def test_outside_semester_is_explicit():
    image = CoursePanel(clock=clock_at(8, 0, 1, 6)).render(document(), DisplayConfig(), "eink", strict=True)
    texts = [entry["text"] for entry in image.info["render_audit"]["texts"]]

    assert "学期外" in texts and "今天没有课" in texts


def test_long_name_is_fitted_not_truncated():
    data = document(courses=[{
        "id": "long", "name": "课" * 24, "weekday": 7, "weeks": [9],
        "start": "08:00", "end": "09:40", "room": "A-101",
    }])
    image = CoursePanel(clock=clock_at(8, 0)).render(data, DisplayConfig(), "eink", strict=True)
    texts = [entry["text"] for entry in image.info["render_audit"]["texts"]]

    assert "课" * 24 in texts


def test_factory_and_schema_contract():
    assert isinstance(create_panel("course"), CoursePanel)
    assert Course.model_validate({
        "id": "a", "name": "课", "weekday": 1, "weeks": [1],
        "start": "08:00", "end": "09:00", "room": "A-1",
    }).weeks == [1]
    with pytest.raises(ValidationError):
        CourseOverride.model_validate({"date": "2026-11-08", "course_id": "a", "action": "cancel",
                                       "room": "A-1"})
    assert date.fromisoformat(SEMESTER).weekday() == 0
