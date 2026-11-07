"""Logical-frame tests use independent pixel decoding, not hardware."""

import hashlib
import io
import json
import re
from pathlib import Path

import pytest
from PIL import Image

from panels.frame_converter import HEADER_NAME, RAW_NAME, convert_frame, make_header, png_to_logical_raw


def png(image=None, **options):
    buffer = io.BytesIO()
    (image if image is not None else Image.new("1", (400, 300), 255)).save(buffer, format="PNG", **options)
    return buffer.getvalue()


@pytest.mark.parametrize("size", [(399, 300), (400, 299), (300, 400), (1, 1)])
def test_wrong_dimensions(size):
    with pytest.raises(ValueError):
        png_to_logical_raw(png(Image.new("1", size)))


@pytest.mark.parametrize("mode", ["L", "P", "RGB", "RGBA"])
def test_wrong_mode(mode):
    with pytest.raises(ValueError):
        png_to_logical_raw(png(Image.new(mode, (400, 300))))


def test_non_png():
    stream = io.BytesIO()
    Image.new("1", (400, 300)).save(stream, format="BMP")
    with pytest.raises(ValueError, match="expected PNG"):
        png_to_logical_raw(stream.getvalue())


@pytest.mark.parametrize("content", [b"", b"not a PNG", png()[:50], png()[:-20]])
def test_corrupt_png(content):
    with pytest.raises((ValueError, OSError, SyntaxError)):
        png_to_logical_raw(content)


def test_animation():
    content = png(Image.new("1", (400, 300)), save_all=True,
                  append_images=[Image.new("1", (400, 300), 255)], duration=100)
    with pytest.raises(ValueError):
        png_to_logical_raw(content)


def test_transparency():
    with pytest.raises(ValueError, match="transparency"):
        png_to_logical_raw(png(transparency=0))


@pytest.mark.parametrize("orientation", [0, 2, 3, 4, 5, 6, 7, 8])
def test_orientation_rejected(orientation):
    exif = Image.Exif()
    exif[274] = orientation
    with pytest.raises(ValueError, match="orientation"):
        png_to_logical_raw(png(exif=exif))


def test_default_orientation():
    exif = Image.Exif()
    exif[274] = 1
    assert png_to_logical_raw(png(exif=exif)) == b"\xff" * 15000


@pytest.mark.parametrize("value,expected", [(0, 0), (255, 255)])
def test_solid(value, expected):
    assert png_to_logical_raw(png(Image.new("1", (400, 300), value))) == bytes([expected]) * 15000


def test_asymmetric_pixel_mapping_and_array():
    image = Image.new("1", (400, 300), 255)
    for y in range(300):
        for x in range(400):
            if (x * 3 + y * 7) % 19 < 5:
                image.putpixel((x, y), 0)
    for xy in [(0, 0), (7, 0), (8, 0), (399, 0), (0, 299), (399, 299)]:
        image.putpixel(xy, 0)
    raw = png_to_logical_raw(png(image))
    assert len(raw) == 15000
    # Independent sequential decode verifies all 120000 logical pixels and bit order.
    decoded = [255 if byte & (1 << shift) else 0 for byte in raw for shift in range(7, -1, -1)]
    assert decoded == list(image.getdata())
    assert raw[0] & 0x81 == 0 and raw[1] & 0x80 == 0
    assert raw[49] & 1 == 0 and raw[-1] & 1 == 0
    header = make_header(raw, "source.png", "a" * 64).decode("ascii")
    body = header.split("progress_logical_frame[] = {", 1)[1].split("};", 1)[0]
    values = bytes(int(v, 16) for v in re.findall(r"0x([0-9A-F]{2})", body))
    assert len(values) == 15000 and values == raw
    assert "sizeof(progress_logical_frame)" in header
    assert "#include <stdint.h>" in header and "#include <stddef.h>" in header
    assert "#ifndef EINK_PROGRESS_LOGICAL_FRAME_H" in header
    assert "no L-to-T adaptation" in header


def test_header_rejects_short_frame():
    with pytest.raises(ValueError):
        make_header(b"", "x.png", "a" * 64)


def test_filename_cannot_escape_comment():
    header = make_header(b"\xff" * 15000, "evil*/\nname.png", "a" * 64).decode()
    assert "evil*/" not in header and "\\nname.png" in header


def test_manifest_and_repeatability(tmp_path):
    source = tmp_path / "source.png"
    source.write_bytes(png())
    first = convert_frame(source, "first", output_root=tmp_path)
    second = convert_frame(source, "second", output_root=tmp_path)
    assert sorted(p.name for p in first.iterdir()) == sorted([RAW_NAME, HEADER_NAME, "converter-manifest.json"])
    metadata = json.loads((first / "converter-manifest.json").read_text())
    assert metadata["coordinate_frame"] == "L" and metadata["pixel_mapping"] == "unchanged"
    assert metadata["input"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert metadata["input"]["size"] == source.stat().st_size
    for name in [RAW_NAME, HEADER_NAME]:
        content = (first / name).read_bytes()
        assert metadata["outputs"][name] == {"size": len(content), "sha256": hashlib.sha256(content).hexdigest()}
        assert content == (second / name).read_bytes()
    assert metadata["array"]["length"] == 15000
    assert metadata["array"]["byte_sequence_sha256"] == metadata["outputs"][RAW_NAME]["sha256"]
    assert "converter-manifest.json" not in metadata["outputs"]
    with pytest.raises(FileExistsError):
        convert_frame(source, "first", output_root=tmp_path)
    assert (first / RAW_NAME).read_bytes() == (second / RAW_NAME).read_bytes()


@pytest.mark.parametrize("run_id", ["", "..", "../x", "x/y", "x\\y", ".hidden", "x" * 81])
def test_bad_run_id(tmp_path, run_id):
    with pytest.raises(ValueError):
        convert_frame(tmp_path / "absent.png", run_id, output_root=tmp_path)


def test_invalid_input_leaves_no_directory(tmp_path):
    source = tmp_path / "bad.png"
    source.write_bytes(b"invalid")
    with pytest.raises(OSError):
        convert_frame(source, "failed", output_root=tmp_path)
    assert not (tmp_path / "failed").exists()


@pytest.mark.parametrize("failure_name", [RAW_NAME, HEADER_NAME, "converter-manifest.pending"])
def test_write_failure_no_completion(tmp_path, monkeypatch, failure_name):
    source = tmp_path / "source.png"
    source.write_bytes(png())
    original = Path.open

    def fail(path, *args, **kwargs):
        if path.name == failure_name:
            raise OSError("injected failure")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail)
    with pytest.raises(OSError, match="injected"):
        convert_frame(source, "failed", output_root=tmp_path)
    assert not (tmp_path / "failed/converter-manifest.json").exists()
    with pytest.raises(FileExistsError):
        convert_frame(source, "failed", output_root=tmp_path)
