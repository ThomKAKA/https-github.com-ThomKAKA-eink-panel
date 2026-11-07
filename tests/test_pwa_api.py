import re
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from server.main import app


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def test_manifest_serves_android_pwa_metadata() -> None:
    response = client.get("/manifest.webmanifest")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/manifest+json")
    body = response.json()
    assert body["name"] == "E-Ink 本地管理"
    assert body["short_name"] == "E-Ink"
    assert body["start_url"] == "/manage"
    assert body["scope"] == "/"
    assert body["display"] == "standalone"
    assert body["theme_color"] == "#000000"
    assert body["background_color"] == "#ffffff"
    assert body["lang"] == "zh-CN"
    assert {icon["sizes"] for icon in body["icons"]} >= {"192x192", "512x512"}
    for icon in body["icons"]:
        assert icon["type"] == "image/png"
        assert icon["src"].startswith("/static/icons/")
        assert client.get(icon["src"]).status_code == 200


def test_pwa_icons_have_expected_png_sizes() -> None:
    for name, size in (
        ("icon-192.png", (192, 192)),
        ("icon-512.png", (512, 512)),
    ):
        response = client.get(f"/static/icons/{name}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        image = Image.open(BytesIO(response.content))
        assert image.format == "PNG"
        assert image.size == size


def test_service_worker_is_served_from_root_without_cache() -> None:
    response = client.get("/sw.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "no-cache" in response.headers["cache-control"]
    assert "eink-shell" in response.text


def test_service_worker_shell_assets_are_served() -> None:
    text = (ROOT / "web" / "sw.js").read_text(encoding="utf-8")
    block = re.search(r"const SHELL_ASSETS = \[(.*?)\];", text, re.S)

    assert block is not None
    offline = re.search(r'const OFFLINE_URL = "([^"]+)"', text).group(1)
    tokens = re.findall(r'"([^"]+)"|\b(OFFLINE_URL)\b', block.group(1))
    assets = [literal or offline for literal, name in tokens if literal or name]
    assert "/manage" in assets
    assert offline in assets
    for asset in assets:
        assert client.get(asset).status_code == 200, asset


def test_management_page_disables_http_reuse_cache() -> None:
    response = client.get("/manage")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"


def test_management_page_declares_android_pwa_entry() -> None:
    response = client.get("/manage")

    assert response.status_code == 200
    for marker in (
        'rel="manifest"',
        'href="/manifest.webmanifest"',
        'name="theme-color"',
        'id="install-hint"',
        'id="install-hint-text"',
        'id="install-app"',
    ):
        assert marker in response.text


def test_offline_page_is_honest_about_cached_state() -> None:
    response = client.get("/static/offline.html")

    assert response.status_code == 200
    assert "Host 不可达" in response.text
    assert "不会显示或重放缓存的设备状态" in response.text


def test_pwa_routes_do_not_change_existing_pages() -> None:
    assert client.get("/").status_code == 200
    assert client.get("/api/panels/progress/status").status_code == 200
