"""H2 — Mobile nav hamburger at 390px (Playwright, 390x844).

TDD tests written BEFORE implementation (all RED).
Acceptance criteria at 390x844 viewport:
  1. #nav-hamburger button is visible in DOM on all 4 farmer pages
  2. .nav-farmer-tabs is NOT visible by default (hidden at 390px)
  3. Clicking #nav-hamburger reveals .nav-farmer-tabs
  4. No horizontal overflow (scrollWidth <= innerWidth) on all 4 farmer pages

Pages tested: /, /campo (field.html), /notificaciones, /conocimiento
"""

import http.server
import socketserver
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

FRONTEND = Path(__file__).parent.parent / "frontend"
VIEWPORT = {"width": 390, "height": 844}

# 4 farmer pages that have the nav hamburger
FARMER_NAV_PAGES = [
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
    """Serve frontend/ over HTTP so /styles.css and /toggle.js resolve correctly."""
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
    """Return (context, page) at 390x844. Injects fake auth token."""
    ctx = pw_browser.new_context(viewport=VIEWPORT)
    ctx.add_init_script("""
        window.localStorage.setItem('cultivOS_token', 'test-token-h2');
        window.localStorage.setItem('cultivOS_user', 'TestUser');
    """)
    pg = ctx.new_page()
    pg.goto(f"{base_url}/{filename}", wait_until="domcontentloaded", timeout=12000)
    return ctx, pg


# ---------------------------------------------------------------------------
# T1 — #nav-hamburger button present in DOM
# ---------------------------------------------------------------------------


class TestH2HamburgerPresent:
    """#nav-hamburger must exist in the DOM on all 4 farmer pages."""

    @pytest.mark.parametrize("filename,route", FARMER_NAV_PAGES)
    def test_hamburger_button_present(self, pw_browser, frontend_server, filename, route):
        ctx, pg = open_page(pw_browser, frontend_server, filename)
        try:
            exists = pg.evaluate(
                "() => !!document.getElementById('nav-hamburger')"
            )
        finally:
            ctx.close()
        assert exists, (
            f"{filename} ({route}): #nav-hamburger button not found in DOM — "
            "hamburger button must be added to the nav at 390px"
        )


# ---------------------------------------------------------------------------
# T2 — .nav-farmer-tabs hidden by default at 390px
# ---------------------------------------------------------------------------


class TestH2TabsHiddenByDefault:
    """.nav-farmer-tabs must not be visible at 390px before hamburger is clicked."""

    @pytest.mark.parametrize("filename,route", FARMER_NAV_PAGES)
    def test_farmer_tabs_hidden_at_390(self, pw_browser, frontend_server, filename, route):
        ctx, pg = open_page(pw_browser, frontend_server, filename)
        try:
            visible = pg.evaluate(
                """() => {
                    const tabs = document.querySelector('.nav-farmer-tabs');
                    if (!tabs) return false;
                    const style = window.getComputedStyle(tabs);
                    // Visible means display != none AND visibility != hidden AND opacity != 0
                    return (
                        style.display !== 'none' &&
                        style.visibility !== 'hidden' &&
                        parseFloat(style.opacity) !== 0
                    );
                }"""
            )
        finally:
            ctx.close()
        assert not visible, (
            f"{filename} ({route}): .nav-farmer-tabs is visible at 390px by default — "
            "must be hidden until hamburger is clicked"
        )


# ---------------------------------------------------------------------------
# T3 — clicking hamburger reveals .nav-farmer-tabs
# ---------------------------------------------------------------------------


class TestH2HamburgerRevealsNav:
    """Clicking #nav-hamburger must make .nav-farmer-tabs visible."""

    @pytest.mark.parametrize("filename,route", FARMER_NAV_PAGES)
    def test_hamburger_click_reveals_tabs(self, pw_browser, frontend_server, filename, route):
        ctx, pg = open_page(pw_browser, frontend_server, filename)
        try:
            pg.click("#nav-hamburger")
            pg.wait_for_timeout(200)  # let CSS transition settle
            visible = pg.evaluate(
                """() => {
                    const tabs = document.querySelector('.nav-farmer-tabs');
                    if (!tabs) return false;
                    const style = window.getComputedStyle(tabs);
                    return (
                        style.display !== 'none' &&
                        style.visibility !== 'hidden' &&
                        parseFloat(style.opacity) !== 0
                    );
                }"""
            )
        finally:
            ctx.close()
        assert visible, (
            f"{filename} ({route}): clicking #nav-hamburger did not reveal .nav-farmer-tabs"
        )


# ---------------------------------------------------------------------------
# T4 — no horizontal overflow at 390px
# ---------------------------------------------------------------------------


class TestH2NoOverflow:
    """scrollWidth must not exceed innerWidth at 390px viewport."""

    @pytest.mark.parametrize("filename,route", FARMER_NAV_PAGES)
    def test_no_horizontal_overflow(self, pw_browser, frontend_server, filename, route):
        ctx, pg = open_page(pw_browser, frontend_server, filename)
        try:
            result = pg.evaluate(
                """() => {
                    const vw = window.innerWidth;
                    const bodyOvx = document.body.style.overflowX;
                    const htmlOvx = document.documentElement.style.overflowX;
                    document.body.style.overflowX = 'auto';
                    document.documentElement.style.overflowX = 'auto';
                    // Also reveal hamburger to test open state
                    const sw = document.documentElement.scrollWidth;
                    document.body.style.overflowX = bodyOvx;
                    document.documentElement.style.overflowX = htmlOvx;
                    return {scrollWidth: sw, viewportWidth: vw, overflow: sw > vw + 1};
                }"""
            )
        finally:
            ctx.close()
        assert not result["overflow"], (
            f"{filename} ({route}): horizontal overflow at 390px — "
            f"scrollWidth={result['scrollWidth']} > viewportWidth={result['viewportWidth']}"
        )
