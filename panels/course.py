"""Deterministic Course (timetable) page renderer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import re
from typing import Any, Callable, Literal, Mapping, Sequence

from PIL import Image, ImageDraw
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from panels.base import BasePanel, DisplayConfig, PanelMetadata
from panels.design_system import (
    BLACK,
    FONT_LG,
    FONT_MD,
    FONT_SM,
    FONT_XS,
    PANEL_PADDING,
    WHITE,
    get_font,
)
from panels.drawing import draw_footer, draw_frame, draw_terminal_mark, fit_font, to_eink
from panels.render_validation import CheckedDraw


SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")
_DAY_KEY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_TIME = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
_WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")


def _as_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not _DAY_KEY.fullmatch(value):
        raise ValueError("Invalid date")
    return date.fromisoformat(value)


def _time_order(start: str, end: str) -> None:
    if not _TIME.fullmatch(start) or not _TIME.fullmatch(end) or start >= end:
        raise ValueError("Invalid course time range")


def parse_weeks(text: str, total_weeks: int = 30) -> list[int]:
    """Expand ``1-8,10`` into an explicit, sorted, duplicate-free week list."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Weeks are required")
    values: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            raise ValueError("Empty week segment")
        if "-" in part:
            if part.count("-") != 1:
                raise ValueError("Invalid week range")
            start, end = part.split("-")
            first, last = int(start), int(end)
            if first > last:
                raise ValueError("Reversed week range")
            values.extend(range(first, last + 1))
        else:
            values.append(int(part))
    if any(value < 1 or value > total_weeks for value in values):
        raise ValueError("Week outside semester")
    if len(values) != len(set(values)):
        raise ValueError("Duplicate week")
    return sorted(values)


def course_week(semester_start: str | date, total_weeks: int, day: str | date) -> int | None:
    start = _as_date(semester_start)
    current = _as_date(day)
    if current < start:
        return None
    week = (current - start).days // 7 + 1
    return week if week <= total_weeks else None


