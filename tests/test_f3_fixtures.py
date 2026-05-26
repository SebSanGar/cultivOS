"""
F3 — Fixture image tests
PNG files must exist, be between 100KB and 2MB, and be valid PNG images.
Dimensions must be 1024x1024.
These tests are RED until scripts/gen_fixtures.py is run.
"""
import os
import struct
import zlib
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "images", "fixtures")

EXPECTED_FIXTURES = [
    "healthy-orchard-ndvi.png",
    "stressed-orchard-ndvi.png",
    "orchard-thermal.png",
    "orchard-rgb-aerial.png",
]

MIN_SIZE_BYTES = 100 * 1024   # 100 KB
MAX_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB


def _read_png_dimensions(path):
    """Read width/height from PNG IHDR chunk — no Pillow needed."""
    with open(path, "rb") as f:
        sig = f.read(8)
        assert sig == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"
        # IHDR chunk: 4-byte length, 4-byte type, 13-byte data
        f.read(4)  # length
        chunk_type = f.read(4)
        assert chunk_type == b"IHDR", f"First chunk is {chunk_type}, expected IHDR"
        width = struct.unpack(">I", f.read(4))[0]
        height = struct.unpack(">I", f.read(4))[0]
    return width, height


@pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
def test_fixture_exists(filename):
    """Each fixture PNG must exist in frontend/images/fixtures/."""
    path = os.path.join(FIXTURES_DIR, filename)
    assert os.path.isfile(path), (
        f"Missing fixture: {filename}. Run scripts/gen_fixtures.py to generate it."
    )


@pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
def test_fixture_size(filename):
    """Each fixture must be between 100 KB and 2 MB."""
    path = os.path.join(FIXTURES_DIR, filename)
    if not os.path.isfile(path):
        pytest.skip(f"{filename} not generated yet")
    size = os.path.getsize(path)
    assert size >= MIN_SIZE_BYTES, (
        f"{filename} too small: {size} bytes (min {MIN_SIZE_BYTES})"
    )
    assert size <= MAX_SIZE_BYTES, (
        f"{filename} too large: {size} bytes (max {MAX_SIZE_BYTES})"
    )


@pytest.mark.parametrize("filename", EXPECTED_FIXTURES)
def test_fixture_dimensions(filename):
    """Each fixture must be exactly 1024×1024 pixels."""
    path = os.path.join(FIXTURES_DIR, filename)
    if not os.path.isfile(path):
        pytest.skip(f"{filename} not generated yet")
    w, h = _read_png_dimensions(path)
    assert w == 1024, f"{filename} width={w}, expected 1024"
    assert h == 1024, f"{filename} height={h}, expected 1024"
