"""FastAPI entry point for the data-driven panel simulator."""

from __future__ import annotations

import io
import argparse
import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from panels.base import DisplayConfig, create_panel
from services.event_store import (
    EventStateStore,
    InvalidPanelData,
    PanelUpdateEvent,
    build_snapshot,
)
from services.firmware_offer import FirmwareOffer
from services.frame_render import render_assets
from services.page_frames import PageFrameService
from services.page_registry import FILE_PAGES, create_page_panel, get_page
from services.page_state import PageRevisionConflict, PageStateStore, PageTooLarge
from services.refresh_manager import RefreshManager
from services.host_discovery import HostAdvertisement
from services.weather_scheduler import WeatherScheduler
from services.weather_source import WeatherSource
from zeroconf import NonUniqueNameException
from services.progress_frame import (
    CACHE_CONTROL,
    DeviceReport,
    FRAME_FORMAT,
    ProgressFramePublisher,
    PublishedFrame,
    condition_matches,
    parse_if_none_match,
    render_transport_assets,
)


ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
CONFIG_PATH = ROOT / "config" / "config.json"
DATA_SOURCES_PATH = ROOT / "config" / "data_sources.json"
WEATHER_CONFIG_PATH = ROOT / "config" / "weather.json"
PAGE_STATE_ROOT = ROOT / "data" / "pages"
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
event_store = EventStateStore()
frame_publisher = ProgressFramePublisher(event_store, os.environ.get("EINK_PROGRESS_SOURCE"))
page_state = PageStateStore(PAGE_STATE_ROOT, FILE_PAGES)
page_frames = PageFrameService(page_state, lambda: frame_publisher)
FIRMWARE_CONFIG_PATH = ROOT / "config" / "firmware.json"
firmware_offer = FirmwareOffer(FIRMWARE_CONFIG_PATH, ROOT)


class PageWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision: int = Field(ge=1)
    data: dict[str, Any]


