"""I5/I6 — accessibility + semantic-heading gates for the impact pages.

I6c: each impact page exposes exactly one top-level <h1> (screen-reader landmark).
I6a: no emoji glyphs in the UI (project rule: no emoji except market flags);
     decorative icons are inline SVG instead.
"""


def test_impacto_agricultor_has_single_h1(client):
    html = client.get("/impacto-agricultor").text
    assert html.count("<h1") == 1, "farmer impact page needs exactly one <h1> landmark"


def test_impacto_agricultor_no_emoji_icon(client):
    html = client.get("/impacto-agricultor").text
    assert "\U0001F33F" not in html, "seedling emoji 🌱 present — use inline SVG"
    assert "&#127807;" not in html, "seedling emoji entity present — use inline SVG"


def test_impacto_agricultor_empty_state_has_svg_icon(client):
    html = client.get("/impacto-agricultor").text
    # the empty-state decorative icon must be an inline SVG, not an emoji glyph
    assert "impact-empty-state__icon" in html
    assert "<svg" in html


# ── I5d: owner page (economic-impact) screen-reader names ──

import re


def _tag(html, tag, id_):
    m = re.search(r"<%s[^>]*id=\"%s\"[^>]*>" % (tag, re.escape(id_)), html)
    return m.group(0) if m else ""


def test_economic_impact_farm_select_has_accessible_name(client):
    html = client.get("/impacto-economico").text
    sel = _tag(html, "select", "econ-farm-select")
    assert sel, "econ-farm-select not found"
    assert "aria-label" in sel or 'for="econ-farm-select"' in html, \
        "farm select needs an accessible name (aria-label or <label for>)"


def test_economic_impact_charts_have_aria_label(client):
    html = client.get("/impacto-economico").text
    canvases = re.findall(r"<canvas[^>]*>", html)
    assert len(canvases) >= 2, "expected 2 chart canvases"
    for c in canvases:
        assert 'role="img"' in c and "aria-label" in c, \
            "each chart <canvas> needs role=img + aria-label: %s" % c


# ── I5c/I6b: WCAG AA contrast on status pills (parsed from styles.css) ──

import os

_CSS = os.path.join(os.path.dirname(__file__), "..", "frontend", "styles.css")


def _rel_lum(hx):
    h = hx.lstrip("#")
    chans = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [(c / 12.92) if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in chans]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast(fg, bg):
    a, b = sorted((_rel_lum(fg), _rel_lum(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def _root_tokens(css):
    return dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})", css))


def _resolve(value, tokens):
    """Resolve a CSS color value (hex, or var(--t, #fallback)) to a hex string."""
    m = re.search(r"var\((--[\w-]+)\s*(?:,\s*(#[0-9a-fA-F]{6}))?\)", value)
    if m:
        return tokens.get(m.group(1)) or m.group(2)
    m = re.search(r"#[0-9a-fA-F]{6}", value)
    return m.group(0) if m else None


def _rule_colors(css, selector):
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    assert m, "rule %s not found in styles.css" % selector
    body = m.group(1)
    tokens = _root_tokens(css)
    fg = re.search(r"(?<!-)color\s*:\s*([^;]+)", body)
    bg = re.search(r"background\s*:\s*([^;]+)", body)
    return _resolve(fg.group(1), tokens), _resolve(bg.group(1), tokens)


def test_delta_pills_meet_wcag_aa():
    """Gain/loss pills are small bold text → WCAG AA needs >= 4.5:1."""
    with open(_CSS, encoding="utf-8") as f:
        css = f.read()
    for selector in (".delta-pill.up", ".delta-pill.down", ".delta-pill.flat"):
        fg, bg = _rule_colors(css, selector)
        assert fg and bg, "%s missing color/background" % selector
        ratio = _contrast(fg, bg)
        assert ratio >= 4.5, "%s contrast %.2f < 4.5 (%s on %s)" % (selector, ratio, fg, bg)
