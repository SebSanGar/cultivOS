"""FL1 — Design-token foundation tests.

Verify styles.css :root contains the full token set (fonts, spacing,
colors, radius, shadows, motion) and index.html loads Google Fonts.
"""

import re
from pathlib import Path

import pytest

FRONTEND = Path(__file__).parent.parent / "frontend"
STYLES = FRONTEND / "styles.css"
INDEX = FRONTEND / "index.html"


@pytest.fixture
def css_text():
    assert STYLES.exists(), "frontend/styles.css not found"
    return STYLES.read_text(encoding="utf-8")


@pytest.fixture
def index_text():
    assert INDEX.exists(), "frontend/index.html not found"
    return INDEX.read_text(encoding="utf-8")


def _extract_root_vars(css: str) -> set[str]:
    """Extract all CSS custom property names from :root blocks."""
    root_blocks = re.findall(r":root\s*\{([^}]+)\}", css)
    props = set()
    for block in root_blocks:
        props.update(re.findall(r"(--[\w-]+)\s*:", block))
    return props


# ── Typography tokens ──


FONT_VARS = {"--font-heading", "--font-body", "--font-mono"}


@pytest.mark.parametrize("var", sorted(FONT_VARS))
def test_font_token_exists(css_text, var):
    root_vars = _extract_root_vars(css_text)
    assert var in root_vars, f"Missing font token {var} in :root"


def test_google_fonts_space_grotesk(index_text):
    assert "Space+Grotesk" in index_text or "Space Grotesk" in index_text, \
        "index.html must load Space Grotesk from Google Fonts"


def test_google_fonts_inter(index_text):
    assert "Inter" in index_text, "index.html must load Inter from Google Fonts"


def test_body_uses_font_body_var(css_text):
    body_match = re.search(r"body\s*\{[^}]*font-family:\s*var\(--font-body\)", css_text)
    assert body_match, "body must use var(--font-body) for font-family"


# ── Spacing tokens (4px base, 8px rhythm) ──


SPACING_VARS = {
    "--space-1", "--space-2", "--space-3", "--space-4",
    "--space-6", "--space-8", "--space-12", "--space-16",
}


@pytest.mark.parametrize("var", sorted(SPACING_VARS))
def test_spacing_token_exists(css_text, var):
    root_vars = _extract_root_vars(css_text)
    assert var in root_vars, f"Missing spacing token {var} in :root"


# ── Color tokens — brand green ──


BRAND_COLOR_VARS = {
    "--brand-green", "--brand-green-light", "--brand-green-dark",
}


@pytest.mark.parametrize("var", sorted(BRAND_COLOR_VARS))
def test_brand_color_exists(css_text, var):
    root_vars = _extract_root_vars(css_text)
    assert var in root_vars, f"Missing brand color {var} in :root"


# ── Color tokens — semantic ──


SEMANTIC_VARS = {
    "--color-success", "--color-warning", "--color-danger", "--color-info",
    "--color-success-light", "--color-warning-light", "--color-danger-light", "--color-info-light",
}


@pytest.mark.parametrize("var", sorted(SEMANTIC_VARS))
def test_semantic_color_exists(css_text, var):
    root_vars = _extract_root_vars(css_text)
    assert var in root_vars, f"Missing semantic color {var} in :root"


# ── Color tokens — neutrals ──


NEUTRAL_VARS = {"--neutral-50", "--neutral-200", "--neutral-500", "--neutral-800"}


@pytest.mark.parametrize("var", sorted(NEUTRAL_VARS))
def test_neutral_color_exists(css_text, var):
    root_vars = _extract_root_vars(css_text)
    assert var in root_vars, f"Missing neutral {var} in :root"


# ── Border radius scale ──


RADIUS_VARS = {"--radius-sm", "--radius", "--radius-lg", "--radius-xl", "--radius-full"}


@pytest.mark.parametrize("var", sorted(RADIUS_VARS))
def test_radius_token_exists(css_text, var):
    root_vars = _extract_root_vars(css_text)
    assert var in root_vars, f"Missing radius token {var} in :root"


# ── Shadow scale ──


SHADOW_VARS = {"--shadow-sm", "--shadow", "--shadow-md", "--shadow-lg"}


@pytest.mark.parametrize("var", sorted(SHADOW_VARS))
def test_shadow_token_exists(css_text, var):
    root_vars = _extract_root_vars(css_text)
    assert var in root_vars, f"Missing shadow token {var} in :root"


# ── Motion tokens ──


MOTION_VARS = {
    "--ease-out", "--ease-in-out",
    "--duration-fast", "--duration-normal", "--duration-slow",
}


@pytest.mark.parametrize("var", sorted(MOTION_VARS))
def test_motion_token_exists(css_text, var):
    root_vars = _extract_root_vars(css_text)
    assert var in root_vars, f"Missing motion token {var} in :root"


# ── Backward compat — legacy vars still exist ──


LEGACY_VARS = {"--green", "--yellow", "--red", "--blue", "--bg", "--surface", "--text", "--border"}


@pytest.mark.parametrize("var", sorted(LEGACY_VARS))
def test_legacy_var_preserved(css_text, var):
    root_vars = _extract_root_vars(css_text)
    assert var in root_vars, f"Legacy var {var} must be preserved for backward compat"
