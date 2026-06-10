"""FL2 — Theme consistency tests.

Verify all pages share the same light brand theme. The intel-body class
must NOT set dark background colors. All pages should consume FL1
design tokens for a consistent light theme.
"""

import re
from pathlib import Path

import pytest

FRONTEND = Path(__file__).parent.parent / "frontend"
STYLES = FRONTEND / "styles.css"

DARK_BG_COLORS = {
    "#0f1117", "#1a1d27", "#2a2d3a",  # intel dark palette
    "#111", "#0d0d0d", "#111827",      # common dark patterns
}

DARK_BG_PATTERN = re.compile(
    r"--intel-bg:\s*(" + "|".join(re.escape(c) for c in DARK_BG_COLORS) + r")"
)


@pytest.fixture
def css_text():
    assert STYLES.exists(), "frontend/styles.css not found"
    return STYLES.read_text(encoding="utf-8")


# ── intel-body must NOT use dark background ──


def test_intel_body_bg_not_dark(css_text):
    """intel-body vars must use light FL1 tokens, not dark palette."""
    match = DARK_BG_PATTERN.search(css_text)
    assert match is None, (
        f"intel-body still uses dark bg: {match.group(0) if match else ''}. "
        "Should use FL1 light tokens (--bg or --neutral-50)."
    )


def test_intel_surface_not_dark(css_text):
    """intel surface color must be light (white/near-white), not dark."""
    m = re.search(r"--intel-surface:\s*(#[0-9a-fA-F]{3,8})", css_text)
    if m:
        color = m.group(1).lower()
        assert color not in {"#1a1d27", "#1e1e2e", "#111827", "#0f1117"}, (
            f"--intel-surface is still dark ({color}). Must be light."
        )


def test_intel_text_not_light_on_dark(css_text):
    """intel text must be dark-on-light, not light-on-dark (#e5e7eb)."""
    m = re.search(r"--intel-text:\s*(#[0-9a-fA-F]{3,8})", css_text)
    if m:
        color = m.group(1).lower()
        assert color not in {"#e5e7eb", "#f9fafb", "#f3f4f6", "#fff", "#ffffff"}, (
            f"--intel-text is light ({color}), indicating dark bg. Must be dark text."
        )


# ── Nav must not have dark override ──


def test_intel_nav_no_dark_bg(css_text):
    """intel-body nav must not override to dark background."""
    nav_section = re.search(
        r"\.intel-body\s+nav\s*\{([^}]+)\}", css_text
    )
    if nav_section:
        content = nav_section.group(1)
        assert "rgba(15,17,23" not in content, (
            "intel-body nav still has dark rgba(15,17,23) bg override"
        )


# ── No hardcoded dark text colors in intel titles ──


def test_intel_title_uses_token(css_text):
    """intel-title must use a CSS var (not hardcoded #f9fafb)."""
    title_block = re.search(r"\.intel-title\s*\{([^}]+)\}", css_text)
    assert title_block, "Missing .intel-title rule"
    content = title_block.group(1)
    if "color" in content:
        assert "#f9fafb" not in content, (
            "intel-title color is hardcoded #f9fafb (light-on-dark). Use var(--text)."
        )


def test_intel_stat_value_uses_token(css_text):
    """intel-stat-value must use token, not hardcoded #f9fafb."""
    block = re.search(r"\.intel-stat-value\s*\{([^}]+)\}", css_text)
    assert block, "Missing .intel-stat-value rule"
    content = block.group(1)
    if "color" in content:
        assert "#f9fafb" not in content, (
            "intel-stat-value color is hardcoded #f9fafb. Use var(--text)."
        )


# ── intel-logo must not force light-on-dark ──


def test_intel_logo_no_forced_light(css_text):
    """intel-logo must not force #e5e7eb (light text for dark bg)."""
    logo_match = re.search(r"\.intel-logo\s*\{([^}]+)\}", css_text)
    if logo_match:
        content = logo_match.group(1)
        assert "#e5e7eb" not in content, (
            "intel-logo forces #e5e7eb (light). Should inherit or use var(--text)."
        )


# ── Panel hover shadow not too dark ──


def test_intel_panel_hover_shadow_not_heavy(css_text):
    """Panel hover shadow should be light-appropriate, not heavy dark."""
    hover = re.search(r"\.intel-panel:hover\s*\{([^}]+)\}", css_text)
    if hover:
        content = hover.group(1)
        assert "rgba(0,0,0,0.2)" not in content.replace(" ", ""), (
            "Panel hover shadow rgba(0,0,0,0.2) too heavy for light bg. "
            "Use lighter shadow or FL1 --shadow-md."
        )


# ── Tab styling not dark-dependent ──


def test_intel_tab_hover_no_forced_light(css_text):
    """intel-tab:hover must not force light text (#e5e7eb)."""
    hover = re.search(r"\.intel-tab:hover\s*\{([^}]+)\}", css_text)
    if hover:
        content = hover.group(1)
        assert "#e5e7eb" not in content, (
            "intel-tab:hover forces #e5e7eb. Should use var(--text)."
        )


# ── Cross-page consistency: all HTML pages link styles.css ──


ALL_HTML = sorted(FRONTEND.glob("*.html"))


@pytest.mark.parametrize("page", ALL_HTML, ids=lambda p: p.name)
def test_page_links_stylesheet(page):
    """Every page must link /styles.css (FL1 tokens)."""
    text = page.read_text(encoding="utf-8")
    assert '/styles.css' in text or 'styles.css' in text, (
        f"{page.name} does not link styles.css — will miss FL1 tokens"
    )


# ── No inline dark background overrides ──


def _is_neutral_dark(hex_color: str) -> bool:
    """Check if a hex color is a neutral dark (not a saturated color like dark green)."""
    h = hex_color.lstrip("#").lower()
    if len(h) == 3:
        r, g, b = int(h[0], 16) * 17, int(h[1], 16) * 17, int(h[2], 16) * 17
    elif len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    else:
        return False
    if max(r, g, b) > 60:
        return False
    return True


INLINE_BG_HEX = re.compile(
    r"background(?:-color)?:\s*(#[0-9a-fA-F]{3,6})\b"
)

# login has own theme; whatsapp-demo/demo have intentional WhatsApp chat mockup
EXEMPT_PAGES = {"login.html", "whatsapp-demo.html", "demo.html"}


@pytest.mark.parametrize("page", ALL_HTML, ids=lambda p: p.name)
def test_no_inline_dark_bg(page):
    """Pages must not have inline <style> with neutral-dark background overrides."""
    if page.name in EXEMPT_PAGES:
        pytest.skip("Exempt page")
    text = page.read_text(encoding="utf-8")
    style_blocks = re.findall(r"<style[^>]*>(.*?)</style>", text, re.DOTALL)
    for block in style_blocks:
        for m in INLINE_BG_HEX.finditer(block):
            color = m.group(1)
            assert not _is_neutral_dark(color), (
                f"{page.name} has inline neutral-dark bg: {m.group(0)}"
            )
