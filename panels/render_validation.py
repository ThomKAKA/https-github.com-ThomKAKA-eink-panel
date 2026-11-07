"""Optional checks of actual Pillow draw calls, not a second layout engine."""

import hashlib
import os
import unicodedata
from pathlib import Path


def intersects(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def contains(a, b):
    return a[0] <= b[0] and a[1] <= b[1] and a[2] >= b[2] and a[3] >= b[3]


class CheckedDraw:
    """Conservative raster missing-glyph and ink-bounds audit for one render.

    Missing glyph comparison is not an exhaustive font cmap proof. The output
    remains a candidate requiring visual review of the final 1-bit image.
    """

    def __init__(self, draw):
        self.draw = draw
        self.bounds = (0, 0, 400, 300)
        self.texts = []
        self.rectangles = []
        self.fonts = {}

    def __getattr__(self, name):
        return getattr(self.draw, name)

    def rectangle(self, xy, **kwargs):
        box = (xy[0], xy[1], xy[2] + 1, xy[3] + 1)
        if any(intersects(box, entry["bbox"]) for entry in self.texts):
            raise ValueError("Layout: graphic overlaps existing text")
        self.rectangles.append(box)
        return self.draw.rectangle(xy, **kwargs)

    def text(self, xy, text, *, font, **kwargs):
        font_path = getattr(font, "path", "")
        if not isinstance(font_path, (str, os.PathLike)):
            raise ValueError("Font: explicit existing font file required")
        path = Path(font_path)
        if not path.is_file():
            raise ValueError("Font: explicit existing font file required")
        missing = font.getmask("\U0010ffff")
        missing_signature = (missing.size, bytes(missing))
        for char in text:
            if unicodedata.category(char).startswith("C"):
                raise ValueError("Font/layout: control or unassigned character")
            mask = font.getmask(char)
            if char != " " and (not mask.getbbox() or (mask.size, bytes(mask)) == missing_signature):
                raise ValueError(f"Font: missing glyph U+{ord(char):04X}")
        box = self.draw.textbbox(xy, text, font=font)
        if not contains(self.bounds, box):
            raise ValueError(f"Layout: text exceeds column: {text!r}")
        for rectangle in self.rectangles:
            if intersects(rectangle, box) and not contains(rectangle, box):
                raise ValueError(f"Layout: text crosses graphic boundary: {text!r}")
        if any(intersects(box, entry["bbox"]) for entry in self.texts):
            raise ValueError(f"Layout: overlapping text: {text!r}")
        self.fonts[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.texts.append({"text": text, "bbox": list(box), "font": str(path.resolve()), "size": font.size})
        return self.draw.text(xy, text, font=font, **kwargs)
