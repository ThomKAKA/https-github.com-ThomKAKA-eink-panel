"""Rebuild assets/pet/chibi.png from the supplied line-art template.

The pet page pastes this prepared 1-bit bitmap unchanged; it is not redrawn.
The watermark region of the source sits outside the crop window.
"""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "pet" / "source.webp"
OUTPUT = ROOT / "assets" / "pet" / "chibi.png"
BOX = (174, 186)
CROP = (0, 0, 1330, 1120)
THRESHOLD = 192


def main() -> None:
    image = Image.open(SOURCE).convert("L")
    content = image.crop(CROP)
    bbox = content.point(lambda pixel: 255 if pixel < 128 else 0).getbbox()
    character = image.crop(bbox)
    scale = min(BOX[0] / character.width, BOX[1] / character.height)
    size = (round(character.width * scale), round(character.height * scale))
    small = character.resize(size, Image.LANCZOS)
    bitmap = small.point(lambda pixel: 0 if pixel < THRESHOLD else 255).convert("1")
    canvas = Image.new("1", BOX, 1)
    canvas.paste(bitmap, ((BOX[0] - size[0]) // 2, (BOX[1] - size[1]) // 2))
    canvas.save(OUTPUT)
    print(f"{OUTPUT} {OUTPUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
