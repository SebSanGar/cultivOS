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
