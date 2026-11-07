import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

from services.firmware_offer import FirmwareOffer, MAX_FIRMWARE_BYTES

NOW = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)
BODY = b"\xE9" + b"x" * 32
SHA = hashlib.sha256(BODY).hexdigest()


class Clock:
    def __init__(self):
        self.value = NOW

    def __call__(self):
        return self.value


def json_text(path):
    """The path as it would appear inside a JSON body, without the surrounding quotes."""
    return json.dumps(str(path))[1:-1]


@pytest.fixture
def offer(tmp_path):
    image = tmp_path / "firmware.bin"
    image.write_bytes(BODY)
    config = tmp_path / "firmware.json"
    config.write_text(json.dumps({"path": str(image), "version": "round2-r6-2"}))
    clock = Clock()
    return FirmwareOffer(config, tmp_path, clock=clock), clock


def write_config(tmp_path, **values):
    config = tmp_path / "firmware.json"
    config.write_text(json.dumps(values))
    return config


def test_configured_status_has_no_path(offer, tmp_path):
    target, _ = offer
    assert target.configured is True
    assert target.status() == {
        "configured": True,
        "armed": False,
        "version": "round2-r6-2",
        "size": len(BODY),
        "sha256": SHA,
        "expires_at": None,
        "served_at": None,
        "device_version": None,
    }
    assert json_text(tmp_path) not in json.dumps(target.status())


def test_path_leak_assertion_is_not_vacuous(tmp_path):
    # Positive control: a body that did carry the path must be detectable.
    escaped = json_text(tmp_path)
    leaked = json.dumps({"path": str(tmp_path)})
    assert escaped in leaked
    # The raw Windows path can never match JSON text, which is why the encoded form
    # is the one asserted against.
    assert str(tmp_path) not in leaked


def test_manifest_is_exact_and_unarmed_by_default(offer):
    target, clock = offer
    assert target.manifest() == {"armed": False}
    assert target.arm() is True
    assert target.manifest() == {
        "armed": True,
        "version": "round2-r6-2",
        "size": len(BODY),
        "sha256": SHA,
    }
    assert target.status()["expires_at"] == (NOW + timedelta(seconds=600)).isoformat()


def test_image_is_one_shot(offer):
    target, _ = offer
    target.arm()
    image = target.take_image()
    assert image is not None
    assert image.version == "round2-r6-2"
    assert image.size == len(BODY)
    assert image.sha256 == SHA
    assert image.body == BODY
    assert target.take_image() is None
    assert target.status()["armed"] is False
    assert target.status()["served_at"] is not None


def test_arm_expires(offer):
    target, clock = offer
    target.arm()
    clock.value = NOW + timedelta(seconds=599)
    assert target.manifest()["armed"] is True
    clock.value = NOW + timedelta(seconds=600)
    assert target.manifest() == {"armed": False}
    assert target.take_image() is None


def test_device_target_version_auto_disarms(offer):
    target, _ = offer
    target.arm()
    target.observe_device_version("round2-r6-1")
    assert target.status()["armed"] is True
    assert target.status()["device_version"] == "round2-r6-1"
    target.observe_device_version("round2-r6-2")
    assert target.status()["armed"] is False
    assert target.status()["expires_at"] is None
    assert target.status()["device_version"] == "round2-r6-2"


@pytest.mark.parametrize(
    "version,body,size_limit",
    [
        ("bad version", BODY, MAX_FIRMWARE_BYTES),
        ("round2-r6-2", b"", MAX_FIRMWARE_BYTES),
        ("round2-r6-2", b"x" * (MAX_FIRMWARE_BYTES + 1), MAX_FIRMWARE_BYTES),
    ],
    # Short ids: the oversized body would otherwise overflow Windows' 32767-char
    # environment limit when pytest records PYTEST_CURRENT_TEST during teardown.
    ids=["bad-version", "empty-body", "oversized-body"],
)
def test_invalid_config_disables_ota_without_path(tmp_path, version, body, size_limit):
    image = tmp_path / "firmware.bin"
    image.write_bytes(body)
    config = write_config(tmp_path, path=str(image), version=version)
    target = FirmwareOffer(config, tmp_path)
    assert target.configured is False
    assert target.manifest() is None
    assert target.take_image() is None
    assert target.arm() is False
    assert json_text(tmp_path) not in json.dumps(target.status())


def test_missing_file_and_directory_are_rejected(tmp_path):
    missing = write_config(tmp_path, path=str(tmp_path / "missing.bin"), version="round2-r6-2")
    assert FirmwareOffer(missing, tmp_path).configured is False

    directory = write_config(tmp_path, path=str(tmp_path), version="round2-r6-2")
    assert FirmwareOffer(directory, tmp_path).configured is False


def test_unconfigured_status_is_explicit(tmp_path):
    target = FirmwareOffer(tmp_path / "missing.json", tmp_path)
    assert target.status() == {
        "configured": False,
        "armed": False,
        "version": None,
        "size": None,
        "sha256": None,
        "expires_at": None,
        "served_at": None,
        "device_version": None,
    }
