"""Crop DATA-value localization — cropName() in i18n.js.

Crop names arrive from the backend as raw seed tokens ('maiz', 'jitomate',
'soybean'). UI copy is localized via the dict, but these DATA values rendered
directly leaked Spanish into EN mode (founder report 2026-06-10: "name of the
veggies" must be English in EN).

Covers:
  1. The crops map in i18n.js covers every crop token present in seed data.
  2. cropName() resolves es->en and en->es, normalizes accents, falls back
     to a capitalized original for unknown values (never blank).
  3. The farmer-journey render sites route crop values through cropLabel().
"""

import http.server
import re
import socketserver
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

FRONTEND = Path(__file__).parent.parent / "frontend"
I18N_JS = FRONTEND / "i18n.js"

# Union of crop tokens in seed data: fields.crop_type, crop_types.name,
# crop_types.companions, crop_varieties.crop_name. Normalized (lowercase,
# accent-free) the way cropName() looks them up.
SEED_CROP_TOKENS = {
    # fields.crop_type
    "agave", "maiz", "fresa", "arandano", "frambuesa", "frijol", "chile",
    "jitomate", "sorgo", "alfalfa", "corn", "soybean", "apple", "grape",
    "wheat", "tomato",
    # crop_types.name (beyond the above)
    "aguacate", "calabaza", "cana de azucar", "corn (field)", "garbanzo",
    "greenhouse tomato", "nopal", "winter wheat",
    # companions (beyond the above)
    "albahaca", "basil", "cacahuate", "cafe", "cebada", "cebolla", "clover",
    "comfrey", "fescue", "girasol", "macadamia", "marigold", "mustard",
    "nasturtium", "pepper", "platano", "soya", "tomate", "trigo", "zanahoria",
}


def _crops_map_keys(js_text: str) -> set:
    m = re.search(r"var crops = \{(.*?)\n    \};", js_text, re.DOTALL)
    assert m, "crops map not found in i18n.js"
    block = m.group(1)
    keys = re.findall(r"^\s*(?:'([^']+)'|([a-zA-Z][\w()]*?))\s*:\s*\{", block, re.MULTILINE)
    return {a or b for a, b in keys}


@pytest.fixture(scope="module")
def i18n_js_text():
    return I18N_JS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def frontend_server():
    frontend_path = str(FRONTEND)

    class SilentHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=frontend_path, **kwargs)

        def log_message(self, _fmt, *_args):
            pass

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("localhost", 0), SilentHandler) as httpd:
        port = httpd.server_address[1]
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        yield f"http://localhost:{port}"
        httpd.shutdown()


@pytest.fixture(scope="module")
def pw_browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


def _crop_name(pw_browser, base_url, lang, value):
    ctx = pw_browser.new_context()
    ctx.add_init_script(
        f"""
        window.localStorage.setItem('cultivOS_lang', '{lang}');
        window.localStorage.setItem('cultivOS_token', 'test-token-crop-i18n');
        window.localStorage.setItem('cultivOS_user', 'TestFarmer');
        """
    )
    pg = ctx.new_page()
    pg.goto(f"{base_url}/index.html", wait_until="domcontentloaded", timeout=12000)
    pg.wait_for_function("() => window.cultivOS_i18n && window.cultivOS_i18n.cropName", timeout=8000)
    result = pg.evaluate(f"window.cultivOS_i18n.cropName({value!r})")
    ctx.close()
    return result


class TestCropsMapCoverage:
    def test_every_seed_token_has_entry(self, i18n_js_text):
        keys = _crops_map_keys(i18n_js_text)
        missing = SEED_CROP_TOKENS - keys
        assert not missing, f"crops map missing seed tokens: {sorted(missing)}"

    def test_entries_have_both_languages(self, i18n_js_text):
        m = re.search(r"var crops = \{(.*?)\n    \};", i18n_js_text, re.DOTALL)
        entries = re.findall(r"\{[^{}]*\}", m.group(1))
        assert entries, "no crop entries parsed"
        for e in entries:
            assert "es:" in e and "en:" in e, f"entry missing a language: {e}"

    def test_cropname_exported(self, i18n_js_text):
        assert re.search(r"window\.cultivOS_i18n\s*=.*cropName:", i18n_js_text)


class TestCropNameResolution:
    def test_en_translates_spanish_token(self, pw_browser, frontend_server):
        assert _crop_name(pw_browser, frontend_server, "en", "maiz") == "Corn"

    def test_en_translates_jitomate(self, pw_browser, frontend_server):
        assert _crop_name(pw_browser, frontend_server, "en", "jitomate") == "Tomato"

    def test_es_translates_english_token(self, pw_browser, frontend_server):
        assert _crop_name(pw_browser, frontend_server, "es", "soybean") == "Soya"

    def test_es_keeps_spanish_token(self, pw_browser, frontend_server):
        assert _crop_name(pw_browser, frontend_server, "es", "maiz") == "Maiz"

    def test_accent_normalization(self, pw_browser, frontend_server):
        assert _crop_name(pw_browser, frontend_server, "en", "Maíz") == "Corn"

    def test_unknown_falls_back_capitalized(self, pw_browser, frontend_server):
        assert _crop_name(pw_browser, frontend_server, "en", "quinoa") == "Quinoa"

    def test_empty_returns_empty(self, pw_browser, frontend_server):
        assert _crop_name(pw_browser, frontend_server, "en", "") == ""


class TestRenderSitesUseCropLabel:
    """Regression guard: crop DATA values must not render raw."""

    def test_app_js(self):
        js = (FRONTEND / "app.js").read_text(encoding="utf-8")
        assert "function cropLabel" in js
        assert 'class="field-crop">${esc(cropLabel(f.crop_type))}' in js
        assert 'class="comparison-field-crop">${esc(cropLabel(f.crop_type))}' in js
        assert ".map(cropLabel).join(', ')" in js

    def test_field_js(self):
        js = (FRONTEND / "field.js").read_text(encoding="utf-8")
        assert "function cropLabel" in js
        assert "cropLabel(field.crop_type)" in js
        assert "cropLabel(cropType).toLowerCase()" in js
        assert "cropLabel(yieldData.crop_type)" in js
        assert "cropLabel(data.crop_type)" in js

    def test_knowledge_js(self):
        js = (FRONTEND / "knowledge.js").read_text(encoding="utf-8")
        assert "function cropLabel" in js
        assert "cropLabel(c.name)" in js
        assert "cropList(c.companions)" in js
        assert "cropList(f.suitable_crops)" in js
        assert "cropList(d.affected_crops)" in js
        assert "cropList(m.crops)" in js
