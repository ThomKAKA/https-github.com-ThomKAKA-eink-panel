"""Manual renderer-only CLI: python -m panels.offline_progress --help."""

import argparse
import hashlib
import io
import json
import platform
import re
from pathlib import Path

import PIL
import pydantic

from adapters.offline_progress import parse_offline_progress
from panels.base import DisplayConfig
from panels.progress import ProgressPanel

OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "artifacts/step016-offline-progress"


def render_offline(input_path: Path, run_id: str, *, output_root: Path = OUTPUT_ROOT) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ValueError("Invalid run-id")
    destination = output_root / run_id
    if destination.exists():
        raise FileExistsError(destination)
    content = Path(input_path).read_bytes()
    data = parse_offline_progress(content)
    image = ProgressPanel().render(data.model_dump(), DisplayConfig(), "eink", strict=True)
    for entry in image.info["render_audit"]["texts"]:
        if set(image.crop(entry["bbox"]).getdata()) != {0, 255}:
            raise ValueError(f"Font: text has no visible contrast after binarization: {entry['text']!r}")
    encoded = io.BytesIO()
    image.save(encoded, format="PNG")
    png = encoded.getvalue()
    manifest = {
        "stage": "STEP016C_RENDERER_ONLY",
        "status": "AUTOMATED_CHECKS_PASS_VISUAL_REVIEW_REQUIRED",
        "input": {"sha256": hashlib.sha256(content).hexdigest(), "size": len(content)},
        "mapped_data": data.model_dump(),
        "image": {"file": "progress.preview.png", "width": 400, "height": 300,
                  "mode": image.mode, "bit_depth": 1, "size": len(png),
                  "sha256": hashlib.sha256(png).hexdigest(), "orientation": "L: normal reading; no preflip"},
        "render_audit": image.info["render_audit"],
        "glyph_check": "conservative raster missing-glyph comparison plus drawing bounds; visual review required",
        "tools": {"python": platform.python_version(), "pillow": PIL.__version__, "pydantic": pydantic.__version__},
        "not_run": ["raw/header export", "transmission preflip", "firmware integration", "hardware test"],
    }
    # Validation completes in memory before creating anything. Exclusive creation
    # prevents overwriting prior runs. Manifest is last; incomplete runs are invalid.
    destination.mkdir(parents=True, exist_ok=False)
    with (destination / "progress.preview.png").open("xb") as stream:
        stream.write(png)
    with (destination / "renderer-manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        print(render_offline(args.input, args.run_id))
    except (ValueError, OSError) as error:
        parser.exit(1, f"Renderer rejected input/output: {error}\n")


if __name__ == "__main__":
    main()
