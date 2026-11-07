"""Deterministic Memo page renderer for the 400x300 e-ink panel."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import re
from typing import Any, Callable, Literal, Mapping

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
_DUE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$")
_WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
_FACES = {"todo": "[ ]", "doing": "[~]", "done": "[x]", "note": "[-]"}


def _valid_date(value: str, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError("Invalid date")
    date.fromisoformat(value)
    return value


class MemoItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    text: str = Field(min_length=1, max_length=60)
    due: str | None = None
    face: Literal["todo", "doing", "done", "note"] = "todo"

    @field_validator("due", mode="before")
    @classmethod
    def blank_due_is_missing(cls, value: Any) -> Any:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value

    @field_validator("due")
    @classmethod
    def due_is_a_real_minute(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _DUE.fullmatch(value):
            raise ValueError("Invalid due time")
        datetime.strptime(value, "%Y-%m-%d %H:%M")
        return value


class MemoPageData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    revision: int = Field(default=1, ge=1)
    updated_at: str | None = Field(default=None, max_length=32)
    day_key: str | None = None
    items: list[MemoItem] = Field(default_factory=list, max_length=8)

    @field_validator("day_key")
    @classmethod
    def day_key_is_a_date(cls, value: str | None) -> str | None:
        return None if value is None else _valid_date(value, _DAY_KEY)

    @model_validator(mode="after")
    def identifiers_are_unique(self) -> "MemoPageData":
        identifiers = [item.id for item in self.items]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Duplicate memo identifier")
        return self


@dataclass(frozen=True)
class NormalizedMemo:
    data: MemoPageData
    day: date
    weekday: str
    state: Literal["ok"] = "ok"
    message: str = ""


class MemoPanel(BasePanel):
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or datetime.now

    def validate(self, data: Mapping[str, Any]) -> MemoPageData:
        return MemoPageData.model_validate(dict(data))

    def normalize(self, data: Mapping[str, Any]) -> NormalizedMemo:
        raw = dict(data)
        raw.setdefault("day_key", self._today())
        payload = self.validate(raw)
        assert payload.day_key is not None
        day = date.fromisoformat(payload.day_key)
        ordered = sorted(payload.items, key=lambda item: (item.due is None, item.due or "", item.id))
        payload = payload.model_copy(update={"items": ordered})
        return NormalizedMemo(payload, day, _WEEKDAYS[day.weekday()])

    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
        *,
        strict: bool = False,
    ) -> Image.Image:
        if config.width != 400 or config.height != 300:
            raise ValueError("MemoPanel is calibrated for a 400x300 display")
        if preview_mode not in {"normal", "eink"}:
            raise ValueError(f"Unknown preview mode: {preview_mode}")

        payload = self.normalize(data)
        image = Image.new("L", (config.width, config.height), WHITE)
        draw: ImageDraw.ImageDraw | CheckedDraw = ImageDraw.Draw(image)
        if strict:
            draw = CheckedDraw(draw)

        draw_frame(draw, config.width, config.height)
        # The divider is drawn before text so the audit can prove no glyph crosses it.
        draw.rectangle((PANEL_PADDING, 36, config.width - PANEL_PADDING - 1, 36), fill=BLACK)

        draw.text((PANEL_PADDING, 6), "备忘录", fill=BLACK, font=get_font(FONT_LG, bold=True))
        draw.text(
            (PANEL_PADDING + 64, 12),
            "MEMO",
            fill=BLACK,
            font=get_font(FONT_SM, bold=True, mono=True),
        )
        header = f"{payload.data.day_key} {payload.weekday}"
        header_font = get_font(FONT_XS, mono=False)
        header_bbox = draw.textbbox((0, 0), header, font=header_font)
        draw.text(
            (360 - (header_bbox[2] - header_bbox[0]), 12),
            header,
            fill=BLACK,
            font=header_font,
        )

        if payload.data.items:
            self._draw_items(draw, payload)
        else:
            draw.text(
                (PANEL_PADDING, 112),
                "暂无备忘",
                fill=BLACK,
                font=get_font(FONT_MD, bold=True),
            )
            draw.text(
                (PANEL_PADDING, 138),
                "在 /manage 添加事项",
                fill=BLACK,
                font=get_font(FONT_SM),
            )

        draw_footer(draw, PANEL_PADDING, 290, f"memo r{payload.data.revision}", payload.data.updated_at)
        draw_terminal_mark(draw, config.width - PANEL_PADDING, 6)

        if preview_mode == "eink":
            image = to_eink(image)
        if strict:
            image.info["render_audit"] = {"fonts": draw.fonts, "texts": draw.texts}
        return image

    @staticmethod
    def _draw_items(draw: ImageDraw.ImageDraw, payload: NormalizedMemo) -> None:
        for index, item in enumerate(payload.data.items):
            y = 44 + index * 26
            draw.text(
                (PANEL_PADDING, y + 2),
                _FACES[item.face],
                fill=BLACK,
                font=get_font(FONT_SM, bold=True, mono=True),
            )
            text = item.text
            font = fit_font(
                draw,
                text,
                256,
                max_size=FONT_MD,
                min_size=FONT_XS,
                bold=False,
                mono=text.isascii(),
            )
            draw.text((PANEL_PADDING + 26, y), text, fill=BLACK, font=font)
            due = MemoPanel._due_label(item.due, payload.day)
            due_font = get_font(FONT_XS, mono=True)
            due_bbox = draw.textbbox((0, 0), due, font=due_font)
            draw.text(
                (390 - (due_bbox[2] - due_bbox[0]), y + 4),
                due,
                fill=BLACK,
                font=due_font,
            )

    @staticmethod
    def _due_label(due: str | None, today: date) -> str:
        if due is None:
            return "--"
        due_date = datetime.strptime(due, "%Y-%m-%d %H:%M").date()
        status = "OVERDUE" if due_date < today else "TODAY" if due_date == today else "LATER"
        return f"{status} {due_date.month:02d}-{due_date.day:02d}"

    def get_metadata(self) -> PanelMetadata:
        return PanelMetadata(
            panel_type="memo",
            display_name="MemoPanel",
            description="Deterministic memo list with day-level due status",
        )

    def _today(self) -> str:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=SHANGHAI)
        return value.astimezone(SHANGHAI).date().isoformat()
