"""Deterministic Codex usage page for the 400x300 e-ink panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from PIL import Image, ImageDraw
from pydantic import BaseModel, ConfigDict, Field

from panels.base import BasePanel, DisplayConfig, PanelMetadata
from panels.design_system import (
    BLACK,
    FONT_LG,
    FONT_SM,
    PANEL_PADDING,
    WHITE,
    get_font,
)
from panels.drawing import draw_frame, draw_terminal_mark, fit_font, to_eink
from panels.render_validation import CheckedDraw


CHART_TOP = 146
CHART_BOTTOM = 214
CHART_SLOT = 55
CHART_BAR = 30


def format_tokens(value: int) -> str:
    if value < 1000:
        return str(value)
    if value < 1_000_000:
        return f"{value / 1000:.1f}k"
    if value < 1_000_000_000:
        return f"{value / 1_000_000:.1f}M"
    return f"{value / 1_000_000_000:.2f}B"


class CodexDay(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    date: str = Field(pattern=r"^[0-9]{2}-[0-9]{2}$")
    tokens: int = Field(ge=0)


class CodexPageData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    revision: int = Field(default=1, ge=1)
    updated_at: str | None = Field(default=None, max_length=32)
    day_key: str | None = Field(default=None, max_length=10)
    today_tokens: int | None = Field(default=None, ge=0)
    week_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    responses: int | None = Field(default=None, ge=0)
    sessions: int | None = Field(default=None, ge=0)
    last_activity: str | None = Field(default=None, max_length=16)
    used_percent: float | None = Field(default=None, ge=0, le=100)
    window_minutes: int | None = Field(default=None, ge=0)
    resets_at: str | None = Field(default=None, max_length=10)
    plan: str | None = Field(default=None, max_length=16)
    quota_at: str | None = Field(default=None, max_length=16)
    days: list[CodexDay] = Field(default_factory=list, max_length=7)
    stale: bool = True
    source: str = Field(default="codex-sessions", max_length=32)


@dataclass(frozen=True)
class NormalizedCodex:
    data: CodexPageData
    state: Literal["ok"] = "ok"
    message: str = ""


class CodexUsagePanel(BasePanel):
    """Render the last synced usage document; never reads the session files."""

    def validate(self, data: Mapping[str, Any]) -> CodexPageData:
        return CodexPageData.model_validate(dict(data))

    def normalize(self, data: Mapping[str, Any]) -> NormalizedCodex:
        return NormalizedCodex(self.validate(data))

    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
        *,
        strict: bool = False,
    ) -> Image.Image:
        if config.width != 400 or config.height != 300:
            raise ValueError("CodexUsagePanel is calibrated for a 400x300 display")
        if preview_mode not in {"normal", "eink"}:
            raise ValueError(f"Unknown preview mode: {preview_mode}")

        payload = self.normalize(data).data
        image = Image.new("L", (config.width, config.height), WHITE)
        draw: ImageDraw.ImageDraw | CheckedDraw = ImageDraw.Draw(image)
        if strict:
            draw = CheckedDraw(draw)

        draw_frame(draw, config.width, config.height)
        draw.rectangle(
            (PANEL_PADDING, 36, config.width - PANEL_PADDING - 1, 36), fill=BLACK
        )
        draw.line((240, 44, 240, 140), fill=BLACK, width=1)
        if payload.stale:
            draw.rectangle((298, 5, 358, 27), fill=BLACK)

        draw.text((PANEL_PADDING, 6), "用量", fill=BLACK, font=get_font(FONT_LG, bold=True))
        draw.text(
            (PANEL_PADDING + 52, 12),
            "CODEX USAGE",
            fill=BLACK,
            font=get_font(FONT_SM, bold=True, mono=True),
        )
        if payload.stale:
            draw.text(
                (304, 7),
                "STALE",
                fill=WHITE,
                font=get_font(14, bold=True, mono=True),
            )

        if payload.today_tokens is None:
            draw.text(
                (PANEL_PADDING, 104),
                "等待 Codex 同步",
                fill=BLACK,
                font=get_font(FONT_LG, bold=True),
            )
            draw.text(
                (PANEL_PADDING, 136),
                "运行 scripts/sync_codex_usage.py",
                fill=BLACK,
                font=get_font(FONT_SM),
            )
        else:
            self._draw_usage(draw, payload)

        self._draw_footer(draw, payload)
        draw_terminal_mark(draw, config.width - PANEL_PADDING, 6)

        if preview_mode == "eink":
            image = to_eink(image)
        if strict:
            image.info["render_audit"] = {"fonts": draw.fonts, "texts": draw.texts}
        return image

    @staticmethod
    def _draw_usage(draw: ImageDraw.ImageDraw, payload: CodexPageData) -> None:
        label_font = get_font(FONT_SM, bold=True)
        draw.text((PANEL_PADDING, 44), "今日 TOKEN", fill=BLACK, font=label_font)
        today = format_tokens(payload.today_tokens or 0)
        draw.text(
            (PANEL_PADDING - 1, 58),
            today,
            fill=BLACK,
            font=fit_font(
                draw, today, 205, max_size=46, min_size=24, bold=True, mono=True
            ),
        )

        draw.text(
            (PANEL_PADDING, 108),
            f"近 7 天 {format_tokens(payload.week_tokens or 0)}",
            fill=BLACK,
            font=label_font,
        )
        draw.text(
            (PANEL_PADDING, 126),
            f"累计 {format_tokens(payload.total_tokens or 0)}",
            fill=BLACK,
            font=label_font,
        )

        quota_x = 252
        plan = f"额度 {payload.plan.upper()}" if payload.plan else "额度"
        draw.text((quota_x, 44), plan, fill=BLACK, font=label_font)
        percent = payload.used_percent if payload.used_percent is not None else 0.0
        draw.text(
            (quota_x, 58),
            f"{percent:g}%",
            fill=BLACK,
            font=get_font(24, bold=True, mono=True),
        )
        if payload.window_minutes:
            days = payload.window_minutes // 1440
            window = f"{days} 天窗口" if days and payload.window_minutes % 1440 == 0 else f"{payload.window_minutes} 分窗口"
            draw.text((quota_x, 90), window, fill=BLACK, font=get_font(FONT_SM))
        if payload.resets_at:
            draw.text(
                (quota_x, 106),
                f"重置 {payload.resets_at}",
                fill=BLACK,
                font=get_font(FONT_SM),
            )
        if payload.quota_at:
            draw.text(
                (quota_x, 122),
                f"快照 {payload.quota_at}",
                fill=BLACK,
                font=get_font(FONT_SM),
            )

        CodexUsagePanel._draw_chart(draw, payload)

        activity = f"最后活动 {payload.last_activity or '--'}"
        if payload.responses is not None and payload.sessions is not None:
            activity += f" · {payload.responses} 次 · {payload.sessions} 个会话"
        draw.text((PANEL_PADDING, 242), activity, fill=BLACK, font=get_font(FONT_SM))

    @staticmethod
    def _draw_chart(draw: ImageDraw.ImageDraw, payload: CodexPageData) -> None:
        days = payload.days[:7]
        if not days:
            return
        peak = max(day.tokens for day in days) or 1
        height = CHART_BOTTOM - CHART_TOP
        label_font = get_font(FONT_SM, mono=True)
        for index, day in enumerate(days):
            slot = PANEL_PADDING + index * CHART_SLOT
            bar_x = slot + (CHART_SLOT - CHART_BAR) // 2
            bar_height = round(height * day.tokens / peak)
            if bar_height > 0:
                draw.rectangle(
                    (bar_x, CHART_BOTTOM - bar_height, bar_x + CHART_BAR - 1, CHART_BOTTOM - 1),
                    fill=BLACK,
                )
            else:
                draw.line(
                    (bar_x, CHART_BOTTOM - 1, bar_x + CHART_BAR - 1, CHART_BOTTOM - 1),
                    fill=BLACK,
                    width=1,
                )
            bbox = draw.textbbox((0, 0), day.date, font=label_font)
            draw.text(
                (slot + (CHART_SLOT - (bbox[2] - bbox[0])) // 2, 224),
                day.date,
                fill=BLACK,
                font=label_font,
            )

    @staticmethod
    def _draw_footer(draw: ImageDraw.ImageDraw, payload: CodexPageData) -> None:
        font = get_font(FONT_SM, bold=True)
        draw.text(
            (PANEL_PADDING, 262),
            f"来源 / {payload.source}",
            fill=BLACK,
            font=font,
        )
        draw.text(
            (PANEL_PADDING, 277),
            f"更新 / {payload.updated_at or '--'}",
            fill=BLACK,
            font=font,
        )

    def get_metadata(self) -> PanelMetadata:
        return PanelMetadata(
            panel_type="codex",
            display_name="CodexUsagePanel",
            description="Deterministic Codex token usage with a seven-day chart",
        )
