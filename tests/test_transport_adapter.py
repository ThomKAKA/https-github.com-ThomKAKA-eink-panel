"""PC transport and static integration checks; no hardware execution."""

import configparser
import hashlib
import json
import re
from pathlib import Path

import pytest

from panels.frame_converter import make_header
from panels.transport_adapter import FORMAT, adapt_frame, logical_to_transport, read_logical_source


ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def synthetic():
    return bytes((17 * y + 29 * b + y * b % 251) % 256 for y in range(300) for b in range(50))


@pytest.fixture
def source(tmp_path):
    folder = tmp_path / "b1"
    folder.mkdir()
    logical = synthetic()
    header = make_header(logical, "preview.png", "a" * 64)
    record = {
        "stage": "STEP016D_B1_LOGICAL_FRAME_ONLY",
        "status": "CONVERSION_COMPLETE_NOT_H1_TRANSPORT_READY",
        "coordinate_frame": "L", "pixel_mapping": "unchanged", "format": dict(FORMAT),
        "input": {"file": "preview.png", "size": 123, "sha256": "a" * 64},
        "outputs": {name: {"size": len(data), "sha256": digest(data)} for name, data in (
            ("progress.logical.raw", logical), ("progress_logical_frame.h", header))},
        "array": {"symbol": "progress_logical_frame", "length": 15000,
                  "byte_sequence_sha256": digest(logical)},
    }
    (folder / "progress.logical.raw").write_bytes(logical)
    (folder / "progress_logical_frame.h").write_bytes(header)
    (folder / "converter-manifest.json").write_text(json.dumps(record))
    return folder


def array_bytes(header):
    body = header.split(b"progress_frame[] = {", 1)[1].split(b"};", 1)[0]
    return bytes(int(value, 16) for value in re.findall(rb"0x([0-9A-F]{2})", body))


@pytest.mark.parametrize("field,value", [
    ("stage", "wrong"), ("status", "partial"), ("coordinate_frame", "T"),
    ("pixel_mapping", "flipped"), ("format", {}), ("outputs", {}), ("array", {}),
    ("input", {}), ("input", {"file": "x", "size": True, "sha256": "a" * 64}),
])
def test_bad_manifest(source, tmp_path, field, value):
    path = source / "converter-manifest.json"
    record = json.loads(path.read_text())
    record[field] = value
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        adapt_frame(source, "rejected", output_root=tmp_path)
    assert not (tmp_path / "rejected").exists()


def test_duplicate_manifest_key(source):
    path = source / "converter-manifest.json"
    path.write_text('{"coordinate_frame":"L",' + path.read_text()[1:])
    with pytest.raises(ValueError, match="duplicate"):
        read_logical_source(source)


@pytest.mark.parametrize("name", ["converter-manifest.json", "progress.logical.raw", "progress_logical_frame.h"])
def test_missing_source_file(source, tmp_path, monkeypatch, name):
    original = Path.read_bytes

    def missing(path):
        if path.name == name:
            raise FileNotFoundError(name)
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", missing)
    with pytest.raises(FileNotFoundError):
        adapt_frame(source, "missing", output_root=tmp_path)
    assert not (tmp_path / "missing").exists()


@pytest.mark.parametrize("field,value", [("width", 399), ("height", 299), ("bit_depth", True),
                                         ("stride", 49), ("polarity", "inverted")])
def test_format_rejected(source, field, value):
    path = source / "converter-manifest.json"
    record = json.loads(path.read_text())
    record["format"][field] = value
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        read_logical_source(source)


@pytest.mark.parametrize("name", ["progress.logical.raw", "progress_logical_frame.h"])
def test_corrupted_file(source, name):
    path = source / name
    path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(ValueError):
        read_logical_source(source)


def test_header_mismatch_even_with_updated_file_hash(source):
    path = source / "progress_logical_frame.h"
    altered = path.read_bytes().replace(b"0x00", b"0xFF", 1)
    path.write_bytes(altered)
    manifest = source / "converter-manifest.json"
    record = json.loads(manifest.read_text())
    record["outputs"][path.name] = {"size": len(altered), "sha256": digest(altered)}
    manifest.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        read_logical_source(source)


@pytest.mark.parametrize("length", [0, 14999, 15001])
def test_wrong_length(length):
    with pytest.raises(ValueError):
        logical_to_transport(bytes(length))


def test_oracle_and_golden_hashes():
    logical = synthetic()
    transport = logical_to_transport(logical)
    source = [int(bit) for byte in logical for bit in f"{byte:08b}"]
    result = [int(bit) for byte in transport for bit in f"{byte:08b}"]
    for y in range(300):
        for x in range(400):
            assert result[y * 400 + x] == source[(299 - y) * 400 + x]
    assert logical_to_transport(transport) == logical
    assert digest(logical) == "6ef4696f9124b264ec2742728f3398ecf1d584a3855719746974f6d8af1b339a"
    assert digest(transport) == "a0ade0ea621dc91f1a1a6f362d35b430981e8540b902fb83527f53cc8dcbe6b3"


