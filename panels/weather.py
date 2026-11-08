"""Deterministic weather page renderer for the 400x300 e-ink panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from PIL import Image, ImageDraw
from pydantic import BaseModel, ConfigDict, Field, model_validator

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
from panels.drawing import draw_footer, draw_frame, draw_terminal_mark, to_eink
from panels.render_validation import CheckedDraw


class WeatherHour(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    hour: int = Field(ge=0, le=23)
    temp: int = Field(ge=-50, le=60)
    label: str = Field(min_length=1, max_length=4)


class WeatherDay(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    date: str = Field(pattern=r"^[0-9]{2}-[0-9]{2}$")
    weekday: str = Field(min_length=1, max_length=3)
    high: int = Field(ge=-50, le=60)
    low: int = Field(ge=-50, le=60)
    label: str = Field(min_length=1, max_length=4)


class WeatherCity(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=8)
    current_temp: int | None = Field(default=None, ge=-50, le=60)
    current_label: str | None = Field(default=None, max_length=4)
    hourly: list[WeatherHour] = Field(default_factory=list, max_length=8)
    daily: list[WeatherDay] = Field(default_factory=list, max_length=3)


class WeatherPageData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    revision: int = Field(default=1, ge=1)
    updated_at: str | None = Field(default=None, max_length=32)
    day_key: str | None = Field(default=None, max_length=10)
    current_city: str = Field(default="changsha", pattern=r"^[a-z][a-z0-9_-]{0,15}$")
    cities: dict[str, WeatherCity] = Field(default_factory=dict)
    stale: bool = True
    source: str = Field(default="open-meteo", max_length=24)

    @model_validator(mode="after")
    def current_city_exists(self) -> "WeatherPageData":
        if self.cities and self.current_city not in self.cities:
            raise ValueError("Unknown current city")
        return self


@dataclass(frozen=True)
class NormalizedWeather:
    data: WeatherPageData
    state: Literal["ok"] = "ok"
    message: str = ""


class WeatherPanel(BasePanel):
    """Render the cached weather document; never reads the system clock."""

    def validate(self, data: Mapping[str, Any]) -> WeatherPageData:
        return WeatherPageData.model_validate(dict(data))

    def normalize(self, data: Mapping[str, Any]) -> NormalizedWeather:
        return NormalizedWeather(self.validate(data))

    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
        *,
        strict: bool = False,
    ) -> Image.Image:
        if config.width != 400 or config.height != 300:
            raise ValueError("WeatherPanel is calibrated for a 400x300 display")
        if preview_mode not in {"normal", "eink"}:
            raise ValueError(f"Unknown preview mode: {preview_mode}")

        payload = self.normalize(data).data
        city = payload.cities.get(payload.current_city)
        image = Image.new("L", (config.width, config.height), WHITE)
        draw: ImageDraw.ImageDraw | CheckedDraw = ImageDraw.Draw(image)
        if strict:
            draw = CheckedDraw(draw)

        draw_frame(draw, config.width, config.height)
        draw.rectangle(
            (PANEL_PADDING, 36, config.width - PANEL_PADDING - 1, 36), fill=BLACK
        )

        draw.text((PANEL_PADDING, 6), "天气", fill=BLACK, font=get_font(FONT_LG, bold=True))
        draw.text(
            (PANEL_PADDING + 52, 12),
            "WEATHER",
            fill=BLACK,
            font=get_font(FONT_SM, bold=True, mono=True),
        )
        header = f"{city.name if city else '天气'} {payload.day_key or ''}".strip()
        header_font = get_font(FONT_SM, bold=True)
        header_bbox = draw.textbbox((0, 0), header, font=header_font)
        draw.text(
            (360 - (header_bbox[2] - header_bbox[0]), 9),
            header,
            fill=BLACK,
            font=header_font,
        )

        if city is None or city.current_temp is None or not city.hourly:
            draw.text(
                (PANEL_PADDING, 84),
                "等待天气数据",
                fill=BLACK,
                font=get_font(FONT_LG, bold=True),
            )
            draw.text(
                (PANEL_PADDING, 114),
                "Host 每小时自动获取",
                fill=BLACK,
                font=get_font(FONT_SM),
            )
        else:
            self._draw_current(draw, city)
            self._draw_hours(draw, city)
            self._draw_days(draw, city)

        footer_source = payload.source.upper() + (" STALE" if payload.stale else "")
        draw_footer(draw, PANEL_PADDING, 290, footer_source, payload.updated_at)
        draw_terminal_mark(draw, config.width - PANEL_PADDING, 6)

        if preview_mode == "eink":
            image = to_eink(image)
        if strict:
            image.info["render_audit"] = {"fonts": draw.fonts, "texts": draw.texts}
        return image

    @staticmethod
    def _draw_current(draw: ImageDraw.ImageDraw, city: WeatherCity) -> None:
        assert city.current_temp is not None
        temp_text = f"{city.current_temp}°"
        temp_font = get_font(56, bold=True, mono=True)
        bbox = draw.textbbox((0, 0), temp_text, font=temp_font)
        draw.text((PANEL_PADDING, 42), temp_text, fill=BLACK, font=temp_font)
        label = city.current_label or "--"
        draw.text(
            (PANEL_PADDING + (bbox[2] - bbox[0]) + 12, 74),
            label,
            fill=BLACK,
            font=get_font(FONT_LG, bold=True),
        )

    @staticmethod
    def _draw_hours(draw: ImageDraw.ImageDraw, city: WeatherCity) -> None:
        draw.text((PANEL_PADDING, 104), "未来 8 小时", fill=BLACK, font=get_font(FONT_XS))
        hour_font = get_font(FONT_XS)
        temp_font = get_font(FONT_MD, bold=True, mono=True)
        label_font = get_font(FONT_XS)
        for index, hour in enumerate(city.hourly):
            x = 8 + index * 47
            draw.text((x, 118), f"{hour.hour}时", fill=BLACK, font=hour_font)
            draw.text((x, 130), f"{hour.temp}°", fill=BLACK, font=temp_font)
            draw.text((x, 148), hour.label, fill=BLACK, font=label_font)

    @staticmethod
    def _draw_days(draw: ImageDraw.ImageDraw, city: WeatherCity) -> None:
        draw.text((PANEL_PADDING, 164), "未来 3 天", fill=BLACK, font=get_font(FONT_XS))
        day_font = get_font(FONT_XS, bold=True)
        temp_font = get_font(FONT_MD, bold=True, mono=True)
        label_font = get_font(FONT_XS)
        for index, day in enumerate(city.daily):
            y = 178 + index * 28
            draw.text(
                (PANEL_PADDING, y + 2),
                f"{day.date} {day.weekday}",
                fill=BLACK,
                font=day_font,
            )
            draw.text((150, y), f"{day.low}~{day.high}°", fill=BLACK, font=temp_font)
            bbox = draw.textbbox((0, 0), day.label, font=label_font)
            draw.text((390 - (bbox[2] - bbox[0]), y + 2), day.label, fill=BLACK, font=label_font)

    def get_metadata(self) -> PanelMetadata:
        return PanelMetadata(
            panel_type="weather",
            display_name="WeatherPanel",
            description="Deterministic cached weather page with stale marking",
        )
