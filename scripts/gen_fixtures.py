#!/usr/bin/env python3
"""
F3 — Generate 4 NDVI/thermal/RGB fixture images via Gemini/Imagen API.

Outputs 4 PNGs (1024×1024) to frontend/images/fixtures/:
  1. healthy-orchard-ndvi.png
  2. stressed-orchard-ndvi.png
  3. orchard-thermal.png
  4. orchard-rgb-aerial.png

Usage:
    cd /Users/SebSan/Documents/cultivOS
    python3 scripts/gen_fixtures.py
"""
import io
import os
import sys
import base64
from pathlib import Path
from dotenv import dotenv_values

# ── Config ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "frontend" / "images" / "fixtures"
ENV_FILE = REPO_ROOT / ".autoagent" / ".env"

# Load API key from .autoagent/.env
env = dotenv_values(ENV_FILE)
API_KEY = env.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    sys.exit("ERROR: GEMINI_API_KEY not found in .autoagent/.env or environment")

TARGET_SIZE = (1024, 1024)

# ── Prompts ───────────────────────────────────────────────────────────────────
FIXTURES = [
    {
        "filename": "healthy-orchard-ndvi.png",
        "prompt": (
            "A top-down satellite NDVI false-color image of a healthy avocado orchard in Jalisco Mexico. "
            "Vivid bright green and lime green colors throughout, showing healthy vegetation. "
            "Rows of avocado trees clearly visible from above, uniform green canopy coverage. "
            "No stress zones, no red or yellow patches. Blue sky edges. 1024x1024 pixels."
        ),
    },
    {
        "filename": "stressed-orchard-ndvi.png",
        "prompt": (
            "A top-down satellite NDVI false-color image of an avocado orchard in Jalisco Mexico "
            "showing water stress in the northeast corner. "
            "Most of the orchard is healthy bright green, but the northeast corner (~15 percent of field) "
            "shows a stress patch in orange and red colors indicating low NDVI. "
            "Clear contrast between healthy green and stressed red/orange zones. 1024x1024 pixels."
        ),
    },
    {
        "filename": "orchard-thermal.png",
        "prompt": (
            "A top-down satellite thermal infrared image of an avocado orchard. "
            "Most of the field is cool blue and purple tones indicating normal temperature. "
            "The northeast corner has a hot red and orange zone indicating thermal stress or irrigation deficit. "
            "False-color thermal palette: blue=cool, red=hot. "
            "The hot zone matches approximately 15 percent of the northeast corner. 1024x1024 pixels."
        ),
    },
    {
        "filename": "orchard-rgb-aerial.png",
        "prompt": (
            "A photorealistic aerial drone photograph of a small avocado farm in Jalisco Mexico, "
            "approximately 5 hectares. Rows of avocado trees with green canopies visible from above. "
            "Mountain backdrop in the distance. A dirt road running alongside the farm. "
            "No people visible. Bright natural daylight. "
            "Rural Mexican landscape, some dry grass between tree rows. 1024x1024 pixels."
        ),
    },
]


# ── Image generation ──────────────────────────────────────────────────────────

def resize_to_target(image_bytes: bytes, target: tuple = TARGET_SIZE) -> bytes:
    """Resize image to target size using PIL, compress to fit ≤2MB, return PNG bytes."""
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))
    if img.size != target:
        print(f"  Resizing from {img.size} to {target}")
        img = img.resize(target, Image.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Try max PNG compression first
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9)
    raw = buf.getvalue()

    # If still > 2MB, quantize colors to reduce file size
    MAX_BYTES = 2 * 1024 * 1024
    if len(raw) > MAX_BYTES:
        print(f"  PNG too large ({len(raw) // 1024} KB), quantizing colors...")
        # Convert to P mode (256 colors) then back — dramatic size reduction
        quantized = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        buf2 = io.BytesIO()
        quantized.save(buf2, format="PNG", optimize=True)
        raw2 = buf2.getvalue()
        if len(raw2) < len(raw):
            raw = raw2
            # Reload to verify it's still valid
            check = Image.open(io.BytesIO(raw))
            print(f"  Quantized: {len(raw) // 1024} KB, mode={check.mode}")

    return raw


def generate_via_imagen4(client, prompt: str) -> bytes:
    """Generate image using Imagen 4 Fast."""
    from google.genai import types

    result = client.models.generate_images(
        model="imagen-4.0-fast-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",
            output_mime_type="image/png",
        ),
    )
    return result.generated_images[0].image.image_bytes


def generate_via_gemini_image(client, prompt: str) -> bytes:
    """Fallback: generate image using gemini-2.5-flash-image."""
    from google.genai import types

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data is not None:
            data = part.inline_data.data
            if isinstance(data, str):
                return base64.b64decode(data)
            return data
    raise RuntimeError("No image part in Gemini response")


def generate_image(client, prompt: str) -> bytes:
    """Try Imagen 4 Fast, fall back to gemini-2.5-flash-image."""
    try:
        print("  Using Imagen 4 Fast...")
        raw = generate_via_imagen4(client, prompt)
    except Exception as e:
        print(f"  Imagen 4 failed ({e!r}), falling back to gemini-2.5-flash-image...")
        raw = generate_via_gemini_image(client, prompt)
    return resize_to_target(raw)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    from google import genai

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    client = genai.Client(api_key=API_KEY)

    print(f"Generating {len(FIXTURES)} fixture images → {FIXTURES_DIR}\n")

    for fixture in FIXTURES:
        out_path = FIXTURES_DIR / fixture["filename"]
        print(f"[{fixture['filename']}]")

        if out_path.exists():
            print(f"  Already exists ({out_path.stat().st_size // 1024} KB), skipping.")
            continue

        png_bytes = generate_image(client, fixture["prompt"])
        out_path.write_bytes(png_bytes)
        size_kb = len(png_bytes) // 1024
        print(f"  Saved {size_kb} KB → {out_path.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
