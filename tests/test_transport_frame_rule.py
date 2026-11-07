"""B2A mathematical contract only: no production adapter or frame-file output."""

import hashlib

import pytest


WIDTH, HEIGHT, STRIDE = 400, 300, 50
FRAME_BYTES = STRIDE * HEIGHT


def reverse_rows(frame):
    """Test-only reference for the future PC L-to-T boundary."""
    if len(frame) != FRAME_BYTES:
        raise ValueError("expected exactly 15000 bytes")
    return b"".join(frame[y * STRIDE:(y + 1) * STRIDE]
                    for y in range(HEIGHT - 1, -1, -1))


def pixels(frame):
    # Independent sequential MSB-first decoder; 0 black, 1 white.
    return [int(bit) for byte in frame for bit in format(byte, "08b")]


def pixel_oracle(frame):
    source = pixels(frame)
    target = [0] * (WIDTH * HEIGHT)
    for y_l in range(HEIGHT):
        for x_l in range(WIDTH):
            x_t, y_t = x_l, 299 - y_l
            target[y_t * WIDTH + x_t] = source[y_l * WIDTH + x_l]
    return bytes(int("".join(map(str, target[i:i + 8])), 2)
                 for i in range(0, len(target), 8))


def synthetic_frame():
    # Seed-free fixture. Exact formula is part of the golden-hash contract.
    return bytes((17 * y + 29 * b + (y * b) % 251) % 256
                 for y in range(HEIGHT) for b in range(STRIDE))


@pytest.mark.parametrize("length", [0, 14999, 15001])
def test_wrong_length_rejected(length):
    with pytest.raises(ValueError, match="15000"):
        reverse_rows(bytes(length))


def test_all_pixels_and_byte_mapping():
    logical = synthetic_frame()
    transport = reverse_rows(logical)
    assert len(transport) == FRAME_BYTES
    assert transport == pixel_oracle(logical)
    for y in range(HEIGHT):
        for b in range(STRIDE):
            assert transport[STRIDE * y + b] == logical[STRIDE * (299 - y) + b]


@pytest.mark.parametrize("x", [0, 7, 8, 399])
@pytest.mark.parametrize("y", [0, 1, 298, 299])
def test_pixel_coordinate_and_bit_boundary(x, y):
    logical = bytearray(b"\xff" * FRAME_BYTES)
    logical[y * STRIDE + x // 8] &= ~(0x80 >> (x % 8))
    transport = reverse_rows(logical)
    black = [i for i, value in enumerate(pixels(transport)) if value == 0]
    assert black == [(299 - y) * WIDTH + x]


def test_distinct_corner_markers():
    logical = bytearray(b"\xff" * FRAME_BYTES)
    # Distinct row-end markers prove left/right and within-byte order are retained.
    logical[0], logical[49], logical[-50], logical[-1] = 0x7F, 0xFC, 0x1F, 0xF0
    transport = reverse_rows(logical)
    assert (transport[0], transport[49], transport[-50], transport[-1]) == (
        0x1F, 0xF0, 0x7F, 0xFC)


@pytest.mark.parametrize("value", [0x00, 0xFF, 0x81])
def test_symmetric_frames_preserve_polarity_and_may_share_hash(value):
    logical = bytes([value]) * FRAME_BYTES
    transport = reverse_rows(logical)
    assert transport == logical
    assert hashlib.sha256(transport).digest() == hashlib.sha256(logical).digest()


def test_inverse_and_fixed_h1_composition():
    logical = synthetic_frame()
    transport = reverse_rows(logical)
    assert reverse_rows(transport) == logical
    # Independent pixel model of the fixed H1 Y mapping, not execution of H1.
    assert pixel_oracle(transport) == logical


def test_golden_hashes():
    logical = synthetic_frame()
    transport = reverse_rows(logical)
    assert hashlib.sha256(logical).hexdigest() == "6ef4696f9124b264ec2742728f3398ecf1d584a3855719746974f6d8af1b339a"
    assert hashlib.sha256(transport).hexdigest() == "a0ade0ea621dc91f1a1a6f362d35b430981e8540b902fb83527f53cc8dcbe6b3"
    assert logical != transport