def file_page(page_id: str):
    try:
        spec = get_page(page_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Unknown page") from error
    if spec.kind != "file":
        raise HTTPException(status_code=404, detail="Page is not a file page")
    return spec


def editable_page(page_id: str):
    spec = file_page(page_id)
    if not spec.editable:
        raise HTTPException(status_code=400, detail="Page is read-only")
    return spec


def normalized_page_data(page_id: str, data: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    panel = create_page_panel(page_id)
    try:
        normalized = panel.validate(data)
    except (ValidationError, ValueError) as error:
        raise HTTPException(status_code=422, detail="Invalid page data") from error
    payload = normalized.model_dump(
        exclude={"revision", "updated_at", "day_key"},
        exclude_none=True,
    )
    return panel, payload


def load_display_config() -> DisplayConfig:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return DisplayConfig(**payload["display"])


def load_weather_config() -> dict[str, Any] | None:
    try:
        payload = json.loads(WEATHER_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("enabled") is not True:
        return None
    return payload


def load_samples(panel_type: str) -> list[dict[str, Any]]:
    path = SAMPLE_PATHS.get(panel_type)
    if path is None:
        raise ValueError(f"Unknown panel type: {panel_type}")
    return json.loads(path.read_text(encoding="utf-8"))


@asynccontextmanager
async def lifespan(application):
    advertisement = getattr(application.state, "host_advertisement", None)
    weather = getattr(application.state, "weather_scheduler", None)
    if advertisement is not None:
        try:
            await asyncio.to_thread(advertisement.start)
        except (OSError, NonUniqueNameException):
            logger.warning("Host advertisement unavailable; configured endpoint remains usable")
    if weather is not None:
        await asyncio.to_thread(weather.start)
    try:
        yield
    finally:
        if weather is not None:
            await asyncio.to_thread(weather.close)
        if advertisement is not None:
            await asyncio.to_thread(advertisement.close)


app = FastAPI(title="E-Ink Panel Simulator", version="0.4.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def simulator_page() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/manage", include_in_schema=False)
def management_page() -> FileResponse:
    return FileResponse(
        WEB_DIR / "manage.html",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/api/device/firmware/status")
def firmware_status() -> JSONResponse:
    return JSONResponse(
        content=firmware_offer.status(),
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/device/firmware/manifest")
def firmware_manifest() -> JSONResponse:
    manifest = firmware_offer.manifest()
    if manifest is None:
        raise HTTPException(status_code=503, detail="Firmware offer unavailable")
    return JSONResponse(
        content=manifest,
        headers={"Cache-Control": "no-store", "Connection": "close"},
    )


@app.get("/api/device/firmware/image")
def firmware_image() -> Response:
    image = firmware_offer.take_image()
    if image is None:
        if not firmware_offer.configured:
            raise HTTPException(status_code=503, detail="Firmware offer unavailable")
        raise HTTPException(status_code=409, detail="Firmware image not armed")
    return Response(
        content=image.body,
        media_type="application/octet-stream",
        headers={
            "Content-Length": str(image.size),
            "X-Firmware-Version": image.version,
            "X-Firmware-SHA256": image.sha256,
            "Cache-Control": "no-store",
            "Connection": "close",
        },
    )


@app.post("/api/device/firmware/arm")
def firmware_arm() -> JSONResponse:
    if not firmware_offer.arm():
        raise HTTPException(status_code=503, detail="Firmware offer unavailable")
    return JSONResponse(content=firmware_offer.status(), headers={"Cache-Control": "no-store"})


@app.post("/api/device/firmware/disarm")
def firmware_disarm() -> JSONResponse:
    firmware_offer.disarm()
    return JSONResponse(content=firmware_offer.status(), headers={"Cache-Control": "no-store"})


@app.get("/manifest.webmanifest", include_in_schema=False)
def pwa_manifest() -> FileResponse:
    return FileResponse(
        WEB_DIR / "manifest.webmanifest",
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/sw.js", include_in_schema=False)
def service_worker() -> FileResponse:
    return FileResponse(
        WEB_DIR / "sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


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


@app.post("/api/events", response_model=None)
def ingest_panel_event(
    event: PanelUpdateEvent,
) -> dict[str, Any] | JSONResponse:
    try:
        outcome = event_store.ingest(event)
    except InvalidPanelData as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    payload = outcome.as_dict()
    if outcome.reason == "out_of_order":
        return JSONResponse(status_code=409, content=payload)
    return payload


@app.get("/api/events/snapshots/{panel_type}/{source}")
def event_snapshot(panel_type: str, source: str) -> dict[str, Any]:
    if panel_type not in PANEL_TYPES:
        raise HTTPException(status_code=404, detail="Unknown panel type")
    snapshot = event_store.get_snapshot(panel_type, source)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot.as_dict()


@app.get("/api/pages")
def page_list() -> JSONResponse:
    payload = page_frames.status()
    return JSONResponse(
        content={"current": payload["page"], "pages": payload["pages"]},
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/pages/status")
def pages_status() -> JSONResponse:
    return JSONResponse(content=page_frames.status(), headers={"Cache-Control": "no-store"})


@app.get("/api/pages/{page_id}")
def read_page(page_id: str) -> JSONResponse:
    spec = file_page(page_id)
    document = page_state.load(spec.page_id)
    return JSONResponse(content=document.as_dict(), headers={"Cache-Control": "no-store"})


@app.put("/api/pages/{page_id}")
def write_page(page_id: str, body: PageWrite) -> JSONResponse:
    spec = editable_page(page_id)
    panel, payload = normalized_page_data(spec.page_id, body.data)
    try:
        render_assets(
            panel,
            {
                **payload,
                "revision": body.revision + 1,
                "updated_at": f"{page_frames.day_key()} 00:00",
                "day_key": page_frames.day_key(),
            },
        )
    except (ValueError, OSError) as error:
        raise HTTPException(status_code=422, detail="Page cannot be rendered") from error
    try:
        document = page_state.save(spec.page_id, payload, body.revision)
    except PageRevisionConflict as conflict:
        return JSONResponse(
            status_code=409,
            content=conflict.current.as_dict(),
            headers={"Cache-Control": "no-store"},
        )
    except PageTooLarge as error:
        raise HTTPException(status_code=422, detail="Page document exceeds storage budget") from error
    return JSONResponse(content=document.as_dict(), headers={"Cache-Control": "no-store"})


@app.post("/api/pages/weather/refresh")
def refresh_weather() -> JSONResponse:
    source = getattr(app.state, "weather_source", None)
    if source is None:
        content = {
            "ok": False,
            "stale": True,
            "revision": None,
            "updated_at": None,
            "error": "weather source unavailable",
        }
    else:
        content = source.refresh()
    return JSONResponse(content=content, headers={"Cache-Control": "no-store"})


@app.post("/api/pages/{page_id}/select")
def select_page(page_id: str) -> JSONResponse:
    try:
        payload = page_frames.select_page(page_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Unknown page") from error
    return JSONResponse(content=payload, headers={"Cache-Control": "no-store"})


@app.post("/api/pages/{page_id}/preview")
def preview_page(page_id: str, data: dict[str, Any] = Body(default_factory=dict)) -> Response:
    spec = file_page(page_id)
    document = page_state.load(spec.page_id)
    if spec.editable:
        merged = dict(data)
        merged.setdefault("revision", document.revision)
        merged.setdefault("updated_at", document.updated_at)
    else:
        merged = document.render_data()
    merged["day_key"] = page_frames.day_key()
    panel = create_page_panel(spec.page_id)
    try:
        normalized = panel.validate(merged)
        png, body = render_assets(panel, normalized.model_dump())
    except (ValidationError, ValueError, OSError) as error:
        raise HTTPException(status_code=422, detail="Invalid page data") from error
    version = hashlib.sha256(body).hexdigest()
    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store",
            "X-Frame-Version": version,
            "X-Frame-Format": FRAME_FORMAT,
            "X-Frame-Bytes": str(len(body)),
        },
    )


@app.get("/api/panels/progress/frame")
def progress_frame(request: Request) -> Response:
    values = request.headers.getlist("if-none-match")
    try:
        condition = parse_if_none_match(",".join(values) if values else None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Malformed If-None-Match") from exc
    frame = page_frames.current()
    if frame is None:
        raise HTTPException(status_code=503, detail="Progress frame unavailable")
    headers = {"ETag": frame.etag, "X-Frame-Format": frame.format, "Cache-Control": CACHE_CONTROL}
    if condition_matches(condition, frame):
        return Response(status_code=304, headers=headers)
    return Response(content=frame.body, media_type="application/octet-stream", headers=headers)


@app.post("/api/panels/progress/preview")
def progress_preview(event: PanelUpdateEvent) -> Response:
    if event.panel != "progress":
        raise HTTPException(status_code=422, detail="Progress event required")
    try:
        snapshot = build_snapshot(event)
        png, body = render_transport_assets(snapshot)
        frame = PublishedFrame.create(body, snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store",
            "X-Frame-Version": frame.etag[1:-1],
            "X-Frame-Format": frame.format,
            "X-Frame-Bytes": str(len(body)),
        },
    )


@app.get("/api/panels/progress/status")
def progress_status() -> JSONResponse:
    return JSONResponse(content=page_frames.legacy_status(), headers={"Cache-Control": "no-store"})


@app.post("/api/panels/progress/device-report")
def progress_device_report(report: DeviceReport) -> dict[str, bool]:
    if not page_frames.report(report):
        raise HTTPException(status_code=409, detail="Frame is not current or acceptance is missing")
    firmware_offer.observe_device_version(report.firmware_version)
    return {"recorded": True}


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


def main(argv=None):
    import uvicorn

    parser = argparse.ArgumentParser(description="E-Ink Host HTTP server")
    parser.add_argument("--host", default="127.0.0.1", help="Explicit bind IPv4; LAN binding advertises discovery")
    parser.add_argument("--port", type=int, default=8000)
    options = parser.parse_args(argv)
    address = IPv4Address(options.host)
    if not 1 <= options.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    app.state.host_advertisement = (
        None if address.is_loopback else HostAdvertisement(str(address), options.port)
    )
    weather_config = None if os.environ.get("EINK_WEATHER") == "0" else load_weather_config()
    if weather_config is None:
        app.state.weather_source = None
        app.state.weather_scheduler = None
    else:
        app.state.weather_source = WeatherSource(page_state, weather_config)
        app.state.weather_scheduler = WeatherScheduler(app.state.weather_source)
    uvicorn.run(app, host=str(address), port=options.port, reload=False)


if __name__ == "__main__":
    main()
