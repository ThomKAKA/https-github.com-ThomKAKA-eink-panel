"""Deterministic Course page rendering and the fixed five-period schedule."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import io

import pytest
from pydantic import ValidationError

from panels.base import DisplayConfig, create_panel
from panels.course import (
    PERIODS,
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
             "period": 1, "room": "A-101"},
            {"id": "b", "name": "大学英语", "weekday": 7, "weeks": [8, 9, 10],
             "period": 2, "room": "B-202"},
        ],
        "overrides": [],
    }
    payload.update(updates)
    return payload


def texts_of(image) -> list[str]:
    return [entry["text"] for entry in image.info["render_audit"]["texts"]]


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


def test_five_fixed_periods_are_the_only_times():
    assert PERIODS == {
        1: ("08:00", "09:40"),
        2: ("10:00", "11:40"),
        3: ("14:00", "15:40"),
        4: ("16:00", "17:40"),
        5: ("19:00", "20:40"),
    }
    payload = CoursePageData.model_validate(document())
    assert [course.period for course in payload.courses] == [1, 2]
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(courses=[
            {"id": "x", "name": "课", "weekday": 1, "weeks": [1], "period": 6, "room": "A-1"},
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(courses=[
            {"id": "x", "name": "课", "weekday": 1, "weeks": [1],
             "start": "08:00", "end": "09:40", "room": "A-1"},
        ]))


def test_day_courses_use_periods_and_apply_cancel_room_and_period_moves():
    payload = CoursePageData.model_validate(document(overrides=[
        {"date": "2026-11-08", "course_id": "b", "action": "cancel"},
        {"date": "2026-11-08", "course_id": "a", "action": "move_room", "room": "C-303"},
    ]))
    effective = day_courses(payload, "2026-11-08")
    assert [(course.id, course.period, course.room) for course in effective] == [
        ("a", 1, "C-303"),
    ]

    moved = CoursePageData.model_validate(document(overrides=[
        {"date": "2026-11-08", "course_id": "a", "action": "move_period", "period": 4},
    ]))
    order = day_courses(moved, "2026-11-08")
    assert [(course.id, course.period) for course in order] == [("b", 2), ("a", 4)]


def test_add_override_inserts_one_extra_class_on_that_day_only():
    payload = CoursePageData.model_validate(document(overrides=[
        {"date": "2026-11-08", "course_id": "extra-1", "action": "add",
         "name": "临时讲座", "period": 3, "room": "报告厅"},
    ]))

    day = day_courses(payload, "2026-11-08")
    assert [(course.id, course.period, course.room) for course in day] == [
        ("a", 1, "A-101"),
        ("b", 2, "B-202"),
        ("extra-1", 3, "报告厅"),
    ]
    assert [course.id for course in day_courses(payload, "2026-11-09")] == []


def test_duplicate_slot_and_override_contracts_are_rejected():
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(courses=[
            {"id": "a", "name": "高数", "weekday": 7, "weeks": [9], "period": 1, "room": "A-1"},
            {"id": "b", "name": "英语", "weekday": 7, "weeks": [9], "period": 1, "room": "B-1"},
        ]))

    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(overrides=[
            {"date": "2026-11-08", "course_id": "extra", "action": "add",
             "period": 3, "room": "报告厅"},
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(overrides=[
            {"date": "2026-11-08", "course_id": "extra", "action": "add",
             "name": "讲座", "period": 3},
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(overrides=[
            {"date": "2026-11-08", "course_id": "a", "action": "add",
             "name": "讲座", "period": 3, "room": "报告厅"},
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(overrides=[
            {"date": "2026-11-08", "course_id": "a", "action": "move_period",
             "period": 2, "room": "C-303"},
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(overrides=[
            {"date": "2026-11-08", "course_id": "a", "action": "move_time",
             "start": "13:00", "end": "14:40"},
        ]))
    with pytest.raises(ValidationError):
        CoursePageData.model_validate(document(overrides=[
            {"date": "2026-11-08", "course_id": "e1", "action": "add",
             "name": "讲座一", "period": 3, "room": "报告厅"},
            {"date": "2026-11-08", "course_id": "e2", "action": "add",
             "name": "讲座二", "period": 4, "room": "报告厅"},
        ]))


def test_render_shows_period_times_names_and_rooms():
    image = CoursePanel(clock=clock_at(8, 0)).render(
        document(revision=2, updated_at="2026-11-08 16:00"),
        DisplayConfig(),
        "eink",
        strict=True,
    )
    texts = texts_of(image)

    assert "第 9 周" in texts and "2026-11-08 周日" in texts
    assert "第1节 08:00-09:40" in texts
    assert "第2节 10:00-11:40" in texts
    assert "高等数学" in texts and "A-101" in texts
    assert "来源 / course r2" in texts
    assert "更新 / 2026-11-08 16:00" in texts
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    assert len(logical_to_transport(png_to_logical_raw(stream.getvalue()))) == 15000


def test_added_class_renders_with_period_time():
    data = document(overrides=[
        {"date": "2026-11-08", "course_id": "extra-1", "action": "add",
         "name": "临时讲座", "period": 3, "room": "报告厅"},
    ])
    image = CoursePanel(clock=clock_at(8, 0)).render(data, DisplayConfig(), "eink", strict=True)
    texts = texts_of(image)

    assert "临时讲座" in texts and "报告厅" in texts
    assert "第3节 14:00-15:40" in texts


def test_six_rows_fit_above_the_footer():
    rows = [
        {"id": f"c{index}", "name": f"课{index}", "weekday": 7, "weeks": [9],
         "period": index + 1, "room": f"A-{index + 1}"}
        for index in range(5)
    ]
    data = document(courses=rows, overrides=[
        {"date": "2026-11-08", "course_id": "extra-1", "action": "add",
         "name": "讲座", "period": 3, "room": "报告厅"},
    ])
    image = CoursePanel(clock=clock_at(8, 0)).render(data, DisplayConfig(), "eink", strict=True)
    texts = texts_of(image)

    assert "课4" in texts and "A-5" in texts and "讲座" in texts


def test_render_is_deterministic_and_crosses_days():
    data = document()
    morning = CoursePanel(clock=clock_at(8, 0)).render(data, DisplayConfig(), "eink", strict=True)
    night = CoursePanel(clock=clock_at(22, 0)).render(data, DisplayConfig(), "eink", strict=True)
    assert morning.tobytes() == night.tobytes()

    sunday = CoursePanel(clock=clock_at(8, 0, 8)).render(data, DisplayConfig(), "eink", strict=True)
    monday = CoursePanel(clock=clock_at(8, 0, 9)).render(data, DisplayConfig(), "eink", strict=True)
    assert "高等数学" in texts_of(sunday)
    assert "高等数学" not in texts_of(monday)
    assert "今天没有课" in texts_of(monday)


def test_outside_semester_is_explicit():
    image = CoursePanel(clock=clock_at(8, 0, 1, 6)).render(
        document(), DisplayConfig(), "eink", strict=True
    )
    texts = texts_of(image)
    assert "学期外" in texts and "今天没有课" in texts


def test_long_name_is_fitted_not_truncated():
    data = document(courses=[{
        "id": "long", "name": "课" * 24, "weekday": 7, "weeks": [9],
        "period": 1, "room": "A-101",
    }])
    image = CoursePanel(clock=clock_at(8, 0)).render(data, DisplayConfig(), "eink", strict=True)
    assert "课" * 24 in texts_of(image)


def test_factory_and_schema_contract():
    assert isinstance(create_panel("course"), CoursePanel)
    assert Course.model_validate({
        "id": "a", "name": "课", "weekday": 1, "weeks": [1],
        "period": 1, "room": "A-1",
    }).period == 1
    with pytest.raises(ValidationError):
        CourseOverride.model_validate({"date": "2026-11-08", "course_id": "a", "action": "cancel",
                                       "room": "A-1"})
    assert date.fromisoformat(SEMESTER).weekday() == 0
