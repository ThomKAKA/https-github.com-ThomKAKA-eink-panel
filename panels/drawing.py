"""Small shared drawing helpers used by the Phase 2 panel renderers."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

from panels.design_system import (
    BLACK,
    BORDER_THIN,
    EINK_THRESHOLD,
    FONT_LG,
    FONT_XS,
    MID_GRAY,
    SPACE_2,
    WHITE,
    get_font,
)


Clock = Callable[[], datetime]


def current_timestamp(clock: Clock) -> str:
    """Return the local panel timestamp at minute precision."""

    return clock().astimezone().strftime("%Y-%m-%d %H:%M")


def draw_frame(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    draw.rectangle(
        (0, 0, width - 1, height - 1),
        outline=BLACK,
        width=BORDER_THIN,
    )


def draw_terminal_mark(
    draw: ImageDraw.ImageDraw,
    right_edge: int,
    y: int,
    *,
    mark: str = "Γ.",
) -> None:
    font = get_font(FONT_LG, bold=True, mono=True)
    bbox = draw.textbbox((0, 0), mark, font=font)
    draw.text((right_edge - (bbox[2] - bbox[0]), y), mark, fill=BLACK, font=font)


def draw_footer(
    draw: ImageDraw.ImageDraw,
    x: int,
    bottom: int,
    source: str,
    updated_at: str | None,
) -> None:
    font = get_font(FONT_XS)
    draw.text((x, bottom - 25), f"来源 / {source or '--'}", fill=MID_GRAY, font=font)
    draw.text(
        (x, bottom - 13),
        f"更新 / {updated_at or '--'}",
        fill=MID_GRAY,
        font=font,
    )


def draw_filled_tag(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    *,
    height: int,
    font: ImageFont.ImageFont,
    max_width: int,
) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    width = min(bbox[2] - bbox[0] + SPACE_2 * 2, max_width)
    draw.rectangle((x, y, x + width, y + height - 1), fill=BLACK)
    draw.text((x + SPACE_2, y + 2), text, fill=WHITE, font=font)
    return width


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    *,
    max_size: int,
    min_size: int,
    bold: bool = True,
    mono: bool = True,
) -> ImageFont.ImageFont:
    size = max_size
    while size > min_size:
        font = get_font(size, bold=bold, mono=mono)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 1
    return get_font(min_size, bold=bold, mono=mono)


def to_eink(image: Image.Image) -> Image.Image:
    return image.point(
        lambda pixel: WHITE if pixel >= EINK_THRESHOLD else BLACK,
        mode="1",
    )
