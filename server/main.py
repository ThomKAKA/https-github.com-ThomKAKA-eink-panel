"""FastAPI entry point for the Phase 3 data-driven panel simulator."""

from __future__ import annotations

import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from panels.base import DisplayConfig, create_panel
from services.refresh_manager import RefreshManager


ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
CONFIG_PATH = ROOT / "config" / "config.json"
DATA_SOURCES_PATH = ROOT / "config" / "data_sources.json"
SAMPLE_PATHS = {
    "progress": ROOT / "examples" / "progress_samples.json",
    "stats": ROOT / "examples" / "stats_samples.json",
    "flow": ROOT / "examples" / "flow_samples.json",
}
PANEL_TYPES = frozenset(SAMPLE_PATHS)
PREVIEW_MODES = frozenset({"normal", "eink"})
IMAGE_FORMATS = frozenset({"png", "bmp"})
REFRESH_INTERVALS = frozenset({0, 5, 30, 60, 300, 900, 1800})

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
refresh_manager = RefreshManager(DATA_SOURCES_PATH, root=ROOT)


def load_display_config() -> DisplayConfig:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return DisplayConfig(**payload["display"])


def load_samples(panel_type: str) -> list[dict[str, Any]]:
    path = SAMPLE_PATHS.get(panel_type)
    if path is None:
        raise ValueError(f"Unknown panel type: {panel_type}")
    return json.loads(path.read_text(encoding="utf-8"))


app = FastAPI(title="E-Ink Panel Simulator", version="0.3.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def simulator_page() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/samples/{panel_type}")
def panel_samples(panel_type: str) -> list[dict[str, Any]]:
    if panel_type not in PANEL_TYPES:
        raise HTTPException(status_code=404, detail="Unknown panel type")
    return load_samples(panel_type)


@app.get("/api/data-sources/{panel_type}")
def data_sources(panel_type: str) -> list[dict[str, Any]]:
    if panel_type not in PANEL_TYPES:
        raise HTTPException(status_code=404, detail="Unknown panel type")
    return refresh_manager.list_sources(panel_type)


@app.post("/api/data-sources/{source_id}/refresh")
def refresh_data_source(
    source_id: str,
    options: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    sample_id = options.get("sample_id")
    interval_seconds = options.get("interval_seconds", 0)
    if sample_id is not None and not isinstance(sample_id, str):
        raise HTTPException(status_code=400, detail="sample_id must be a string")
    if not isinstance(interval_seconds, int) or interval_seconds not in REFRESH_INTERVALS:
        raise HTTPException(status_code=400, detail="Unsupported refresh interval")
    try:
        outcome = refresh_manager.refresh(
            source_id,
            sample_id=sample_id,
            interval_seconds=interval_seconds,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown data source") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return outcome.as_dict()


@app.post("/api/panels/{panel_type}/render")
def render_panel(
    panel_type: str,
    data: dict[str, Any] = Body(default_factory=dict),
    mode: str = Query(default="normal"),
    image_format: str = Query(default="png", alias="format"),
) -> Response:
    if panel_type not in PANEL_TYPES:
        raise HTTPException(status_code=404, detail="Unknown panel type")
    if mode not in PREVIEW_MODES:
        raise HTTPException(status_code=400, detail="Unknown preview mode")
    if image_format not in IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail="Unknown image format")

    panel = create_panel(panel_type)
    config = load_display_config()
    image = panel.render(data, config, preview_mode=mode)
    rendered_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("Render: panel=%s mode=%s format=%s", panel_type, mode, image_format)

    output = io.BytesIO()
    pillow_format = image_format.upper()
    image.save(output, format=pillow_format)
    media_type = "image/png" if image_format == "png" else "image/bmp"
    return Response(
        content=output.getvalue(),
        media_type=media_type,
        headers={
            "Cache-Control": "no-store",
            "X-Panel-Width": str(config.width),
            "X-Panel-Height": str(config.height),
            "X-Panel-Mode": mode,
            "X-Panel-Type": panel_type,
            "X-Rendered-At": rendered_at,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.main:app", host="127.0.0.1", port=8000, reload=False)
