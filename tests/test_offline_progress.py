"""STEP016C renderer-only contract tests; no hardware or transport exports."""

import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from adapters.offline_progress import parse_offline_progress
from panels.base import DisplayConfig
from panels.design_system import get_font
from panels.offline_progress import render_offline
from panels.progress import ProgressPanel
from panels.render_validation import CheckedDraw

EXAMPLE = Path(__file__).resolve().parents[1] / "data/progress_offline.json"


def payload(**changes):
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data.update(changes)
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def test_mapping_defaults_and_no_clock(monkeypatch):
    data = json.loads(payload())
    data.pop("tags")
    data.pop("description")
    model = parse_offline_progress(json.dumps(data).encode())
    assert model.title == data["project"]
    assert model.current_step == data["step"]
    assert model.updated_at == "2026-09-13 14:30"
    assert model.source == "Local JSON"
    assert model.tags == [] and model.description == ""
    monkeypatch.setattr(ProgressPanel, "_current_time", lambda _: pytest.fail("clock fallback"))
    ProgressPanel().render(model.model_dump(), DisplayConfig(), "eink", strict=True)


@pytest.mark.parametrize("value", [True, False, 60.0, "60", -1, 101, None, [], {}])
def test_reject_progress(value):
    with pytest.raises(ValueError):
        parse_offline_progress(payload(progress=value))


@pytest.mark.parametrize("value", [0, 100])
def test_progress_boundaries(value):
    model = parse_offline_progress(payload(progress=value))
    assert model.progress == value
    ProgressPanel().render(model.model_dump(), DisplayConfig(), "eink", strict=True)


@pytest.mark.parametrize("field", ["project", "step", "progress", "status", "timestamp"])
def test_required(field):
    data = json.loads(payload())
    del data[field]
    with pytest.raises(ValueError):
        parse_offline_progress(json.dumps(data).encode())


@pytest.mark.parametrize("changes", [
    {"project": " "}, {"project": 1}, {"step": None}, {"step": ""},
    {"status": " "}, {"status": False}, {"description": None},
    {"tags": None}, {"tags": "a"}, {"tags": ["a", "b", "c"]},
    {"tags": [""]}, {"tags": [1]}, {"tags": [" "]},
    {"title": "alias"}, {"current_step": "alias"}, {"updated_at": "alias"},
    {"source": "override"}, {"extra": 1},
])
def test_invalid_fields(changes):
    with pytest.raises(ValueError):
        parse_offline_progress(payload(**changes))


@pytest.mark.parametrize("value", [
    None, "", "2026-02-30 10:00", "2026-02-29 10:00", "0000-01-01 00:00",
    "2026-9-13 14:30", "2026-09-13T14:30", "2026-09-13 24:00",
    "2026-09-13 14:60", "2026-09-13 14:30:00", "2026-09-13 14:30+08:00",
    " 2026-09-13 14:30", 123,
])
def test_invalid_time(value):
    with pytest.raises(ValueError):
        parse_offline_progress(payload(timestamp=value))


def test_leap_day_and_whitespace():
    data = parse_offline_progress(payload(timestamp="2024-02-29 00:00", project=" 项目 ", tags=[" 离线 "]))
    assert data.updated_at == "2024-02-29 00:00"
    assert data.title == "项目" and data.tags == ["离线"]


@pytest.mark.parametrize("content", [b"[]", b"null", b"{", b'"text"', b"\xff", b'{"project":"A","project":"B"}'])
def test_bad_json(content):
    with pytest.raises(ValueError):
        parse_offline_progress(content)


@pytest.mark.parametrize("field", ["project", "step", "description", "status", "tags"])
def test_long_text_rejected(field):
    value = ["长" * 60] if field == "tags" else "长" * 60
    model = parse_offline_progress(payload(**{field: value}))
    with pytest.raises(ValueError, match="Layout"):
        ProgressPanel().render(model.model_dump(), DisplayConfig(), "eink", strict=True)


@pytest.mark.parametrize("text", ["\u0378", "line\nbreak", "\U0010ffff"])
def test_missing_glyph_or_control_rejected(text):
    model = parse_offline_progress(payload(description=text))
    with pytest.raises(ValueError, match="Font"):
        ProgressPanel().render(model.model_dump(), DisplayConfig(), "eink", strict=True)


def test_missing_font_rejected():
    checked = CheckedDraw(ImageDraw.Draw(Image.new("L", (400, 300))))
    with pytest.raises(ValueError, match="font file"):
        checked.text((10, 10), "abc", font=ImageFont.load_default())


