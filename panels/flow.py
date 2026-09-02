"""Compact monochrome FlowPanel renderer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Literal, Mapping

from PIL import Image, ImageDraw
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from panels.base import BasePanel, DisplayConfig, PanelMetadata
from panels.design_system import (
    BLACK,
    BORDER_NORMAL,
    BORDER_THIN,
    FLOW_LEFT_COLUMN_RATIO,
    FLOW_NODE_ACTIVE,
    FLOW_NODE_DONE,
    FLOW_NODE_PENDING,
    FONT_MD,
    FONT_NUMBER,
    FONT_SM,
    FONT_XL,
    PANEL_PADDING,
    SPACE_2,
    SPACE_3,
    TAG_HEIGHT,
    WHITE,
    get_font,
)
from panels.drawing import (
    current_timestamp,
    draw_filled_tag,
    draw_footer,
    draw_frame,
    draw_terminal_mark,
    fit_font,
    to_eink,
)


StageStatus = Literal["done", "active", "pending", "error"]


class FlowStage(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    name: str
    status: StageStatus = "pending"


class FlowPanelData(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    panel_type: Literal["flow"] = "flow"
    title: str = "正在送达"
    category: str = "DELIVERY"
    eta: str | None = None
    eta_unit: str = "分钟"
    distance: str = ""
    description: str = ""
    current_stage: int = Field(default=0, ge=0)
    stages: list[FlowStage] = Field(default_factory=list)
    updated_at: str | None = None
    source: str = ""

    @field_validator("eta", mode="before")
    @classmethod
    def normalize_eta(cls, value: Any) -> Any:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return str(value)

    @field_validator("updated_at", mode="before")
    @classmethod
    def blank_time_is_missing(cls, value: Any) -> Any:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value


@dataclass(frozen=True)
class NormalizedFlow:
    data: FlowPanelData
    state: Literal["ok", "waiting", "error"] = "ok"
    message: str = ""


class FlowPanel(BasePanel):
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or datetime.now

    def validate(self, data: Mapping[str, Any]) -> FlowPanelData:
        return FlowPanelData.model_validate(dict(data))

    def normalize(self, data: Mapping[str, Any]) -> NormalizedFlow:
        raw = dict(data)
        if raw.get("updated_at") is None or not str(raw.get("updated_at", "")).strip():
            raw["updated_at"] = current_timestamp(self._clock)

        try:
            normalized = self.validate(raw)
        except ValidationError:
            failed = FlowPanelData(
                title="ERROR",
                eta="--",
                description="WAITING FLOW DATA",
                stages=[FlowStage(name="ERROR", status="error")],
                updated_at=str(raw["updated_at"]),
                source=str(raw.get("source") or ""),
            )
            return NormalizedFlow(failed, state="error", message="ERROR")

        if normalized.eta is None or not normalized.stages:
            waiting = normalized.model_copy(
                update={
                    "title": "WAITING",
                    "eta": "--",
                    "description": "WAITING FLOW DATA",
                    "stages": [],
                }
            )
            return NormalizedFlow(
                waiting,
                state="waiting",
                message="WAITING FLOW DATA",
            )

        return NormalizedFlow(normalized)

    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
    ) -> Image.Image:
        if config.width != 400 or config.height != 300:
            raise ValueError("Phase 2 FlowPanel is calibrated for a 400x300 display")
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
        left_width = round(width * FLOW_LEFT_COLUMN_RATIO)
        right_x = x + left_width + SPACE_3
        right_edge = x + width

        self._draw_eta(draw, payload.data, x, y, left_width, height)
        self._draw_flow(draw, payload.data, right_x, y, right_edge, height)

        return to_eink(image) if preview_mode == "eink" else image

    def get_metadata(self) -> PanelMetadata:
        return PanelMetadata(
            panel_type="flow",
            display_name="FlowPanel",
            description="Compact ETA and staged process status panel",
        )

    @staticmethod
    def _draw_eta(
        draw: ImageDraw.ImageDraw,
        data: FlowPanelData,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        draw.rectangle((x, y, x + width - 1, y + height - 1), fill=BLACK)
        inner_x = x + SPACE_3
        inner_right = x + width - SPACE_3
        draw.text(
            (inner_x, y + 13),
            (data.category or "FLOW").upper(),
            fill=WHITE,
            font=get_font(FONT_SM, bold=True, mono=True),
        )

        eta = data.eta or "--"
        unit = data.eta_unit or ""
        unit_font = get_font(FONT_XL, bold=True)
        unit_bbox = draw.textbbox((0, 0), unit, font=unit_font)
        unit_width = unit_bbox[2] - unit_bbox[0]
        eta_font = fit_font(
            draw,
            eta,
            max(inner_right - inner_x - unit_width - SPACE_2, 36),
            max_size=FONT_NUMBER,
            min_size=FONT_XL,
        )
        eta_y = y + 52
        draw.text((inner_x - 2, eta_y), eta, fill=WHITE, font=eta_font)
        eta_bbox = draw.textbbox((inner_x - 2, eta_y), eta, font=eta_font)
        unit_y = eta_bbox[3] - unit_bbox[3]
        draw.text((eta_bbox[2] + SPACE_2, unit_y), unit, fill=WHITE, font=unit_font)

        strip_x = inner_x
        strip_y = y + height - 48
        strip_width = inner_right - inner_x
        strip_height = 30
        draw.rectangle(
            (strip_x, strip_y, strip_x + strip_width, strip_y + strip_height),
            fill=WHITE,
        )
        description = data.description or "WAITING FLOW DATA"
        description_font = fit_font(
            draw,
            description,
            strip_width - SPACE_2 * 2,
            max_size=FONT_MD,
            min_size=FONT_SM,
            mono=False,
        )
        bbox = draw.textbbox((0, 0), description, font=description_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            (strip_x + (strip_width - text_width) // 2, strip_y + 5),
            description,
            fill=BLACK,
            font=description_font,
        )

    @staticmethod
    def _draw_flow(
        draw: ImageDraw.ImageDraw,
        data: FlowPanelData,
        x: int,
        y: int,
        right_edge: int,
        height: int,
    ) -> None:
        draw_terminal_mark(draw, right_edge, y)
        title_font = get_font(FONT_MD, bold=True)
        draw_filled_tag(
            draw,
            x,
            y,
            data.title,
            height=TAG_HEIGHT,
            font=title_font,
            max_width=max(right_edge - x - 42, 60),
        )
        distance = data.distance or "--"
        draw.text(
            (x, y + 34),
            f"距离约 {distance}",
            fill=BLACK,
            font=get_font(FONT_MD, bold=True),
        )

        stages = data.stages[:4]
        if not stages:
            draw.text(
                (x, y + 94),
                "WAITING FLOW DATA",
                fill=BLACK,
                font=get_font(FONT_SM, bold=True, mono=True),
            )
        else:
            node_y = y + 119
            available = right_edge - x
            if len(stages) == 1:
                centers = [x + available // 2]
            else:
                centers = [
                    x + round(index * available / (len(stages) - 1))
                    for index in range(len(stages))
                ]
                centers[0] += FLOW_NODE_ACTIVE // 2
                centers[-1] -= FLOW_NODE_ACTIVE // 2

            for start, end in zip(centers, centers[1:]):
                FlowPanel._draw_dashed_connector(draw, start + 14, end - 14, node_y)
            for center_x, stage in zip(centers, stages):
                FlowPanel._draw_stage(draw, center_x, node_y, stage)

        draw_footer(draw, x, y + height, data.source, data.updated_at)

    @staticmethod
    def _draw_dashed_connector(
        draw: ImageDraw.ImageDraw,
        start_x: int,
        end_x: int,
        y: int,
    ) -> None:
        cursor = start_x
        while cursor < end_x:
            draw.line((cursor, y, min(cursor + 6, end_x), y), fill=BLACK, width=2)
            cursor += 11

    @staticmethod
    def _draw_stage(
        draw: ImageDraw.ImageDraw,
        center_x: int,
        center_y: int,
        stage: FlowStage,
    ) -> None:
        if stage.status == "active":
            size = FLOW_NODE_ACTIVE
        elif stage.status == "done":
            size = FLOW_NODE_DONE
        else:
            size = FLOW_NODE_PENDING

        left = center_x - size // 2
        top = center_y - size // 2
        box = (left, top, left + size, top + size)
        if stage.status in {"done", "active"}:
            draw.rectangle(box, fill=BLACK)
        else:
            draw.rectangle(box, outline=BLACK, width=BORDER_NORMAL)

        label = stage.name
        if stage.status == "error":
            draw.line((left + 4, top + 4, left + size - 4, top + size - 4), fill=BLACK, width=BORDER_THIN)
            draw.line((left + size - 4, top + 4, left + 4, top + size - 4), fill=BLACK, width=BORDER_THIN)
            label = "ERROR"

        font = get_font(FONT_SM, bold=True)
        bbox = draw.textbbox((0, 0), label, font=font)
        draw.text(
            (center_x - (bbox[2] - bbox[0]) // 2, center_y + 24),
            label,
            fill=BLACK,
            font=font,
        )
