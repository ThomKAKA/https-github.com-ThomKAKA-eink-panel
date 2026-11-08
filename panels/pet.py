"""Deterministic pet status page: a chibi whale-girl with daily decay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
import re
from typing import Any, Callable, Mapping

from PIL import Image, ImageDraw
from pydantic import BaseModel, ConfigDict, Field, field_validator

from panels.base import BasePanel, DisplayConfig, PanelMetadata
from panels.design_system import (
    BLACK,
    FONT_LG,
    FONT_MD,
    FONT_SM,
    WHITE,
    PANEL_PADDING,
    get_font,
)
from panels.drawing import draw_frame, draw_terminal_mark, fit_font, to_eink
from panels.render_validation import CheckedDraw


SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")
PET_ART = Path(__file__).resolve().parents[1] / "assets" / "pet" / "chibi.png"
PET_ART_ORIGIN = (16, 56)
_DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_MINUTE = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
_WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")


@lru_cache(maxsize=1)
def pet_art() -> Image.Image:
    return Image.open(PET_ART).convert("1")


def _blank_is_missing(value: Any) -> Any:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return value


class PetPageData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    revision: int = Field(default=1, ge=1)
    updated_at: str | None = Field(default=None, max_length=32)
    day_key: str | None = None
    name: str = Field(default="大肥鱼", min_length=1, max_length=8)
    satiety: int = Field(default=50, ge=0, le=100)
    mood: int = Field(default=60, ge=0, le=100)
    affinity: int = Field(default=0, ge=0, le=999)
    last_fed: str | None = None
    last_interaction: str | None = None

    @field_validator("last_fed", "last_interaction", "updated_at", mode="before")
    @classmethod
    def blank_is_missing(cls, value: Any) -> Any:
        return _blank_is_missing(value)

    @field_validator("last_fed", "day_key")
    @classmethod
    def day_is_a_date(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _DAY.fullmatch(value):
            raise ValueError("Invalid day")
        date.fromisoformat(value)
        return value

    @field_validator("last_interaction", "updated_at")
    @classmethod
    def moment_is_a_minute(cls, value: str | None) -> str | None:
        if value is None:
            return None
        day, _, minute = value.partition(" ")
        if not _DAY.fullmatch(day) or not _MINUTE.fullmatch(minute):
            raise ValueError("Invalid moment")
        date.fromisoformat(day)
        return value


@dataclass(frozen=True)
class PetState:
    satiety: int
    mood: int
    affinity: int
    level: int
    fed_today: bool
    satiety_label: str
    mood_label: str


@dataclass(frozen=True)
class NormalizedPet:
    data: PetPageData
    weekday: str
    pet: PetState
    state: str = "ok"
    message: str = ""


def satiety_label(value: int) -> str:
    if value >= 70:
        return "很饱"
    if value >= 30:
        return "正常"
    if value > 0:
        return "有点饿"
    return "饿扁了"


def mood_label(value: int) -> str:
    if value >= 70:
        return "开心"
    if value >= 40:
        return "一般"
    return "低落"


def pet_state(document: PetPageData, day_key: str) -> PetState:
    """Derive today's stats from the last write day; no side effects."""
    today = date.fromisoformat(day_key)
    base = date.fromisoformat(document.updated_at[:10]) if document.updated_at else today
    days = max(0, (today - base).days)
    decay = 0 if days <= 0 else 25 + 15 * (days - 1)
    satiety = max(0, document.satiety - decay)
    mood = max(0, document.mood - (10 if satiety < 30 else 0))
    return PetState(
        satiety=satiety,
        mood=mood,
        affinity=document.affinity,
        level=min(99, 1 + document.affinity // 25),
        fed_today=document.last_fed == day_key,
        satiety_label=satiety_label(satiety),
        mood_label=mood_label(mood),
    )


class PetPanel(BasePanel):
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or datetime.now

    def validate(self, data: Mapping[str, Any]) -> PetPageData:
        return PetPageData.model_validate(dict(data))

    def normalize(self, data: Mapping[str, Any]) -> NormalizedPet:
        raw = dict(data)
        raw.setdefault("day_key", self._today())
        payload = self.validate(raw)
        assert payload.day_key is not None
        day = date.fromisoformat(payload.day_key)
        return NormalizedPet(payload, _WEEKDAYS[day.weekday()], pet_state(payload, payload.day_key))

    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
        *,
        strict: bool = False,
    ) -> Image.Image:
        if config.width != 400 or config.height != 300:
            raise ValueError("PetPanel is calibrated for a 400x300 display")
        if preview_mode not in {"normal", "eink"}:
            raise ValueError(f"Unknown preview mode: {preview_mode}")

        payload = self.normalize(data)
        state = payload.pet
        image = Image.new("L", (config.width, config.height), WHITE)
        draw: ImageDraw.ImageDraw | CheckedDraw = ImageDraw.Draw(image)
        if strict:
            draw = CheckedDraw(draw)

        draw_frame(draw, config.width, config.height)
        image.paste(pet_art(), PET_ART_ORIGIN)
        draw.rectangle((PANEL_PADDING, 50, config.width - PANEL_PADDING - 1, 50), fill=BLACK)

        draw.text((PANEL_PADDING, 6), "宠物", fill=BLACK, font=get_font(FONT_LG, bold=True))
        draw.text(
            (PANEL_PADDING + 44, 12),
            "PET",
            fill=BLACK,
            font=get_font(FONT_SM, bold=True, mono=True),
        )
        day_label = f"{payload.data.day_key} {payload.weekday}"
        draw.text((PANEL_PADDING, 31), day_label, fill=BLACK, font=get_font(FONT_MD, bold=True))

        self._draw_facts(draw, payload.data, state)
        self._draw_footer(draw, payload.data)
        draw_terminal_mark(draw, config.width - PANEL_PADDING, 6)

        if preview_mode == "eink":
            image = to_eink(image)
        if strict:
            image.info["render_audit"] = {"fonts": draw.fonts, "texts": draw.texts}
        return image

    @staticmethod
    def _draw_facts(draw: ImageDraw.ImageDraw, data: PetPageData, state: PetState) -> None:
        name_font = fit_font(
            draw,
            data.name,
            130,
            max_size=FONT_LG,
            min_size=FONT_MD,
            bold=True,
            mono=data.name.isascii(),
        )
        draw.text((196, 62), data.name, fill=BLACK, font=name_font)
        level = f"Lv.{state.level}"
        level_font = get_font(FONT_MD, bold=True, mono=True)
        level_bbox = draw.textbbox((0, 0), level, font=level_font)
        draw.text((390 - (level_bbox[2] - level_bbox[0]), 65), level, fill=BLACK, font=level_font)

        rows = (("饱食", state.satiety), ("心情", state.mood), ("亲密", state.affinity))
        for index, (label, value) in enumerate(rows):
            top = 96 + index * 30
            draw.text((196, top), label, fill=BLACK, font=get_font(FONT_SM, bold=True))
            draw.rectangle((196, top + 14, 316, top + 23), outline=BLACK)
            width = round(118 * min(value, 100) / 100)
            if width > 0:
                draw.rectangle((197, top + 15, 197 + width - 1, top + 22), fill=BLACK)
            number = str(min(value, 100))
            number_font = get_font(FONT_SM, mono=True)
            draw.text((324, top + 10), number, fill=BLACK, font=number_font)

        draw.text(
            (196, 188),
            f"{state.satiety_label} · {state.mood_label}",
            fill=BLACK,
            font=get_font(FONT_SM, bold=True),
        )
        draw.text(
            (196, 204),
            "今天已喂" if state.fed_today else "今天还没喂",
            fill=BLACK,
            font=get_font(FONT_SM, bold=True),
        )
        interaction = data.last_interaction[5:] if data.last_interaction else "--"
        draw.text(
            (196, 220),
            f"上次互动 {interaction}",
            fill=BLACK,
            font=get_font(FONT_SM),
        )

    @staticmethod
    def _draw_footer(draw: ImageDraw.ImageDraw, data: PetPageData) -> None:
        font = get_font(FONT_SM, bold=True)
        draw.text((PANEL_PADDING, 265), f"来源 / pet r{data.revision}", fill=BLACK, font=font)
        draw.text(
            (PANEL_PADDING, 279),
            f"更新 / {data.updated_at or '等待互动'}",
            fill=BLACK,
            font=font,
        )

    def get_metadata(self) -> PanelMetadata:
        return PanelMetadata(
            panel_type="pet",
            display_name="PetPanel",
            description="Deterministic whale-girl pet page with daily decay",
        )

    def _today(self) -> str:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=SHANGHAI)
        return value.astimezone(SHANGHAI).date().isoformat()
