"""FL6 — Sweep + verify consistency tests.

Verify all CSS custom property names used across HTML pages are defined
in styles.css :root. No orphan dark fallbacks, no inline dark backgrounds
on non-exempt pages. Every page links styles.css + uses FL1 font stack.
"""

import re
from pathlib import Path

import pytest

FRONTEND = Path(__file__).parent.parent / "frontend"
STYLES = FRONTEND / "styles.css"

ALL_HTML = sorted(FRONTEND.glob("*.html"))

WHATSAPP_EXEMPT = {"demo.html", "whatsapp-demo.html"}

KNOWN_DARK_BG = re.compile(
    r"background\s*:\s*#(?:"
    r"1a1a2e|1e293b|0f172a|1e1e1e|0d0d1a|1a2332|121212"
    r"|0a0a0a|2d2d2d|111a"
    r")\b",
    re.IGNORECASE,
)

VAR_NAME_RE = re.compile(r"var\(\s*(--[a-z][a-z0-9-]*)")


@pytest.fixture(scope="module")
def css_text():
    return STYLES.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def root_vars(css_text):
    """Extract all CSS custom property names defined in :root."""
    root_match = re.search(r":root\s*\{([^}]+)\}", css_text, re.DOTALL)
    assert root_match, ":root block must exist in styles.css"
    root_block = root_match.group(1)
    return set(re.findall(r"(--[a-z][a-z0-9-]+)\s*:", root_block))


# ── CSS var coverage: all var names used in HTML must be defined in :root ──

CRITICAL_VARS = [
    "--card-bg",
    "--text-secondary",
    "--muted",
    "--card",
    "--text-primary",
    "--accent-green",
    "--card-surface",
    "--input-bg",
]


@pytest.mark.parametrize("var_name", CRITICAL_VARS)
def test_critical_var_defined_in_root(var_name, root_vars):
    assert var_name in root_vars, (
        f"{var_name} is used in HTML pages but not defined in styles.css :root. "
        f"Dark fallback values will render instead of FL1 tokens."
    )


def test_no_orphan_var_names(root_vars):
    """Every var() name used in any HTML page should be defined in :root."""
    missing = set()
    for html_file in ALL_HTML:
        text = html_file.read_text(encoding="utf-8")
        used = set(VAR_NAME_RE.findall(text))
        for v in used:
            if v not in root_vars:
                missing.add(v)
    assert not missing, (
        f"CSS vars used in HTML but NOT defined in :root: {sorted(missing)}"
    )


# ── No inline dark backgrounds on non-exempt pages ──


@pytest.fixture(params=[p for p in ALL_HTML if p.name not in WHATSAPP_EXEMPT])
def page_path(request):
    return request.param


def test_no_inline_dark_bg(page_path):
    """Non-exempt pages must not have inline style dark backgrounds."""
    text = page_path.read_text(encoding="utf-8")
    inline_styles = re.findall(r'style="([^"]*)"', text)
    for style in inline_styles:
        match = KNOWN_DARK_BG.search(style)
        assert not match, (
            f"{page_path.name} has inline dark background: {match.group()}"
        )


# ── disease.html inputs must use FL1 tokens ──


def test_disease_inputs_not_dark():
    """disease.html input fields should use var tokens not hardcoded dark bg."""
    disease = FRONTEND / "disease.html"
    if not disease.exists():
        pytest.skip("disease.html not found")
    text = disease.read_text(encoding="utf-8")
    inputs = re.findall(r'<input[^>]*style="([^"]*)"[^>]*>', text)
    for style in inputs:
        assert "#1a1a2e" not in style, (
            "disease.html inputs still use hardcoded dark #1a1a2e background"
        )
        assert "color:#eee" not in style, (
            "disease.html inputs still use hardcoded light #eee text color"
        )


# ── Every page links styles.css ──


@pytest.mark.parametrize("html_file", ALL_HTML, ids=lambda p: p.name)
def test_page_links_stylesheet(html_file):
    text = html_file.read_text(encoding="utf-8")
    assert re.search(
        r'<link[^>]*href=["\']/?styles\.css["\']', text
    ), f"{html_file.name} does not link to styles.css"


# ── Font stack: body uses FL1 font via var or styles.css ──


def test_body_uses_fl1_font(css_text):
    assert "var(--font-body)" in css_text, (
        "body must use var(--font-body) from FL1 tokens"
    )


# ── No scoped <style> blocks with hardcoded dark body bg ──


@pytest.mark.parametrize(
    "html_file",
    [p for p in ALL_HTML if p.name not in WHATSAPP_EXEMPT],
    ids=lambda p: p.name,
)
def test_no_scoped_dark_body_bg(html_file):
    text = html_file.read_text(encoding="utf-8")
    style_blocks = re.findall(r"<style[^>]*>(.*?)</style>", text, re.DOTALL)
    for block in style_blocks:
        body_rules = re.findall(
            r"body\s*\{[^}]*\}", block, re.DOTALL
        )
        for rule in body_rules:
            assert not re.search(
                r"background\s*:\s*#[012][0-9a-f]{5}", rule
            ), f"{html_file.name} has scoped body dark background"
