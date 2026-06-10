"""NB-B2 — EN toggle doesn't translate page text.

Problem: i18n.js switchLang→applyAll works mechanically, but:
  (a) notifications.html / field.html / knowledge.html have 0 data-i18n attrs
  (b) Those pages don't include i18n.js at all
  (c) No lang-toggle button on those pages

Fix verified by:
  1. dict.en has a value for every key in dict.es (parity)
  2. Key farmer pages include i18n.js script tag
  3. Key farmer pages carry data-i18n attrs on their nav + heading
  4. Lang toggle button (.nav-lang-toggle) present on each page
  5. Playwright: toggle EN on index.html → nav.farms becomes 'My Plots'
  6. Playwright: toggle EN on notifications.html → title becomes 'Notification History'

TDD: these tests FAIL before the fix and PASS after.
"""

import http.server
import re
import socketserver
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

FRONTEND = Path(__file__).parent.parent / "frontend"
VIEWPORT = {"width": 1280, "height": 800}

I18N_JS = FRONTEND / "i18n.js"

FARMER_PAGES = [
    "notifications.html",
    "field.html",
    "knowledge.html",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read_html(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def _extract_dict_keys(js_text: str, lang: str) -> set:
    """Extract keys from the cultivOS i18n.js dict block for a given language.

    Handles both quoted and unquoted JS object keys (e.g. `es: {` or `'es': {`).
    Looks for the block `<lang>: { ... }` and extracts `'key.name': 'value'` entries.
    """
    # Match either unquoted `es: {` or quoted `'es': {`
    pattern = re.compile(
        rf"(?:'{re.escape(lang)}'|{re.escape(lang)})\s*:\s*\{{(.*?)\}}\s*[,;]?\s*(?:en|es)\s*:",
        re.DOTALL,
    )
    m = pattern.search(js_text)
    if not m:
        # Fallback: match to end of file for last block
        pattern2 = re.compile(
            rf"(?:'{re.escape(lang)}'|{re.escape(lang)})\s*:\s*\{{(.*?)\}}\s*\}};",
            re.DOTALL,
        )
        m = pattern2.search(js_text)
    if not m:
        return set()
    block = m.group(1)
    # Extract key names: 'key.name': 'value'
    keys = re.findall(r"'([a-z][a-zA-Z0-9.]+)'\s*:", block)
    return set(keys)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


def open_page(pw_browser, base_url, filename):
    ctx = pw_browser.new_context(viewport=VIEWPORT)
    ctx.add_init_script("""
        window.localStorage.setItem('cultivOS_token', 'test-token-nb-b2');
        window.localStorage.setItem('cultivOS_user', 'TestFarmer');
        window.localStorage.removeItem('cultivOS_lang');
    """)
    pg = ctx.new_page()
    pg.goto(f"{base_url}/{filename}", wait_until="domcontentloaded", timeout=12000)
    return ctx, pg


# ---------------------------------------------------------------------------
# T1 — dict EN/ES parity
# ---------------------------------------------------------------------------


class TestI18nDictParity:
    """Every key in dict.es must exist in dict.en with a non-empty value."""

    def test_en_has_all_es_keys(self, i18n_js_text):
        es_keys = _extract_dict_keys(i18n_js_text, "es")
        en_keys = _extract_dict_keys(i18n_js_text, "en")

        assert len(es_keys) > 0, "Could not parse dict.es keys from i18n.js"
        assert len(en_keys) > 0, "Could not parse dict.en keys from i18n.js"

        missing = es_keys - en_keys
        assert not missing, (
            f"NB-B2: dict.en is missing keys that dict.es has: {sorted(missing)}"
        )

    def test_key_notif_historyTitle_exists_in_en(self, i18n_js_text):
        """New key needed for notifications page heading."""
        assert "'notif.historyTitle'" in i18n_js_text, (
            "NB-B2: key 'notif.historyTitle' not defined in i18n.js"
        )
        # EN value should be English, not Spanish
        assert "Notification History" in i18n_js_text, (
            "NB-B2: EN value for notif.historyTitle should be 'Notification History'"
        )

    def test_key_knowledge_title_exists_in_en(self, i18n_js_text):
        assert "'knowledge.title'" in i18n_js_text, (
            "NB-B2: key 'knowledge.title' not defined in i18n.js"
        )
        assert "Knowledge Base" in i18n_js_text, (
            "NB-B2: EN value for knowledge.title should be 'Knowledge Base'"
        )

    def test_key_field_cta_exists_in_en(self, i18n_js_text):
        assert "'field.cta'" in i18n_js_text, (
            "NB-B2: key 'field.cta' not defined in i18n.js"
        )


# ---------------------------------------------------------------------------
# T2 — farmer pages include i18n.js
# ---------------------------------------------------------------------------


class TestFarmerPagesIncludeI18n:
    """notifications.html, field.html, knowledge.html must include i18n.js."""

    @pytest.mark.parametrize("filename", FARMER_PAGES)
    def test_page_includes_i18n_js(self, filename):
        html = read_html(filename)
        assert 'src="/i18n.js"' in html or "src='/i18n.js'" in html, (
            f"NB-B2: {filename} does not include <script src=\"/i18n.js\">"
        )


# ---------------------------------------------------------------------------
# T3 — lang toggle present on farmer pages
# ---------------------------------------------------------------------------


class TestLangTogglePresent:
    """Each farmer page must have a .nav-lang-toggle button."""

    @pytest.mark.parametrize("filename", FARMER_PAGES + ["login.html"])
    def test_lang_toggle_present(self, filename):
        html = read_html(filename)
        assert "nav-lang-toggle" in html, (
            f"NB-B2: {filename} does not contain .nav-lang-toggle element"
        )


# ---------------------------------------------------------------------------
# T4 — key elements have data-i18n attributes
# ---------------------------------------------------------------------------


class TestDataI18nCoverage:
    """Key strings on farmer pages must carry data-i18n for switchLang to work."""

    def test_notifications_nav_has_data_i18n(self):
        html = read_html("notifications.html")
        assert 'data-i18n="nav.alerts"' in html or "data-i18n='nav.alerts'" in html, (
            "NB-B2: notifications.html nav 'Alertas' link missing data-i18n"
        )

    def test_notifications_heading_has_data_i18n(self):
        html = read_html("notifications.html")
        assert 'data-i18n="notif.historyTitle"' in html, (
            "NB-B2: notifications.html h1 missing data-i18n='notif.historyTitle'"
        )

    def test_field_nav_has_data_i18n(self):
        html = read_html("field.html")
        assert 'data-i18n="nav.farms"' in html, (
            "NB-B2: field.html nav 'Mis Parcelas' link missing data-i18n"
        )

    def test_field_cta_has_data_i18n(self):
        html = read_html("field.html")
        assert 'data-i18n="field.cta"' in html, (
            "NB-B2: field.html CTA button missing data-i18n='field.cta'"
        )

    def test_knowledge_heading_has_data_i18n(self):
        html = read_html("knowledge.html")
        assert 'data-i18n="knowledge.title"' in html, (
            "NB-B2: knowledge.html h1 missing data-i18n='knowledge.title'"
        )

    def test_agronomo_toggle_has_data_i18n_on_all_pages(self):
        for fname in FARMER_PAGES:
            html = read_html(fname)
            assert 'data-i18n="toggle.agronomo"' in html, (
                f"NB-B2: {fname} agronomo toggle button missing data-i18n"
            )


# ---------------------------------------------------------------------------
# T5 — Playwright: toggle EN on index.html
# ---------------------------------------------------------------------------


class TestPlaywrightLangToggleIndex:
    """Clicking EN on index.html changes visible nav text."""

    def test_en_toggle_changes_nav_farms_to_english(self, pw_browser, frontend_server):
        ctx, pg = open_page(pw_browser, frontend_server, "index.html")
        try:
            # Initially Spanish (default)
            nav_text_es = pg.evaluate(
                """() => {
                    const el = document.querySelector('[data-i18n="nav.farms"]');
                    return el ? el.textContent.trim() : null;
                }"""
            )
            # Click EN
            pg.evaluate(
                """() => {
                    if (window.cultivOS_i18n) window.cultivOS_i18n.switchLang('en');
                }"""
            )
            pg.wait_for_timeout(200)
            nav_text_en = pg.evaluate(
                """() => {
                    const el = document.querySelector('[data-i18n="nav.farms"]');
                    return el ? el.textContent.trim() : null;
                }"""
            )
        finally:
            ctx.close()

        assert nav_text_es is not None, "NB-B2: nav.farms element not found on index.html"
        assert nav_text_en == "My Crops", (
            f"NB-B2: nav.farms did not switch to English. Got: {nav_text_en!r}"
        )

    def test_lang_toggle_button_is_in_dom(self, pw_browser, frontend_server):
        ctx, pg = open_page(pw_browser, frontend_server, "index.html")
        try:
            has_toggle = pg.evaluate(
                """() => !!document.querySelector('.nav-lang-toggle')"""
            )
        finally:
            ctx.close()
        assert has_toggle, "NB-B2: .nav-lang-toggle not found on index.html"


# ---------------------------------------------------------------------------
# T6 — Playwright: toggle EN on notifications.html
# ---------------------------------------------------------------------------


class TestPlaywrightLangToggleNotifications:
    """Clicking EN on notifications.html changes heading text."""

    def test_en_toggle_changes_notifications_title(self, pw_browser, frontend_server):
        ctx, pg = open_page(pw_browser, frontend_server, "notifications.html")
        try:
            pg.wait_for_timeout(300)
            # Switch to EN via i18n API
            pg.evaluate(
                """() => {
                    if (window.cultivOS_i18n) window.cultivOS_i18n.switchLang('en');
                }"""
            )
            pg.wait_for_timeout(200)
            heading_text = pg.evaluate(
                """() => {
                    const el = document.querySelector('[data-i18n="notif.historyTitle"]');
                    return el ? el.textContent.trim() : null;
                }"""
            )
        finally:
            ctx.close()

        assert heading_text is not None, (
            "NB-B2: [data-i18n='notif.historyTitle'] not found in notifications.html DOM"
        )
        assert heading_text == "Notification History", (
            f"NB-B2: heading did not switch to English. Got: {heading_text!r}"
        )
