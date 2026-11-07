from io import BytesIO
import logging

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from server.main import app


client = TestClient(app)

DATA = {
    "title": "CODING",
    "progress": 72,
    "current_step": "接口改动前",
    "status": "先确认",
    "description": "协议兼容需人工确认",
    "tags": ["观点通过", "暂停继续"],
    "source": "AI Copilot",
}


def test_httpx_request_urls_are_not_logged_at_info() -> None:
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING


def test_simulator_page_loads() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "E-Ink Panel Simulator" in response.text
    assert 'data-panel="stats"' in response.text
    assert 'data-panel="flow"' in response.text
    assert "DATA SOURCE" in response.text
    assert "AUTO REFRESH" in response.text


def test_progress_samples_include_phase_one_states() -> None:
    response = client.get("/api/samples/progress")

    assert response.status_code == 200
    assert [sample["id"] for sample in response.json()] == [
        "default",
        "waiting",
        "error",
    ]
    assert "updated_at" not in response.json()[0]["data"]


@pytest.mark.parametrize("panel_type", ["stats", "flow"])
def test_phase_two_samples_include_three_states(panel_type: str) -> None:
    response = client.get(f"/api/samples/{panel_type}")

    assert response.status_code == 200
    assert [sample["id"] for sample in response.json()] == [
        "default",
        "waiting",
        "error",
    ]


def test_png_render_endpoint() -> None:
    response = client.post(
        "/api/panels/progress/render?mode=normal&format=png",
        json=DATA,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["x-panel-width"] == "400"
    assert response.headers["x-rendered-at"]
    image = Image.open(BytesIO(response.content))
    assert image.size == (400, 300)
    assert image.mode == "L"


def test_eink_bmp_render_endpoint() -> None:
    response = client.post(
        "/api/panels/progress/render?mode=eink&format=bmp",
        json=DATA,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/bmp"
    assert response.content[:2] == b"BM"
    image = Image.open(BytesIO(response.content))
    assert image.size == (400, 300)
    assert image.mode == "1"


def test_invalid_payload_still_returns_an_image() -> None:
    response = client.post(
        "/api/panels/progress/render?mode=normal&format=png",
        json={"progress": "not-a-number"},
    )

    assert response.status_code == 200
    assert Image.open(BytesIO(response.content)).size == (400, 300)


@pytest.mark.parametrize("panel_type", ["progress", "stats", "flow"])
def test_all_panels_render_png(panel_type: str) -> None:
    samples = client.get(f"/api/samples/{panel_type}").json()
    response = client.post(
        f"/api/panels/{panel_type}/render?mode=normal&format=png",
        json=samples[0]["data"],
    )

    assert response.status_code == 200
    assert response.headers["x-panel-type"] == panel_type
    image = Image.open(BytesIO(response.content))
    assert image.size == (400, 300)
    assert image.mode == "L"


@pytest.mark.parametrize("panel_type", ["progress", "stats", "flow"])
def test_all_panels_render_one_bit_bmp(panel_type: str) -> None:
    samples = client.get(f"/api/samples/{panel_type}").json()
    response = client.post(
        f"/api/panels/{panel_type}/render?mode=eink&format=bmp",
        json=samples[0]["data"],
    )

    assert response.status_code == 200
    image = Image.open(BytesIO(response.content))
    assert image.size == (400, 300)
    assert image.mode == "1"


def test_unknown_panel_returns_404() -> None:
    assert client.get("/api/samples/unknown").status_code == 404
    assert client.post("/api/panels/unknown/render", json={}).status_code == 404


@pytest.mark.parametrize(
    "query",
    ["mode=animated&format=png", "mode=normal&format=gif"],
)
def test_invalid_render_option_returns_400(query: str) -> None:
    response = client.post(f"/api/panels/progress/render?{query}", json=DATA)

    assert response.status_code == 400


@pytest.mark.parametrize("panel_type", ["progress", "stats", "flow"])
def test_each_panel_lists_three_data_sources(panel_type: str) -> None:
    response = client.get(f"/api/data-sources/{panel_type}")

    assert response.status_code == 200
    sources = response.json()
    assert [source["type"] for source in sources] == [
        "mock",
        "local_json",
        "http_json",
    ]
    assert sources[0]["default"] is True


@pytest.mark.parametrize(
    ("source_id", "expected_field"),
    [
        ("progress_mock", "progress"),
        ("stats_mock", "primary_value"),
        ("flow_mock", "stages"),
        ("progress_local", "progress"),
        ("stats_local", "primary_value"),
        ("flow_local", "stages"),
    ],
)
def test_mock_and_local_sources_refresh(source_id: str, expected_field: str) -> None:
    response = client.post(
        f"/api/data-sources/{source_id}/refresh",
        json={"sample_id": "default", "interval_seconds": 300},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ONLINE"
    assert expected_field in payload["data"]
    assert payload["next_refresh"]


def test_unknown_data_source_returns_404() -> None:
    response = client.post("/api/data-sources/missing/refresh", json={})

    assert response.status_code == 404


@pytest.mark.parametrize("interval", [-1, 6, 301, "5"])
def test_refresh_rejects_unsupported_interval(interval) -> None:
    response = client.post(
        "/api/data-sources/stats_mock/refresh",
        json={"interval_seconds": interval},
    )

    assert response.status_code == 400
