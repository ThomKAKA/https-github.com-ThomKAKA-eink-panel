"""Compact industrial ProgressPanel renderer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Literal, Mapping

from PIL import Image, ImageDraw
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from panels.base import BasePanel, DisplayConfig, PanelMetadata
from panels.render_validation import CheckedDraw
from panels.design_system import (
    BLACK,
    BORDER_THIN,
    CONTENT_GAP,
    FONT_MD,
    FONT_NUMBER,
    FONT_SM,
    FONT_XL,
    FONT_XS,
    LEFT_COLUMN_RATIO,
    PANEL_PADDING,
    PROGRESS_HEIGHT,
    SPACE_1,
    SPACE_2,
    SPACE_3,
    SPACE_4,
    TAG_HEIGHT,
    WHITE,
    get_font,
)
from panels.drawing import (
    current_timestamp,
    draw_footer,
    draw_frame,
    draw_terminal_mark,
    to_eink,
)


class ProgressPanelData(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    title: str = "CODING"
    progress: int | None = Field(default=None, ge=0, le=100)
    current_step: str = ""
    status: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    updated_at: str | None = None
    source: str = ""

    @field_validator("updated_at", mode="before")
    @classmethod
    def empty_time_is_missing(cls, value: Any) -> Any:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value


@dataclass(frozen=True)
class NormalizedProgress:
    data: ProgressPanelData
    state: Literal["ok", "waiting", "error"] = "ok"
    message: str = ""


class ProgressPanel(BasePanel):
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or datetime.now

    def validate(self, data: Mapping[str, Any]) -> ProgressPanelData:
        return ProgressPanelData.model_validate(dict(data))

    def normalize(self, data: Mapping[str, Any]) -> NormalizedProgress:
        raw = dict(data)
        if not raw:
            waiting = ProgressPanelData(
                title="CODING",
                progress=0,
                status="WAITING DATA",
                description="等待进度数据",
                updated_at=self._current_time(),
            )
            return NormalizedProgress(waiting, state="waiting", message="WAITING DATA")

        if raw.get("updated_at") is None or not str(raw.get("updated_at", "")).strip():
            raw["updated_at"] = self._current_time()

        try:
            normalized = self.validate(raw)
        except ValidationError:
            failed = ProgressPanelData(
                title=str(raw.get("title") or "CODING"),
                progress=0,
                status="UPDATE FAILED",
                description="进度数据格式错误",
                updated_at=str(raw["updated_at"]),
                source=str(raw.get("source") or ""),
            )
            return NormalizedProgress(failed, state="error", message="UPDATE FAILED")

        if normalized.progress is None:
            waiting = normalized.model_copy(
                update={
                    "progress": 0,
                    "status": "WAITING DATA",
                    "description": normalized.description or "等待进度数据",
                }
            )
            return NormalizedProgress(waiting, state="waiting", message="WAITING DATA")

        return NormalizedProgress(normalized)

    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
        *,
        strict: bool = False,
    ) -> Image.Image:
        if config.width != 400 or config.height != 300:
            raise ValueError("Phase 1 ProgressPanel is calibrated for a 400x300 display")
        if preview_mode not in {"normal", "eink"}:
            raise ValueError(f"Unknown preview mode: {preview_mode}")

        payload = self.normalize(data)
        image = Image.new("L", (config.width, config.height), WHITE)
        draw = ImageDraw.Draw(image)
        if strict:
            draw = CheckedDraw(draw)

        draw_frame(draw, config.width, config.height)

        content_x = PANEL_PADDING
        content_y = PANEL_PADDING
        content_width = config.width - PANEL_PADDING * 2
        content_height = config.height - PANEL_PADDING * 2
        usable_width = content_width - CONTENT_GAP
        left_width = round(usable_width * LEFT_COLUMN_RATIO)
        right_x = content_x + left_width + CONTENT_GAP
        right_width = usable_width - left_width

        if strict:
            draw.bounds = (content_x, content_y, content_x + left_width, content_y + content_height)
        self._draw_left(
            draw,
            payload.data,
            content_x,
            content_y,
            left_width,
            content_height,
        )
        if strict:
            draw.bounds = (right_x, content_y, right_x + right_width, content_y + content_height)
        self._draw_right(
            draw,
            payload.data,
            right_x,
            content_y,
            right_width,
            content_height,
        )

        if preview_mode == "eink":
            image = to_eink(image)
        if strict:
            image.info["render_audit"] = {"fonts": draw.fonts, "texts": draw.texts}
        return image

    def get_metadata(self) -> PanelMetadata:
        return PanelMetadata(
            panel_type="progress",
            display_name="ProgressPanel",
            description="Compact progress and confirmation status panel",
        )

    def _current_time(self) -> str:
        return current_timestamp(self._clock)

    @staticmethod
    def _draw_left(
        draw: ImageDraw.ImageDraw,
        data: ProgressPanelData,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        draw.rectangle((x, y, x + width - 1, y + height - 1), fill=BLACK)
        inner_x = x + SPACE_3
        inner_width = width - SPACE_3 * 2

        draw.text(
            (inner_x, y + SPACE_4),
            data.title.upper(),
            fill=WHITE,
            font=get_font(FONT_SM, bold=True, mono=data.title.isascii()),
        )
        number_text = str(data.progress or 0)
        percent_font = get_font(FONT_XL, bold=True, mono=True)
        percent_bbox = draw.textbbox((0, 0), "%", font=percent_font)
        percent_width = percent_bbox[2] - percent_bbox[0]
        number_size = FONT_NUMBER
        number_font = get_font(number_size, bold=True, mono=True)
        while number_size > FONT_XL:
            number_bbox = draw.textbbox((0, 0), number_text, font=number_font)
            number_width = number_bbox[2] - number_bbox[0]
            if number_width + SPACE_1 + percent_width <= inner_width:
                break
            number_size -= 1
            number_font = get_font(number_size, bold=True, mono=True)
        number_x = inner_x - SPACE_1
        number_y = y + 39
        draw.text(
            (number_x, number_y),
            number_text,
            fill=WHITE,
            font=number_font,
        )
        number_bbox = draw.textbbox((number_x, number_y), number_text, font=number_font)
        percent_y = number_bbox[3] - percent_bbox[3]
        draw.text(
            (number_bbox[2] + SPACE_1, percent_y),
            "%",
            fill=WHITE,
            font=percent_font,
        )

        step = data.current_step or data.status or "等待数据"
        draw.text(
            (inner_x, y + height - 59),
            step,
            fill=WHITE,
            font=get_font(FONT_SM, bold=True),
        )

        bar_x = inner_x
        bar_y = y + height - SPACE_4 - PROGRESS_HEIGHT
        bar_width = inner_width
        draw.rectangle(
            (bar_x, bar_y, bar_x + bar_width - 1, bar_y + PROGRESS_HEIGHT - 1),
            outline=WHITE,
            width=BORDER_THIN,
        )
        inner_bar_width = bar_width - 2
        completed = round(inner_bar_width * (data.progress or 0) / 100)
        if completed > 0:
            draw.rectangle(
                (bar_x + 1, bar_y + 1, bar_x + completed, bar_y + PROGRESS_HEIGHT - 2),
                fill=WHITE,
            )

        remaining_start = bar_x + 1 + completed
        remaining_width = inner_bar_width - completed
        if remaining_width >= 9:
            segment_width = max(3, remaining_width // 3)
            for index in range(3):
                segment_x = remaining_start + index * segment_width
                segment_right = (
                    bar_x + bar_width - 2
                    if index == 2
                    else min(segment_x + segment_width - 2, bar_x + bar_width - 2)
                )
                if segment_x <= segment_right:
                    draw.rectangle(
                        (segment_x, bar_y + 1, segment_right, bar_y + PROGRESS_HEIGHT - 2),
                        outline=WHITE,
                        width=BORDER_THIN,
                    )

    @staticmethod
    def _draw_right(
        draw: ImageDraw.ImageDraw,
        data: ProgressPanelData,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        right_edge = x + width
        status_text = data.status or "进行中"
        tag_font = get_font(FONT_SM, bold=True)
        tag_bbox = draw.textbbox((0, 0), status_text, font=tag_font)
        tag_width = tag_bbox[2] - tag_bbox[0] + SPACE_2 * 2
        tag_width = min(tag_width, width - 42)
        draw.rectangle((x, y, x + tag_width, y + TAG_HEIGHT - 1), fill=BLACK)
        draw.text(
            (x + SPACE_2, y + 2),
            status_text,
            fill=WHITE,
            font=tag_font,
        )

        draw_terminal_mark(draw, right_edge, y)

        if data.status in {"WAITING DATA", "UPDATE FAILED"}:
            main_title = data.status
        else:
            main_title = data.current_step or "等待数据"
        draw.text(
            (x, y + TAG_HEIGHT + SPACE_4),
            main_title,
            fill=BLACK,
            font=get_font(FONT_XL, bold=True),
        )

        description = data.description or "等待进一步信息"
        draw.text(
            (x, y + TAG_HEIGHT + SPACE_4 + 38),
            description,
            fill=BLACK,
            font=get_font(FONT_MD),
        )

        tag_y = y + TAG_HEIGHT + SPACE_4 + 70
        cursor_x = x
        for tag in data.tags[:2]:
            tag_text_font = get_font(FONT_SM)
            tag_text_bbox = draw.textbbox((0, 0), tag, font=tag_text_font)
            text_width = tag_text_bbox[2] - tag_text_bbox[0]
            terminal_tag_width = text_width + SPACE_2 * 2
            if cursor_x + terminal_tag_width > right_edge:
                if isinstance(draw, CheckedDraw):
                    raise ValueError("Layout: tags exceed column")
                break
            draw.rectangle(
                (cursor_x, tag_y, cursor_x + terminal_tag_width, tag_y + TAG_HEIGHT - 1),
                outline=BLACK,
                width=BORDER_THIN,
            )
            draw.text(
                (cursor_x + SPACE_2, tag_y + 2),
                tag,
                fill=BLACK,
                font=tag_text_font,
            )
            cursor_x += terminal_tag_width + SPACE_2

        draw_footer(draw, x, y + height, data.source, data.updated_at)
