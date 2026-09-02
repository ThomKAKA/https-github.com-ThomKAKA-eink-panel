"""Shared monochrome design tokens for e-ink panels."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont


# Typography
FONT_XS = 8
FONT_SM = 10
FONT_MD = 13
FONT_LG = 18
FONT_XL = 24
FONT_NUMBER = 64

# Spacing
SPACE_1 = 3
SPACE_2 = 6
SPACE_3 = 9
SPACE_4 = 12

# Geometry
PANEL_PADDING = 10
BORDER_THIN = 1
BORDER_NORMAL = 2
TAG_HEIGHT = 20
PROGRESS_HEIGHT = 14
CONTENT_GAP = 8
LEFT_COLUMN_RATIO = 0.38
EINK_THRESHOLD = 192
DIVIDER_WIDTH = 1
STATS_BAR_HEIGHT = 10
STATS_LEFT_COLUMN_RATIO = 0.40
FLOW_LEFT_COLUMN_RATIO = 0.39
FLOW_NODE_DONE = 16
FLOW_NODE_ACTIVE = 24
FLOW_NODE_PENDING = 20

# Monochrome palette
BLACK = 0
MID_GRAY = 112
LIGHT_GRAY = 232
WHITE = 255


@dataclass(frozen=True)
class FontSpec:
    size: int
    bold: bool = False
    mono: bool = False


_WINDOWS_FONTS = Path("C:/Windows/Fonts")
_PROJECT_FONTS = Path(__file__).resolve().parents[1] / "assets" / "fonts"


def _font_candidates(spec: FontSpec) -> list[Path]:
    if spec.mono:
        names = ["consolab.ttf" if spec.bold else "consola.ttf"]
    else:
        names = ["msyhbd.ttc" if spec.bold else "msyh.ttc"]

    candidates = [_PROJECT_FONTS / name for name in names]
    candidates.extend(_WINDOWS_FONTS / name for name in names)
    candidates.extend(
        [
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
            if spec.bold
            else Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
            if spec.bold
            else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]
    )
    return candidates


@lru_cache(maxsize=32)
def get_font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    spec = FontSpec(size=size, bold=bold, mono=mono)
    for path in _font_candidates(spec):
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)
