"""F7 — Mobile viewport sweep (Playwright, 375×812).

TDD tests written BEFORE implementation.
Acceptance criteria:
  - No horizontal overflow on all 5 farmer pages at 375px viewport
  - WhatsApp FAB (#whatsapp-fab) height >= 44px on all farmer pages
  - Primary campo CTA (#cta-que-hago) height >= 44px
  - Body computed font-size >= 16px on all farmer pages

Approach:
  - Simple HTTP server (http.server) serves frontend/ at a random port
  - /styles.css absolute path resolves correctly (unlike file://)
  - Playwright Chromium at 375x812; wait_until="domcontentloaded" (CDN ok to skip)
"""

import http.server
import socketserver
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

FRONTEND = Path(__file__).parent.parent / "frontend"
VIEWPORT = {"width": 375, "height": 812}

FARMER_PAGES = [
    ("index.html", "/"),
    ("field.html", "/campo"),
    ("notifications.html", "/notificaciones"),
    ("knowledge.html", "/conocimiento"),
    ("whatsapp-demo.html", "/whatsapp-demo"),
]

# F5 spec only requires FAB on these 4 pages (whatsapp-demo IS the WA page)
FARMER_PAGES_FAB = [
    ("index.html", "/"),
    ("field.html", "/campo"),
    ("notifications.html", "/notificaciones"),
    ("knowledge.html", "/conocimiento"),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def frontend_server():
    """Serve frontend/ over HTTP so /styles.css resolves correctly."""
    frontend_path = str(FRONTEND)

    class SilentHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=frontend_path, **kwargs)

        def log_message(self, _fmt, *_args):
            pass  # suppress request logs during tests

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("localhost", 0), SilentHandler) as httpd:
        port = httpd.server_address[1]
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        yield f"http://localhost:{port}"
        httpd.shutdown()


@pytest.fixture(scope="module")
def pw_browser():
    """Single Chromium browser for the entire module (headless)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


def open_page(pw_browser, base_url: str, filename: str):
    """Return (context, page) at 375×812. Caller must close context.

    Injects a fake cultivOS_token so auth-guard.js does not redirect to /login.
    """
    ctx = pw_browser.new_context(viewport=VIEWPORT)
    # Must run before any page script — prevents auth-guard.js redirect
    ctx.add_init_script("""
        window.localStorage.setItem('cultivOS_token', 'test-token-f7');
        window.localStorage.setItem('cultivOS_user', 'TestUser');
    """)
    pg = ctx.new_page()
    pg.goto(f"{base_url}/{filename}", wait_until="domcontentloaded", timeout=12000)
    return ctx, pg


# ---------------------------------------------------------------------------
# T1 — No horizontal overflow
# ---------------------------------------------------------------------------


class TestF7NoHorizontalOverflow:
    """document.documentElement.scrollWidth must not exceed viewport width."""

    @pytest.mark.parametrize("filename,route", FARMER_PAGES)
    def test_no_horizontal_overflow(self, pw_browser, frontend_server, filename, route):
        ctx, pg = open_page(pw_browser, frontend_server, filename)
        try:
            result = pg.evaluate(
                """() => {
                    const vw = window.innerWidth;
                    // Temporarily remove overflow:hidden to expose true scrollWidth
                    const bodyOvx = document.body.style.overflowX;
                    const htmlOvx = document.documentElement.style.overflowX;
                    document.body.style.overflowX = 'auto';
                    document.documentElement.style.overflowX = 'auto';
                    const sw = document.documentElement.scrollWidth;
                    document.body.style.overflowX = bodyOvx;
                    document.documentElement.style.overflowX = htmlOvx;
                    return {scrollWidth: sw, viewportWidth: vw, overflow: sw > vw + 1};
                }"""
            )
        finally:
            ctx.close()
        assert not result["overflow"], (
            f"{filename} ({route}): horizontal overflow at 375px — "
            f"scrollWidth={result['scrollWidth']} > viewportWidth={result['viewportWidth']}"
        )


# ---------------------------------------------------------------------------
# T2 — WhatsApp FAB tap target >= 44px
# ---------------------------------------------------------------------------


class TestF7WhatsAppFABTapTarget:
    """#whatsapp-fab rendered height must be >= 44px on the 4 farmer content pages.
    whatsapp-demo.html is excluded — the FAB loops back to itself there (F5 spec).
    """

    @pytest.mark.parametrize("filename,route", FARMER_PAGES_FAB)
    def test_whatsapp_fab_height_ge_44(
        self, pw_browser, frontend_server, filename, route
    ):
        ctx, pg = open_page(pw_browser, frontend_server, filename)
        try:
            height = pg.evaluate(
                """() => {
                    const el = document.getElementById('whatsapp-fab');
                    if (!el) return null;
                    return el.getBoundingClientRect().height;
                }"""
            )
        finally:
            ctx.close()
        assert height is not None, (
            f"{filename} ({route}): #whatsapp-fab not found in DOM"
        )
        assert height >= 44, (
            f"{filename} ({route}): #whatsapp-fab height {height}px < 44px"
        )


# ---------------------------------------------------------------------------
# T3 — Primary campo CTA tap target >= 44px
# ---------------------------------------------------------------------------


class TestF7CTAPrimary:
    """#cta-que-hago on campo must be >= 44px tall."""

    def test_cta_que_hago_height_ge_44(self, pw_browser, frontend_server):
        ctx, pg = open_page(pw_browser, frontend_server, "field.html")
        try:
            height = pg.evaluate(
                """() => {
                    const el = document.getElementById('cta-que-hago');
                    if (!el) return null;
                    return el.getBoundingClientRect().height;
                }"""
            )
        finally:
            ctx.close()
        assert height is not None, "field.html: #cta-que-hago not found in DOM"
        assert height >= 44, (
            f"field.html: #cta-que-hago height {height}px < 44px"
        )


# ---------------------------------------------------------------------------
# T4 — Body font-size >= 16px
# ---------------------------------------------------------------------------


class TestF7BodyFontSize:
    """Computed font-size on document.body must be >= 16px."""

    @pytest.mark.parametrize("filename,route", FARMER_PAGES)
    def test_body_font_size_ge_16px(
        self, pw_browser, frontend_server, filename, route
    ):
        ctx, pg = open_page(pw_browser, frontend_server, filename)
        try:
            font_size = pg.evaluate(
                """() => parseFloat(window.getComputedStyle(document.body).fontSize)"""
            )
        finally:
            ctx.close()
        assert font_size >= 16, (
            f"{filename} ({route}): body font-size {font_size}px < 16px"
        )