class Course(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    name: str = Field(min_length=1, max_length=24)
    weekday: int = Field(ge=1, le=7)
    weeks: list[int] = Field(min_length=1, max_length=30)
    start: str
    end: str
    room: str = Field(min_length=1, max_length=16)

    @field_validator("start", "end")
    @classmethod
    def clock_time(cls, value: str) -> str:
        if not _TIME.fullmatch(value):
            raise ValueError("Invalid clock time")
        return value

    @field_validator("weeks")
    @classmethod
    def weeks_are_bounded(cls, value: list[int]) -> list[int]:
        if any(type(week) is not int or not 1 <= week <= 30 for week in value):
            raise ValueError("Invalid week")
        if len(value) != len(set(value)):
            raise ValueError("Duplicate week")
        return sorted(value)

    @model_validator(mode="after")
    def ordered_clock(self) -> "Course":
        _time_order(self.start, self.end)
        return self


class CourseOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    date: str
    course_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    action: Literal["cancel", "move_room", "move_time"]
    room: str | None = Field(default=None, min_length=1, max_length=16)
    start: str | None = None
    end: str | None = None

    @field_validator("date")
    @classmethod
    def valid_day(cls, value: str) -> str:
        return _as_date(value).isoformat()

    @field_validator("start", "end")
    @classmethod
    def optional_clock_time(cls, value: str | None) -> str | None:
        if value is not None and not _TIME.fullmatch(value):
            raise ValueError("Invalid clock time")
        return value

    @model_validator(mode="after")
    def action_matches_fields(self) -> "CourseOverride":
        if self.action == "cancel" and (self.room or self.start or self.end):
            raise ValueError("Cancel takes no replacement fields")
        if self.action == "move_room" and (self.room is None or self.start or self.end):
            raise ValueError("Room move requires only a room")
        if self.action == "move_time":
            if self.start is None or self.end is None or self.room is not None:
                raise ValueError("Time move requires only a time range")
            _time_order(self.start, self.end)
        return self


class CoursePageData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    revision: int = Field(default=1, ge=1)
    updated_at: str | None = Field(default=None, max_length=32)
    day_key: str | None = None
    semester_start: str
    total_weeks: int = Field(ge=1, le=30)
    courses: list[Course] = Field(default_factory=list, max_length=12)
    overrides: list[CourseOverride] = Field(default_factory=list, max_length=16)

    @field_validator("day_key")
    @classmethod
    def day_key_is_a_date(cls, value: str | None) -> str | None:
        return None if value is None else _as_date(value).isoformat()

    @field_validator("semester_start")
    @classmethod
    def semester_is_a_date(cls, value: str) -> str:
        return _as_date(value).isoformat()

    @model_validator(mode="after")
    def document_is_consistent(self) -> "CoursePageData":
        identifiers = [course.id for course in self.courses]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Duplicate course identifier")
        if any(week > self.total_weeks for course in self.courses for week in course.weeks):
            raise ValueError("Week outside semester")
        capacity: dict[tuple[int, int], int] = {}
        for course in self.courses:
            for week in course.weeks:
                key = (course.weekday, week)
                capacity[key] = capacity.get(key, 0) + 1
        if any(count > 8 for count in capacity.values()):
            raise ValueError("Too many courses for one day")
        days = [(override.date, override.course_id) for override in self.overrides]
        if len(days) != len(set(days)):
            raise ValueError("Duplicate override")
        return self


@dataclass(frozen=True)
class EffectiveCourse:
    id: str
    name: str
    start: str
    end: str
    room: str


@dataclass(frozen=True)
class NormalizedCourse:
    data: CoursePageData
    day: date
    weekday: str
    week: int | None
    courses: tuple[EffectiveCourse, ...]
    state: Literal["ok"] = "ok"
    message: str = ""


def day_courses(document: CoursePageData, day: str | date) -> list[EffectiveCourse]:
    current = _as_date(day)
    week = course_week(document.semester_start, document.total_weeks, current)
    if week is None:
        return []
    weekday = current.isoweekday()
    overrides = {
        override.course_id: override
        for override in document.overrides
        if override.date == current.isoformat()
    }
    effective: list[EffectiveCourse] = []
    for course in document.courses:
        if course.weekday != weekday or week not in course.weeks:
            continue
        override = overrides.get(course.id)
        start, end, room = course.start, course.end, course.room
        if override is not None:
            if override.action == "cancel":
                continue
            if override.action == "move_room":
                room = override.room or room
            else:
                start = override.start or start
                end = override.end or end
        effective.append(EffectiveCourse(course.id, course.name, start, end, room))
    effective.sort(key=lambda item: (item.start, item.end, item.id))
    return effective


class CoursePanel(BasePanel):
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or datetime.now

    def validate(self, data: Mapping[str, Any]) -> CoursePageData:
        return CoursePageData.model_validate(dict(data))

    def normalize(self, data: Mapping[str, Any]) -> NormalizedCourse:
        raw = dict(data)
        raw.setdefault("day_key", self._today())
        payload = self.validate(raw)
        assert payload.day_key is not None
        day = date.fromisoformat(payload.day_key)
        week = course_week(payload.semester_start, payload.total_weeks, day)
        return NormalizedCourse(
            payload,
            day,
            _WEEKDAYS[day.weekday()],
            week,
            tuple(day_courses(payload, day)),
        )

    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
        *,
        strict: bool = False,
    ) -> Image.Image:
        if config.width != 400 or config.height != 300:
            raise ValueError("CoursePanel is calibrated for a 400x300 display")
        if preview_mode not in {"normal", "eink"}:
            raise ValueError(f"Unknown preview mode: {preview_mode}")

        payload = self.normalize(data)
        image = Image.new("L", (config.width, config.height), WHITE)
        draw: ImageDraw.ImageDraw | CheckedDraw = ImageDraw.Draw(image)
        if strict:
            draw = CheckedDraw(draw)

        draw_frame(draw, config.width, config.height)
        draw.rectangle((PANEL_PADDING, 50, config.width - PANEL_PADDING - 1, 50), fill=BLACK)

        draw.text((PANEL_PADDING, 6), "课程表", fill=BLACK, font=get_font(FONT_LG, bold=True))
        draw.text(
            (PANEL_PADDING + 74, 12),
            "COURSE",
            fill=BLACK,
            font=get_font(FONT_SM, bold=True, mono=True),
        )
        week_label = f"第 {payload.week} 周" if payload.week is not None else "学期外"
        week_font = get_font(FONT_SM, bold=True)
        week_bbox = draw.textbbox((0, 0), week_label, font=week_font)
        draw.text((360 - (week_bbox[2] - week_bbox[0]), 12), week_label, fill=BLACK, font=week_font)

        day_label = f"{payload.data.day_key} {payload.weekday}"
        draw.text((PANEL_PADDING, 32), day_label, fill=BLACK, font=get_font(FONT_XS))
        count_label = f"{len(payload.courses)} 门课"
        count_font = get_font(FONT_XS)
        count_bbox = draw.textbbox((0, 0), count_label, font=count_font)
        draw.text((360 - (count_bbox[2] - count_bbox[0]), 32), count_label, fill=BLACK, font=count_font)

        if payload.courses:
            self._draw_courses(draw, payload.courses)
        else:
            draw.text(
                (PANEL_PADDING, 112),
                "今天没有课",
                fill=BLACK,
                font=get_font(FONT_MD, bold=True),
            )
            draw.text(
                (PANEL_PADDING, 138),
                "在 /manage 编辑课表",
                fill=BLACK,
                font=get_font(FONT_SM),
            )

        draw_footer(
            draw, PANEL_PADDING, 290, f"course r{payload.data.revision}", payload.data.updated_at
        )
        draw_terminal_mark(draw, config.width - PANEL_PADDING, 6)

        if preview_mode == "eink":
            image = to_eink(image)
        if strict:
            image.info["render_audit"] = {"fonts": draw.fonts, "texts": draw.texts}
        return image

    @staticmethod
    def _draw_courses(draw: ImageDraw.ImageDraw, courses: Sequence[EffectiveCourse]) -> None:
        for index, course in enumerate(courses):
            y = 58 + index * 26
            draw.text(
                (PANEL_PADDING, y + 2),
                f"{course.start}-{course.end}",
                fill=BLACK,
                font=get_font(FONT_XS, bold=True, mono=True),
            )
            name_font = fit_font(
                draw,
                course.name,
                200,
                max_size=FONT_MD,
                min_size=FONT_XS,
                bold=False,
                mono=course.name.isascii(),
            )
            draw.text((PANEL_PADDING + 62, y), course.name, fill=BLACK, font=name_font)
            room_font = fit_font(
                draw,
                course.room,
                88,
                max_size=FONT_XS,
                min_size=FONT_XS,
                bold=True,
                mono=course.room.isascii(),
            )
            room_bbox = draw.textbbox((0, 0), course.room, font=room_font)
            draw.text(
                (390 - (room_bbox[2] - room_bbox[0]), y + 2),
                course.room,
                fill=BLACK,
                font=room_font,
            )

    def get_metadata(self) -> PanelMetadata:
        return PanelMetadata(
            panel_type="course",
            display_name="CoursePanel",
            description="Deterministic daily timetable with per-date overrides",
        )

    def _today(self) -> str:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=SHANGHAI)
        return value.astimezone(SHANGHAI).date().isoformat()
