"""Compact monochrome StatsPanel renderer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Literal, Mapping

from PIL import Image, ImageDraw
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from panels.base import BasePanel, DisplayConfig, PanelMetadata
from panels.design_system import (
    BLACK,
    DIVIDER_WIDTH,
    FONT_LG,
    FONT_MD,
    FONT_NUMBER,
    FONT_SM,
    FONT_XL,
    PANEL_PADDING,
    SPACE_2,
    SPACE_3,
    STATS_BAR_HEIGHT,
    STATS_LEFT_COLUMN_RATIO,
    WHITE,
    get_font,
)
from panels.drawing import (
    current_timestamp,
    draw_footer,
    draw_frame,
    draw_terminal_mark,
    fit_font,
    to_eink,
)


class StatsBreakdownItem(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    name: str
    value: float
    unit: str = "%"


class StatsPanelData(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    panel_type: Literal["stats"] = "stats"
    title: str = "TODAY TOKEN"
    primary_value: str | None = None
    primary_label: str = "TODAY TOKEN"
    secondary_value: str = ""
    secondary_label: str = "TOTAL TOKEN"
    cost: str = ""
    breakdown: list[StatsBreakdownItem] = Field(default_factory=list)
    updated_at: str | None = None
    source: str = ""

    @field_validator("primary_value", "updated_at", mode="before")
    @classmethod
    def blank_value_is_missing(cls, value: Any) -> Any:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value


@dataclass(frozen=True)
class NormalizedStats:
    data: StatsPanelData
    state: Literal["ok", "waiting", "error"] = "ok"
    message: str = ""


class StatsPanel(BasePanel):
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or datetime.now

    def validate(self, data: Mapping[str, Any]) -> StatsPanelData:
        return StatsPanelData.model_validate(dict(data))

    def normalize(self, data: Mapping[str, Any]) -> NormalizedStats:
        raw = dict(data)
        if raw.get("updated_at") is None or not str(raw.get("updated_at", "")).strip():
            raw["updated_at"] = current_timestamp(self._clock)

        try:
            normalized = self.validate(raw)
        except ValidationError:
            failed = StatsPanelData(
                title=str(raw.get("title") or "TODAY TOKEN"),
                primary_value="NO DATA",
                primary_label="TODAY TOKEN",
                updated_at=str(raw["updated_at"]),
                source=str(raw.get("source") or ""),
            )
            return NormalizedStats(failed, state="error", message="NO DATA")

        if normalized.primary_value is None:
            waiting = normalized.model_copy(
                update={
                    "primary_value": "NO DATA",
                    "secondary_value": normalized.secondary_value or "--",
                }
            )
            return NormalizedStats(waiting, state="waiting", message="NO DATA")

        return NormalizedStats(normalized)

    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
    ) -> Image.Image:
        if config.width != 400 or config.height != 300:
            raise ValueError("Phase 2 StatsPanel is calibrated for a 400x300 display")
        if preview_mode not in {"normal", "eink"}:
            raise ValueError(f"Unknown preview mode: {preview_mode}")

        payload = self.normalize(data)
        image = Image.new("L", (config.width, config.height), WHITE)
        draw = ImageDraw.Draw(image)
        draw_frame(draw, config.width, config.height)

        x = PANEL_PADDING
        y = PANEL_PADDING
        width = config.width - PANEL_PADDING * 2
        height = config.height - PANEL_PADDING * 2
        divider_x = x + round(width * STATS_LEFT_COLUMN_RATIO)
        left_right = divider_x - SPACE_3
        right_x = divider_x + SPACE_3
        right_edge = x + width

        draw.line(
            (divider_x, y + 28, divider_x, y + height - 36),
            fill=BLACK,
            width=DIVIDER_WIDTH,
        )
        draw_terminal_mark(draw, right_edge, y)
        self._draw_left(draw, payload.data, x + SPACE_3, y, left_right)
        self._draw_breakdown(draw, payload.data, right_x, y, right_edge)
        draw_footer(draw, right_x, y + height, payload.data.source, payload.data.updated_at)

        return to_eink(image) if preview_mode == "eink" else image

    def get_metadata(self) -> PanelMetadata:
        return PanelMetadata(
            panel_type="stats",
            display_name="StatsPanel",
            description="Compact primary statistics and breakdown panel",
        )

    @staticmethod
    def _draw_left(
        draw: ImageDraw.ImageDraw,
        data: StatsPanelData,
        x: int,
        y: int,
        right_edge: int,
    ) -> None:
        available = right_edge - x
        primary_label = data.primary_label or data.title
        draw.text(
            (x, y + 12),
            primary_label.upper(),
            fill=BLACK,
            font=get_font(FONT_SM, bold=True, mono=True),
        )

        primary = data.primary_value or "NO DATA"
        primary_font = fit_font(
            draw,
            primary,
            available,
            max_size=44,
            min_size=FONT_XL,
        )
        draw.text((x - 1, y + 38), primary, fill=BLACK, font=primary_font)

        cost = data.cost or "--"
        draw.text(
            (x, y + 96),
            f"COST {cost}",
            fill=BLACK,
            font=get_font(FONT_MD, bold=True, mono=True),
        )
        divider_y = y + 129
        draw.line((x, divider_y, right_edge, divider_y), fill=BLACK, width=DIVIDER_WIDTH)

        draw.text(
            (x, y + 142),
            (data.secondary_label or "TOTAL TOKEN").upper(),
            fill=BLACK,
            font=get_font(FONT_SM, bold=True, mono=True),
        )
        secondary = data.secondary_value or "--"
        secondary_font = fit_font(
            draw,
            secondary,
            available,
            max_size=34,
            min_size=FONT_XL,
        )
        draw.text((x - 1, y + 166), secondary, fill=BLACK, font=secondary_font)

    @staticmethod
    def _draw_breakdown(
        draw: ImageDraw.ImageDraw,
        data: StatsPanelData,
        x: int,
        y: int,
        right_edge: int,
    ) -> None:
        draw.text(
            (x, y + 30),
            "MODEL SHARE",
            fill=BLACK,
            font=get_font(FONT_LG, bold=True, mono=True),
        )
        rows = data.breakdown[:4]
        if not rows:
            draw.text(
                (x, y + 77),
                "NO DATA",
                fill=BLACK,
                font=get_font(FONT_MD, bold=True, mono=True),
            )
            return

        label_font = get_font(FONT_SM, bold=True, mono=True)
        value_font = get_font(FONT_SM, mono=True)
        bar_x = x + 73
        bar_max_width = 58
        value_right = right_edge
        for index, item in enumerate(rows):
            row_y = y + 79 + index * 38
            name = item.name[:10]
            draw.text((x, row_y), name, fill=BLACK, font=label_font)
            ratio = min(max(item.value, 0.0), 100.0) / 100.0
            bar_width = round(bar_max_width * ratio)
            if bar_width > 0:
                draw.rectangle(
                    (bar_x, row_y + 1, bar_x + bar_width - 1, row_y + STATS_BAR_HEIGHT),
                    fill=BLACK,
                )
            value = f"{item.value:g}{item.unit}"
            bbox = draw.textbbox((0, 0), value, font=value_font)
            draw.text(
                (value_right - (bbox[2] - bbox[0]), row_y),
                value,
                fill=BLACK,
                font=value_font,
            )
