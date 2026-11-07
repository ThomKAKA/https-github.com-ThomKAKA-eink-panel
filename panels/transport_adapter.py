"""Manual PC-only B1 logical frame to fixed-H1 transport frame adapter."""

import argparse
import json
import platform
import re
from pathlib import Path

from panels.frame_converter import make_header as make_logical_header, sha256


OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "artifacts/step016-transport-adapter"
RAW_NAME = "progress.frame.raw"
HEADER_NAME = "progress_frame.h"
FORMAT = {"width": 400, "height": 300, "bit_depth": 1, "stride": 50,
          "order": "row-major, MSB-first", "polarity": "0 black / 1 white"}


def logical_to_transport(logical: bytes) -> bytes:
    if len(logical) != 15000:
        raise ValueError("FRAME_INVALID: expected 15000 bytes")
    return b"".join(logical[y * 50:(y + 1) * 50] for y in range(299, -1, -1))


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("SOURCE_INVALID: duplicate manifest key")
        result[key] = value
    return result


def read_logical_source(directory: Path):
    """Accept the fixed B1 publication only; never infer direction from bytes."""
    directory = Path(directory)
    metadata = (directory / "converter-manifest.json").read_bytes()
    record = json.loads(metadata, object_pairs_hook=_unique_object)
    logical = (directory / "progress.logical.raw").read_bytes()
    header = (directory / "progress_logical_frame.h").read_bytes()
    try:
        valid = (
            record["stage"] == "STEP016D_B1_LOGICAL_FRAME_ONLY"
            and record["status"] == "CONVERSION_COMPLETE_NOT_H1_TRANSPORT_READY"
            and record["coordinate_frame"] == "L"
            and record["pixel_mapping"] == "unchanged"
            and record["format"] == FORMAT
            and all(type(record["format"][key]) is int
                    for key in ("width", "height", "bit_depth", "stride"))
            and len(logical) == 15000
            and record["array"] == {"symbol": "progress_logical_frame", "length": 15000,
                                    "byte_sequence_sha256": sha256(logical)}
        )
        for name, data in (("progress.logical.raw", logical), ("progress_logical_frame.h", header)):
            valid = valid and record["outputs"][name] == {"size": len(data), "sha256": sha256(data)}
        origin = record["input"]
        valid = (valid and isinstance(origin["file"], str) and bool(origin["file"])
                 and type(origin["size"]) is int and origin["size"] > 0
                 and isinstance(origin["sha256"], str)
                 and re.fullmatch(r"[0-9a-f]{64}", origin["sha256"]) is not None)
        if not valid or header != make_logical_header(logical, origin["file"], origin["sha256"]):
            raise ValueError("SOURCE_INVALID: B1 format, direction, hash or array mismatch")
    except (KeyError, TypeError) as error:
        raise ValueError("SOURCE_INVALID: incomplete B1 manifest") from error
    # Input PNG provenance is inherited from B1, not reauthenticated by this raw API.
    return logical, metadata, origin


def make_transport_header(transport: bytes, logical_hash: str, source_manifest_hash: str) -> bytes:
    if len(transport) != 15000:
        raise ValueError("FRAME_INVALID: expected 15000 bytes")
    lines = [
        "#ifndef EINK_PROGRESS_TRANSPORT_FRAME_H",
        "#define EINK_PROGRESS_TRANSPORT_FRAME_H",
        "#include <stdint.h>", "#include <stddef.h>",
        "/* Transport frame T; PC L-to-T row reversal exactly once.",
        " * Source: B1 progress.logical.raw + converter-manifest.json.",
        f" * B1 manifest SHA256: {source_manifest_hash}",
        f" * Logical L SHA256: {logical_hash}",
        f" * Transport T array/raw SHA256: {sha256(transport)}",
        " * MCU copies unchanged; fixed H1 mirror_y=true remains required.",
        " * Software integration candidate, NOT physical display verification.",
        " */",
        "static const unsigned progress_frame_width = 400;",
        "static const unsigned progress_frame_height = 300;",
        "static const unsigned progress_frame_stride = 50;",
        "static const char progress_frame_coordinate = 'T';",
        "static const uint8_t progress_frame[] = {",
    ]
    lines.extend("    " + ", ".join(f"0x{value:02X}" for value in transport[i:i + 16]) + ","
                 for i in range(0, len(transport), 16))
    lines.extend(["};", "static const size_t progress_frame_length = sizeof(progress_frame);", "#endif", ""])
    header = "\n".join(lines).encode("ascii")
    body = header.split(b"progress_frame[] = {", 1)[1].split(b"};", 1)[0]
    if bytes(int(value, 16) for value in re.findall(rb"0x([0-9A-F]{2})", body)) != transport:
        raise ValueError("FRAME_INVALID: generated header mismatch")
    return header


def adapt_frame(input_dir: Path, run_id: str, *, output_root: Path = OUTPUT_ROOT) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ValueError("OUTPUT_INVALID: invalid run-id")
    destination = output_root / run_id
    if destination.exists():
        raise FileExistsError(f"OUTPUT_CONFLICT: {destination}")
    logical, metadata, origin = read_logical_source(input_dir)
    transport = logical_to_transport(logical)
    header = make_transport_header(transport, sha256(logical), sha256(metadata))
    record = {
        "stage": "STEP016D_B2B_TRANSPORT_ONLY", "status": "SOFTWARE_CANDIDATE_NOT_PHYSICALLY_VERIFIED",
        "coordinate_frame": "T", "format": FORMAT,
        "mapping": "T[50*y+b] = L[50*(299-y)+b]",
        "source": {"b1_manifest_sha256": sha256(metadata), "b1_manifest_size": len(metadata),
                   "logical_raw_size": len(logical), "logical_raw_sha256": sha256(logical),
                   "png_provenance_from_b1": origin},
        "outputs": {name: {"size": len(data), "sha256": sha256(data)}
                    for name, data in ((RAW_NAME, transport), (HEADER_NAME, header))},
        "array": {"symbol": "progress_frame", "length": len(transport),
                  "byte_sequence_sha256": sha256(transport)},
        "tools": {"python": platform.python_version()},
        "not_run": ["physical display verification"],
    }
    encoded = (json.dumps(record, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in ((RAW_NAME, transport), (HEADER_NAME, header), ("transport-manifest.pending", encoded)):
        with (destination / name).open("xb") as stream:
            stream.write(data)
    (destination / "transport-manifest.pending").rename(destination / "transport-manifest.json")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        print(adapt_frame(args.input_dir, args.run_id))
    except (ValueError, OSError) as error:
        parser.exit(1, f"Transport adaptation rejected: {error}\n")


if __name__ == "__main__":
    main()