@pytest.mark.parametrize("x,y", [(0, 0), (7, 1), (8, 298), (399, 299)])
def test_single_pixel(x, y):
    logical = bytearray(b"\xff" * 15000)
    logical[y * 50 + x // 8] &= ~(0x80 >> (x % 8))
    transport = logical_to_transport(logical)
    expected = bytearray(b"\xff" * 15000)
    expected[(299 - y) * 50 + x // 8] &= ~(0x80 >> (x % 8))
    assert transport == expected


def test_publication_and_repeatability(source, tmp_path):
    first = adapt_frame(source, "first", output_root=tmp_path)
    second = adapt_frame(source, "second", output_root=tmp_path)
    metadata = json.loads((first / "transport-manifest.json").read_text())
    assert metadata["coordinate_frame"] == "T"
    assert metadata["source"]["b1_manifest_sha256"] == digest((source / "converter-manifest.json").read_bytes())
    assert metadata["source"]["logical_raw_sha256"] == digest(synthetic())
    for name, entry in metadata["outputs"].items():
        data = (first / name).read_bytes()
        assert entry == {"size": len(data), "sha256": digest(data)}
        assert data == (second / name).read_bytes()
    raw = (first / "progress.frame.raw").read_bytes()
    assert array_bytes((first / "progress_frame.h").read_bytes()) == raw
    assert metadata["array"]["length"] == len(raw) == 15000
    assert metadata["array"]["byte_sequence_sha256"] == digest(raw)
    assert "transport-manifest.json" not in metadata["outputs"]
    with pytest.raises(FileExistsError):
        adapt_frame(source, "first", output_root=tmp_path)
    assert (first / "progress.frame.raw").read_bytes() == raw


@pytest.mark.parametrize("run_id", ["", "..", "../x", "a/b", "a\\b", "x" * 81])
def test_invalid_run_id(source, tmp_path, run_id):
    with pytest.raises(ValueError):
        adapt_frame(source, run_id, output_root=tmp_path)


@pytest.mark.parametrize("failed", ["progress.frame.raw", "progress_frame.h", "transport-manifest.pending"])
def test_write_failure(source, tmp_path, monkeypatch, failed):
    original = Path.open

    def fail(path, *args, **kwargs):
        if path.name == failed:
            raise OSError("injected failure")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail)
    with pytest.raises(OSError):
        adapt_frame(source, "failed", output_root=tmp_path)
    assert not (tmp_path / "failed/transport-manifest.json").exists()
    with pytest.raises(FileExistsError):
        adapt_frame(source, "failed", output_root=tmp_path)


def test_embedded_sample_matches_source_hash_contract():
    header = (ROOT / "hardware/gdey042t81_esp32/src/progress/progress_frame.h").read_bytes()
    raw = array_bytes(header)
    assert len(raw) == 15000
    assert digest(logical_to_transport(raw)) == "b482dfb702fb425b9734bc1824ed02587fd428516b0aea2edacfaa3718e54209"
    assert digest(raw).encode() in header
    assert b"progress_frame_coordinate = 'T'" in header


def test_entry_isolation_and_stop_structure():
    project = ROOT / "hardware/gdey042t81_esp32"
    config = configparser.ConfigParser(interpolation=None)
    config.read(project / "platformio.ini")
    env = config["env:esp32-m1-progress"]
    assert env["extends"] == "env:esp32-m1"
    assert env["build_src_filter"] == "-<*> +<progress/main.cpp>"
    assert "-I.build/progress-private" in env["build_flags"]
    for other in ("env:esp32dev", "env:esp32-m1", "env:esp32-m1-h1"):
        assert "progress" not in str(dict(config[other]))
    code = (project / "src/progress/main.cpp").read_text()
    assert code.startswith("#ifdef EINK_PROGRESS_EMBEDDED_TEST")
    assert '"../h1/atomic_display.h"' in code
    assert "progress_frame_coordinate == 'T'" in code
    assert "progress_frame_length == eink::h1::kBytes" in code
    assert code.index("std::memcpy") < code.index("SPI.begin") < code.index("display.coldInit")
    assert code.count("display.refreshOnce()") == 1
    tail = code.split("display.refreshOnce();", 1)[1]
    assert "display." not in tail and "SPI." not in tail
    assert "void loop() { delay(1000); }" in code
    assert "std::array<std::uint8_t, eink::h1::kBytes> frame_ram{};" in code