def test_font_without_chinese_rejected():
    checked = CheckedDraw(ImageDraw.Draw(Image.new("L", (400, 300))))
    with pytest.raises(ValueError, match="missing glyph"):
        checked.text((10, 10), "中文", font=get_font(13, mono=True))


def test_io_failure_is_not_published(tmp_path, monkeypatch):
    original_open = Path.open

    def fail_manifest(path, *args, **kwargs):
        if path.name == "renderer-manifest.json":
            raise OSError("injected write failure")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_manifest)
    with pytest.raises(OSError, match="injected"):
        render_offline(EXAMPLE, "incomplete", output_root=tmp_path)
    assert not (tmp_path / "incomplete/renderer-manifest.json").exists()
    with pytest.raises(FileExistsError):
        render_offline(EXAMPLE, "incomplete", output_root=tmp_path)


def test_overlap_rejected():
    checked = CheckedDraw(ImageDraw.Draw(Image.new("L", (400, 300))))
    checked.text((10, 10), "中文", font=get_font(13))
    with pytest.raises(ValueError, match="overlapping"):
        checked.text((10, 10), "中文", font=get_font(13))


@pytest.mark.parametrize("status,expected", [("进行中", "页面验证"), ("WAITING DATA", "WAITING DATA"), ("UPDATE FAILED", "UPDATE FAILED")])
def test_main_title_and_status_branches(monkeypatch, status, expected):
    calls = []
    original = ImageDraw.ImageDraw.text

    def record(draw, xy, text, *args, **kwargs):
        calls.append((xy, text))
        return original(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", record)
    ProgressPanel().render(parse_offline_progress(payload(status=status)).model_dump(), DisplayConfig())
    assert ((159, 42), expected) in calls


def test_output_consistency_and_chinese(tmp_path):
    first = render_offline(EXAMPLE, "first", output_root=tmp_path)
    second = render_offline(EXAMPLE, "second", output_root=tmp_path)
    assert sorted(p.name for p in first.iterdir()) == ["progress.preview.png", "renderer-manifest.json"]
    with Image.open(first / "progress.preview.png") as image, Image.open(second / "progress.preview.png") as other:
        assert image.format == "PNG" and image.size == (400, 300) and image.mode == "1"
        assert set(image.getdata()) == {0, 255}
        assert image.tobytes() == other.tobytes()
        manifest = json.loads((first / "renderer-manifest.json").read_text(encoding="utf-8"))
        audit = manifest["render_audit"]
        for entry in audit["texts"]:
            pixels = set(image.crop(entry["bbox"]).getdata())
            assert pixels == {0, 255}, entry["text"]  # actual ink after 1-bit conversion
        assert any(t["text"] == "电子纸项目" for t in audit["texts"])
        assert any(t["text"] == "页面验证" and t["bbox"][0] == 159 for t in audit["texts"])
    png = (first / "progress.preview.png").read_bytes()
    assert manifest["image"]["sha256"] == hashlib.sha256(png).hexdigest()
    assert manifest["image"]["size"] == len(png)
    assert manifest["input"]["sha256"] == hashlib.sha256(EXAMPLE.read_bytes()).hexdigest()
    for font, digest in audit["fonts"].items():
        assert Path(font).is_absolute() and Path(font).is_file()
        assert hashlib.sha256(Path(font).read_bytes()).hexdigest() == digest
    assert manifest["stage"] == "STEP016C_RENDERER_ONLY"
    assert "VISUAL_REVIEW_REQUIRED" in manifest["status"]


def test_conflict_and_failure_no_overwrite(tmp_path):
    destination = render_offline(EXAMPLE, "old", output_root=tmp_path)
    original = {p.name: p.read_bytes() for p in destination.iterdir()}
    with pytest.raises(FileExistsError):
        render_offline(EXAMPLE, "old", output_root=tmp_path)
    invalid = tmp_path / "invalid.json"
    invalid.write_bytes(payload(step="长" * 80))
    with pytest.raises(ValueError):
        render_offline(invalid, "failed", output_root=tmp_path)
    assert not (tmp_path / "failed").exists()
    assert original == {p.name: p.read_bytes() for p in destination.iterdir()}


@pytest.mark.parametrize("run_id", ["../bad", "..", "a/b", "a\\b", "", ".hidden"])
def test_bad_run_id(tmp_path, run_id):
    with pytest.raises(ValueError):
        render_offline(EXAMPLE, run_id, output_root=tmp_path)
