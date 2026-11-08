"""Deterministic month calendar renderer with lunar dates and solar terms."""

from __future__ import annotations

import calendar as month_calendar
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal, Mapping

from PIL import Image, ImageDraw
from pydantic import BaseModel, ConfigDict, Field, field_validator

from panels.almanac import cell_label, festival, lunar_date, solar_terms
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
from panels.drawing import draw_frame, draw_terminal_mark, to_eink
from panels.render_validation import CheckedDraw


WEEKDAY_HEADERS = ("一", "二", "三", "四", "五", "六", "日")
WEEKDAY_NAMES = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
GRID_LEFT = 8
CELL_WIDTH = 55
GRID_TOP = 54
GRID_BOTTOM = 238


class CalendarPageData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    revision: int = Field(default=1, ge=1)
    updated_at: str | None = Field(default=None, max_length=32)
    day_key: str

    @field_validator("day_key")
    @classmethod
    def day_key_is_a_date(cls, value: str) -> str:
        if len(value) != 10:
            raise ValueError("Invalid day key")
        date.fromisoformat(value)
        return value


@dataclass(frozen=True)
class NormalizedCalendar:
    data: CalendarPageData
    day: date
    state: Literal["ok"] = "ok"
    message: str = ""


class CalendarPanel(BasePanel):
    """Render the month that contains ``day_key`` and highlight that day."""

    def validate(self, data: Mapping[str, Any]) -> CalendarPageData:
        return CalendarPageData.model_validate(dict(data))

    def normalize(self, data: Mapping[str, Any]) -> NormalizedCalendar:
        payload = self.validate(data)
        return NormalizedCalendar(payload, date.fromisoformat(payload.day_key))

    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
        *,
        strict: bool = False,
    ) -> Image.Image:
        if config.width != 400 or config.height != 300:
            raise ValueError("CalendarPanel is calibrated for a 400x300 display")
        if preview_mode not in {"normal", "eink"}:
            raise ValueError(f"Unknown preview mode: {preview_mode}")

        payload = self.normalize(data)
        image = Image.new("L", (config.width, config.height), WHITE)
        draw: ImageDraw.ImageDraw | CheckedDraw = ImageDraw.Draw(image)
        if strict:
            draw = CheckedDraw(draw)

        draw_frame(draw, config.width, config.height)
        draw.rectangle(
            (PANEL_PADDING, 36, config.width - PANEL_PADDING - 1, 36), fill=BLACK
        )

        self._draw_header(draw, payload)
        self._draw_weekdays(draw)
        self._draw_grid(draw, payload)
        self._draw_today(draw, payload)

        self._draw_footer(draw, payload.data)
        draw_terminal_mark(draw, config.width - PANEL_PADDING, 6)

        if preview_mode == "eink":
            image = to_eink(image)
        if strict:
            image.info["render_audit"] = {"fonts": draw.fonts, "texts": draw.texts}
        return image

    @staticmethod
    def _draw_header(draw: ImageDraw.ImageDraw, payload: NormalizedCalendar) -> None:
        draw.text((PANEL_PADDING, 6), "日历", fill=BLACK, font=get_font(FONT_LG, bold=True))
        draw.text(
            (PANEL_PADDING + 52, 12),
            "CALENDAR",
            fill=BLACK,
            font=get_font(FONT_SM, bold=True, mono=True),
        )
        header = f"{payload.day.year}年{payload.day.month}月"
        font = get_font(FONT_SM, bold=True)
        bbox = draw.textbbox((0, 0), header, font=font)
        draw.text((360 - (bbox[2] - bbox[0]), 12), header, fill=BLACK, font=font)

    @staticmethod
    def _draw_weekdays(draw: ImageDraw.ImageDraw) -> None:
        font = get_font(FONT_XS, bold=True)
        for column, name in enumerate(WEEKDAY_HEADERS):
            bbox = draw.textbbox((0, 0), name, font=font)
            x = GRID_LEFT + column * CELL_WIDTH + (CELL_WIDTH - (bbox[2] - bbox[0])) // 2
            draw.text((x, 41), name, fill=BLACK, font=font)

    @staticmethod
    def _row_bounds(rows: int) -> list[tuple[int, int]]:
        span = GRID_BOTTOM - GRID_TOP
        return [
            (
                GRID_TOP + round(index * span / rows),
                GRID_TOP + round((index + 1) * span / rows),
            )
            for index in range(rows)
        ]

    def _draw_grid(self, draw: ImageDraw.ImageDraw, payload: NormalizedCalendar) -> None:
        day = payload.day
        first = day.replace(day=1)
        days_in_month = month_calendar.monthrange(first.year, first.month)[1]
        lead = first.weekday()
        rows = -(-(lead + days_in_month) // 7)
        bounds = self._row_bounds(rows)

        number_font = get_font(FONT_MD, bold=True, mono=True)
        today_font = get_font(FONT_LG, bold=True, mono=True)
        label_font = get_font(FONT_XS)
        for row, (top, bottom) in enumerate(bounds):
            height = bottom - top
            for column in range(7):
                x = GRID_LEFT + column * CELL_WIDTH
                self._draw_cell(
                    draw,
                    x,
                    top,
                    bottom,
                    day,
                    row,
                    column,
                    lead,
                    days_in_month,
                    number_font,
                    today_font,
                    label_font,
                    height,
                )

    def _draw_cell(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        top: int,
        bottom: int,
        day: date,
        row: int,
        column: int,
        lead: int,
        days_in_month: int,
        number_font: Any,
        today_font: Any,
        label_font: Any,
        height: int,
    ) -> None:
        box = (x, top, x + CELL_WIDTH - 1, bottom - 1)
        index = row * 7 + column - lead
        if not 0 <= index < days_in_month:
            draw.rectangle(box, outline=BLACK, width=1)
            return

        current = day.replace(day=index + 1)
        number = str(index + 1)
        if current == day:
            # A filled cell keeps the date visible; the lunar date is in the
            # footer line, because an 8 px white glyph does not survive 1-bit.
            draw.rectangle(box, fill=BLACK)
            font = today_font
            bbox = draw.textbbox((0, 0), number, font=font)
            draw.text(
                (x + (CELL_WIDTH - (bbox[2] - bbox[0])) // 2, top + height // 2 - 12),
                number,
                fill=WHITE,
                font=font,
            )
            return

        draw.rectangle(box, outline=BLACK, width=1)
        draw.text((x + 6, top + height // 2 - 10), number, fill=BLACK, font=number_font)
        draw.text((x + 4, bottom - 12), cell_label(current), fill=BLACK, font=label_font)

    @staticmethod
    def _draw_footer(draw: ImageDraw.ImageDraw, data: CalendarPageData) -> None:
        # The shared 8 px gray footer is too thin on the physical panel.
        font = get_font(FONT_SM, bold=True)
        draw.text(
            (PANEL_PADDING, 262),
            f"来源 / 日历 r{data.revision}",
            fill=BLACK,
            font=font,
        )
        draw.text(
            (PANEL_PADDING, 277),
            f"更新 / {data.updated_at or '按当天日期渲染'}",
            fill=BLACK,
            font=font,
        )

    @staticmethod
    def _draw_today(draw: ImageDraw.ImageDraw, payload: NormalizedCalendar) -> None:
        day = payload.day
        _, leap, _, day_label, month_name = lunar_date(day)
        lunar_text = ("闰" if leap else "") + month_name + day_label
        detail = festival(day) or solar_terms(day.year).get(day) or ""
        line = f"今日 {day.isoformat()} {WEEKDAY_NAMES[day.weekday()]} 农历{lunar_text}"
        if detail:
            line += f" {detail}"
        draw.text((PANEL_PADDING, 244), line, fill=BLACK, font=get_font(FONT_XS))

    def get_metadata(self) -> PanelMetadata:
        return PanelMetadata(
            panel_type="calendar",
            display_name="CalendarPanel",
            description="Deterministic month grid with lunar dates and solar terms",
        )
