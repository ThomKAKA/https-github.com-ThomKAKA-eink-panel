"""Deterministic Takeout status page renderer for the 400x300 e-ink panel."""

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
from panels.drawing import draw_frame, draw_terminal_mark, fit_font, to_eink
from panels.render_validation import CheckedDraw


SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")
_DAY_KEY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_MINUTE = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
_WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
STATUS_LABELS = {
    "waiting": "待取",
    "delivering": "配送中",
    "arrived": "已到",
    "late": "超时",
}
_STATUS_ORDER = {"late": 0, "delivering": 1, "waiting": 2, "arrived": 3}


class TakeoutOrder(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    name: str = Field(min_length=1, max_length=20)
    status: Literal["waiting", "delivering", "arrived"] = "waiting"
    expected_at: str | None = None
    note: str | None = Field(default=None, max_length=8)

    @field_validator("expected_at", "note", mode="before")
    @classmethod
    def blank_is_missing(cls, value: Any) -> Any:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value

    @field_validator("expected_at")
    @classmethod
    def expected_is_a_minute(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _MINUTE.fullmatch(value):
            raise ValueError("Invalid expected time")
        return value


class TakeoutPageData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    revision: int = Field(default=1, ge=1)
    updated_at: str | None = Field(default=None, max_length=32)
    day_key: str | None = None
    now: str | None = None
    orders: list[TakeoutOrder] = Field(default_factory=list, max_length=6)

    @field_validator("day_key")
    @classmethod
    def day_key_is_a_date(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _DAY_KEY.fullmatch(value):
            raise ValueError("Invalid day")
        date.fromisoformat(value)
        return value

    @field_validator("now")
    @classmethod
    def now_is_a_minute(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _MINUTE.fullmatch(value):
            raise ValueError("Invalid current time")
        return value

    @model_validator(mode="after")
    def identifiers_are_unique(self) -> "TakeoutPageData":
        identifiers = [order.id for order in self.orders]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Duplicate takeout identifier")
        return self


@dataclass(frozen=True)
class EffectiveOrder:
    id: str
    name: str
    status: Literal["waiting", "delivering", "arrived", "late"]
    expected_at: str | None
    note: str | None


@dataclass(frozen=True)
class NormalizedTakeout:
    data: TakeoutPageData
    weekday: str
    orders: tuple[EffectiveOrder, ...]
    state: Literal["ok"] = "ok"
    message: str = ""


def effective_status(order: TakeoutOrder, now: str | None) -> str:
    """Late is derived from the expected minute; arrived always wins."""
    if order.status == "arrived" or order.expected_at is None or now is None:
        return order.status
    return "late" if now > order.expected_at else order.status


class TakeoutPanel(BasePanel):
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or datetime.now

    def validate(self, data: Mapping[str, Any]) -> TakeoutPageData:
        return TakeoutPageData.model_validate(dict(data))

    def normalize(self, data: Mapping[str, Any]) -> NormalizedTakeout:
        raw = dict(data)
        raw.setdefault("day_key", self._today())
        payload = self.validate(raw)
        assert payload.day_key is not None
        day = date.fromisoformat(payload.day_key)
        orders = [
            EffectiveOrder(
                order.id,
                order.name,
                effective_status(order, payload.now),
                order.expected_at,
                order.note,
            )
            for order in payload.orders
        ]
        orders.sort(
            key=lambda item: (
                _STATUS_ORDER[item.status],
                item.expected_at is None,
                item.expected_at or "",
                item.id,
            )
        )
        return NormalizedTakeout(payload, _WEEKDAYS[day.weekday()], tuple(orders))

    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
        *,
        strict: bool = False,
    ) -> Image.Image:
        if config.width != 400 or config.height != 300:
            raise ValueError("TakeoutPanel is calibrated for a 400x300 display")
        if preview_mode not in {"normal", "eink"}:
            raise ValueError(f"Unknown preview mode: {preview_mode}")

        payload = self.normalize(data)
        image = Image.new("L", (config.width, config.height), WHITE)
        draw: ImageDraw.ImageDraw | CheckedDraw = ImageDraw.Draw(image)
        if strict:
            draw = CheckedDraw(draw)

        draw_frame(draw, config.width, config.height)
        draw.rectangle((PANEL_PADDING, 50, config.width - PANEL_PADDING - 1, 50), fill=BLACK)

        draw.text((PANEL_PADDING, 6), "外卖", fill=BLACK, font=get_font(FONT_LG, bold=True))
        draw.text(
            (PANEL_PADDING + 60, 12),
            "TAKEOUT",
            fill=BLACK,
            font=get_font(FONT_SM, bold=True, mono=True),
        )

        count_label = f"{len(payload.orders)}单"
        count_font = get_font(FONT_MD, bold=True)
        count_bbox = draw.textbbox((0, 0), count_label, font=count_font)
        draw.text(
            (360 - (count_bbox[2] - count_bbox[0]), 12),
            count_label,
            fill=BLACK,
            font=count_font,
        )

        day_label = f"{payload.data.day_key} {payload.weekday}"
        draw.text((PANEL_PADDING, 31), day_label, fill=BLACK, font=get_font(FONT_MD, bold=True))

        if payload.orders:
            self._draw_orders(draw, payload.orders)
        else:
            draw.text(
                (PANEL_PADDING, 112),
                "暂无外卖订单",
                fill=BLACK,
                font=get_font(FONT_MD, bold=True),
            )
            draw.text(
                (PANEL_PADDING, 138),
                "在 /manage 添加外卖单",
                fill=BLACK,
                font=get_font(FONT_SM, bold=True),
            )

        self._draw_footer(draw, payload.data)
        draw_terminal_mark(draw, config.width - PANEL_PADDING, 6)

        if preview_mode == "eink":
            image = to_eink(image)
        if strict:
            image.info["render_audit"] = {"fonts": draw.fonts, "texts": draw.texts}
        return image

    @staticmethod
    def _status_line(order: EffectiveOrder) -> str:
        label = STATUS_LABELS[order.status]
        if order.expected_at is None:
            return label
        if order.status == "arrived":
            return f"{label} · {order.expected_at}"
        return f"{label} · 预计 {order.expected_at}"

    @staticmethod
    def _draw_orders(draw: ImageDraw.ImageDraw, orders: tuple[EffectiveOrder, ...]) -> None:
        for index, order in enumerate(orders):
            y = 58 + index * 34
            draw.text(
                (PANEL_PADDING, y + 1),
                TakeoutPanel._status_line(order),
                fill=BLACK,
                font=get_font(FONT_MD, bold=True),
            )
            name_font = fit_font(
                draw,
                order.name,
                240,
                max_size=FONT_MD,
                min_size=FONT_XS,
                bold=False,
                mono=order.name.isascii(),
            )
            draw.text((PANEL_PADDING, y + 16), order.name, fill=BLACK, font=name_font)
            if order.note:
                note_font = fit_font(
                    draw,
                    order.note,
                    110,
                    max_size=FONT_SM,
                    min_size=FONT_XS,
                    bold=True,
                    mono=order.note.isascii(),
                )
                note_bbox = draw.textbbox((0, 0), order.note, font=note_font)
                draw.text(
                    (390 - (note_bbox[2] - note_bbox[0]), y + 19),
                    order.note,
                    fill=BLACK,
                    font=note_font,
                )

    @staticmethod
    def _draw_footer(draw: ImageDraw.ImageDraw, data: TakeoutPageData) -> None:
        font = get_font(FONT_SM, bold=True)
        draw.text(
            (PANEL_PADDING, 265),
            f"来源 / takeout r{data.revision}",
            fill=BLACK,
            font=font,
        )
        draw.text(
            (PANEL_PADDING, 279),
            f"更新 / {data.updated_at or '--'}",
            fill=BLACK,
            font=font,
        )

    def get_metadata(self) -> PanelMetadata:
        return PanelMetadata(
            panel_type="takeout",
            display_name="TakeoutPanel",
            description="Deterministic takeout status list with automatic overdue",
        )

    def _today(self) -> str:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=SHANGHAI)
        return value.astimezone(SHANGHAI).date().isoformat()
