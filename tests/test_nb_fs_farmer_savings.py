"""NB-FS — farmer dollar-savings view (/impacto-agricultor).

English-first, currency-neutral, honest (no $0 headline, estimate badge with the number).
Main-thread-authored in parallel with the agency.
"""

from pathlib import Path

FRONTEND = Path(__file__).parent.parent / "frontend"
HTML = (FRONTEND / "impacto-agricultor.html").read_text(encoding="utf-8")
JS = (FRONTEND / "impacto-agricultor.js").read_text(encoding="utf-8")
CSS = (FRONTEND / "styles.css").read_text(encoding="utf-8")


class TestServed:
    def test_route_200_html(self, client):
        resp = client.get("/impacto-agricultor")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")


class TestEnglishFirst:
    def test_lang_is_english(self):
        assert '<html lang="en">' in HTML

    def test_hero_copy_english(self):
        assert "You've saved about" in HTML
        assert "Your Savings" in HTML

    def test_no_spanish_leftovers_from_old_page(self):
        # the old dark Spanish page is fully replaced
        for s in ["Impacto del Agricultor", "Ahorro Estimado", "Dias en Plataforma", "intel-body"]:
            assert s not in HTML, f"old Spanish/dark artifact still present: {s}"


class TestCurrencyNeutral:
    def test_no_currency_code_in_user_copy(self):
        for s in ["MXN", "pesos", "Pesos", "CAD", "es-MX"]:
            assert s not in HTML, f"non-neutral currency token in HTML: {s}"
        # JS formats money locale-neutral (en-US grouping, bare $)
        assert "en-US" in JS and "MXN" not in JS

    def test_money_helper_is_bare_dollar(self):
        assert 'return "$" +' in JS


class TestHonesty:
    def test_no_zero_dollar_headline(self):
        # empty/insufficient data must show a forward-looking line, not $0
        assert "savings <= 0 || treatments <= 0" in JS
        assert "Here you'll see how much you save" in JS

    def test_estimate_badge_present(self):
        assert "impact-badge" in HTML
        assert "Estimate" in HTML

    def test_methodology_link(self):
        assert "/metodologia" in HTML


class TestStructure:
    def test_hero_and_components(self):
        for el in ["impact-hero", "hero-amount", "impact-support"]:
            assert el in HTML, f"missing hero/component hook in HTML: {el}"
        # field cards are rendered by JS
        for el in ["before-after", "semaforo-dot"]:
            assert el in JS, f"missing field-card hook in JS: {el}"

    def test_css_block_present(self):
        for cls in [".impact-hero", ".impact-hero-amount", ".semaforo-dot.green", ".before-after"]:
            assert cls in CSS, f"missing impact CSS: {cls}"

    def test_no_hardcoded_hex_in_js(self):
        # colors come from tokens via CSS classes, not inline hex (design rule T3.7)
        for hexcode in ["#22c55e", "#ef4444", "#a3a3a3"]:
            assert hexcode not in JS, f"hardcoded hex in JS: {hexcode}"
