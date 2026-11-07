"""PC-only PNG to logical (L) raw/header conversion; no H1 direction adaptation."""

import argparse
import hashlib
import io
import json
import platform
import re
from pathlib import Path

import PIL
from PIL import Image

OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "artifacts/step016-frame-converter"
RAW_NAME = "progress.logical.raw"
HEADER_NAME = "progress_logical_frame.h"


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def png_to_logical_raw(content: bytes) -> bytes:
    """Validate the actual PNG and preserve every decoded (x, y) pixel."""
    with Image.open(io.BytesIO(content)) as image:
        if image.format != "PNG":
            raise ValueError("INPUT_INVALID: expected PNG")
        image.verify()
    with Image.open(io.BytesIO(content)) as image:
        if image.size != (400, 300) or image.mode != "1":
            raise ValueError("INPUT_INVALID: expected 400x300 mode 1")
        if getattr(image, "n_frames", 1) != 1 or getattr(image, "is_animated", False):
            raise ValueError("INPUT_INVALID: animated PNG is not supported")
        if "transparency" in image.info:
            raise ValueError("INPUT_INVALID: transparency is not supported")
        if image.getexif().get(274, 1) != 1:
            raise ValueError("INPUT_INVALID: non-default orientation")
        image.load()
        pixels = image.load()
        packed = bytearray(15000)
        for y in range(300):
            for x in range(400):
                if pixels[x, y]:
                    packed[y * 50 + x // 8] |= 0x80 >> (x % 8)
        return bytes(packed)


def make_header(raw: bytes, source_name: str, input_hash: str) -> bytes:
    if len(raw) != 15000:
        raise ValueError("FRAME_INVALID: expected 15000 bytes")
    # JSON escaping plus comment-terminator escaping keeps filenames as comments.
    source = json.dumps(source_name, ensure_ascii=True).replace("*/", "* /")
    lines = [
        "#ifndef EINK_PROGRESS_LOGICAL_FRAME_H",
        "#define EINK_PROGRESS_LOGICAL_FRAME_H",
        "#include <stdint.h>",
        "#include <stddef.h>",
        "/* Logical frame L: pixel mapping unchanged; no L-to-T adaptation.",
        " * NOT a forward-reading transport frame for the fixed H1 mirror_y path.",
        f" * Source PNG: {source}",
        f" * Input PNG SHA256: {input_hash}",
        f" * Array/raw SHA256: {sha256(raw)}",
        " * 400x300, 15000 bytes, stride 50, MSB-first, 0 black / 1 white.",
        " */",
        "static const uint8_t progress_logical_frame[] = {",
    ]
    lines.extend("    " + ", ".join(f"0x{value:02X}" for value in raw[i:i + 16]) + ","
                 for i in range(0, len(raw), 16))
    lines.extend([
        "};",
        "static const size_t progress_logical_frame_length = sizeof(progress_logical_frame);",
        "#endif",
        "",
    ])
    header = "\n".join(lines).encode("ascii")
    body = header.split(b"progress_logical_frame[] = {", 1)[1].split(b"};", 1)[0]
    if bytes(int(value, 16) for value in re.findall(rb"0x([0-9A-F]{2})", body)) != raw:
        raise ValueError("FRAME_INVALID: header/raw mismatch")
    return header


def convert_frame(input_path: Path, run_id: str, *, output_root: Path = OUTPUT_ROOT) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ValueError("OUTPUT_INVALID: invalid run-id")
    destination = output_root / run_id
    if destination.exists():
        raise FileExistsError(f"OUTPUT_CONFLICT: {destination}")
    input_path = Path(input_path)
    content = input_path.read_bytes()
    raw = png_to_logical_raw(content)
    header = make_header(raw, input_path.name, sha256(content))
    manifest = {
        "stage": "STEP016D_B1_LOGICAL_FRAME_ONLY",
        "status": "CONVERSION_COMPLETE_NOT_H1_TRANSPORT_READY",
        "coordinate_frame": "L", "pixel_mapping": "unchanged",
        "input": {"file": input_path.name, "size": len(content), "sha256": sha256(content)},
        "format": {"width": 400, "height": 300, "bit_depth": 1, "stride": 50,
                   "order": "row-major, MSB-first", "polarity": "0 black / 1 white"},
        "outputs": {name: {"size": len(data), "sha256": sha256(data)}
                    for name, data in ((RAW_NAME, raw), (HEADER_NAME, header))},
        "array": {"symbol": "progress_logical_frame", "length": len(raw),
                  "byte_sequence_sha256": sha256(raw)},
        "tools": {"python": platform.python_version(), "pillow": PIL.__version__},
        "not_run": ["L-to-T adaptation", "ESP32 integration", "compilation", "physical verification"],
    }
    metadata = (json.dumps(manifest, ensure_ascii=True, indent=2) + "\n").encode("utf-8")
    # Validate in memory, then create exclusively. A failed directory is never reused.
    # Only a complete final manifest denotes completion; partial files stay local.
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in ((RAW_NAME, raw), (HEADER_NAME, header), ("converter-manifest.pending", metadata)):
        with (destination / name).open("xb") as stream:
            stream.write(data)
    (destination / "converter-manifest.pending").rename(destination / "converter-manifest.json")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        print(convert_frame(args.input, args.run_id))
    except (ValueError, OSError, SyntaxError) as error:
        parser.exit(1, f"Frame conversion rejected: {error}\n")


if __name__ == "__main__":
    main()
