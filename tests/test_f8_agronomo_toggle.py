"""F8 — Agronomist toggle (Playwright).

TDD tests written BEFORE implementation.
Acceptance criteria:
  1. #agronomo-toggle button present on all 4 farmer pages (/, /campo, /notificaciones, /conocimiento)
  2. #agronomo-toggle absent from analytical pages (/intel, /vuelos, /estado)
  3. Default (farmer) mode: .agronomo-only elements hidden, .nav-agronomo-extras hidden
  4. Agronomist mode (localStorage='agronomist'): .agronomo-only visible, nav-agronomo-extras visible
  5. Toggle click flips mode and persists to localStorage
  6. Page reload with agronomist localStorage: elements remain visible
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
]

ANALYTICAL_PAGES = [
    ("intel.html", "/intel"),
    ("flights.html", "/vuelos"),
    ("status.html", "/estado"),
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


def open_page_farmer(pw_browser, base_url: str, filename: str, view_mode: str = "farmer"):
    """Return (context, page) at 375x812 in farmer mode (default).

    Injects cultivOS_token to bypass auth-guard.js.
    view_mode: 'farmer' (default) or 'agronomist'
    """
    ctx = pw_browser.new_context(viewport=VIEWPORT)
    ctx.add_init_script(f"""
        window.localStorage.setItem('cultivOS_token', 'test-token-f8');
        window.localStorage.setItem('cultivOS_user', 'TestUser');
        window.localStorage.setItem('cultivos_view_mode', '{view_mode}');
    """)
    pg = ctx.new_page()
    pg.goto(f"{base_url}/{filename}", wait_until="domcontentloaded", timeout=12000)
    return ctx, pg


# ---------------------------------------------------------------------------
# T1 — Toggle button present on farmer pages
# ---------------------------------------------------------------------------


class TestF8ToggleButtonPresent:
    """#agronomo-toggle must exist in DOM on all 4 farmer pages."""

    @pytest.mark.parametrize("filename,route", FARMER_PAGES)
    def test_toggle_button_present(self, pw_browser, frontend_server, filename, route):
        ctx, pg = open_page_farmer(pw_browser, frontend_server, filename)
        try:
            exists = pg.evaluate(
                "() => !!document.getElementById('agronomo-toggle')"
            )
        finally:
            ctx.close()
        assert exists, (
            f"{filename} ({route}): #agronomo-toggle button not found in DOM"
        )


# ---------------------------------------------------------------------------
# T2 — Toggle absent from analytical pages
# ---------------------------------------------------------------------------


class TestF8ToggleAbsentAnalytical:
    """#agronomo-toggle must NOT be present on analytical pages."""

    @pytest.mark.parametrize("filename,route", ANALYTICAL_PAGES)
    def test_toggle_absent_on_analytical(self, pw_browser, frontend_server, filename, route):
        ctx, pg = open_page_farmer(pw_browser, frontend_server, filename)
        try:
            exists = pg.evaluate(
                "() => !!document.getElementById('agronomo-toggle')"
            )
        finally:
            ctx.close()
        assert not exists, (
            f"{filename} ({route}): #agronomo-toggle should NOT appear on analytical pages"
        )


# ---------------------------------------------------------------------------
# T3 — Default farmer mode: agronomo content hidden
# ---------------------------------------------------------------------------


class TestF8DefaultFarmerMode:
    """In farmer mode (default), .agronomo-only and nav-agronomo-extras must be hidden."""

    def test_field_agronomo_only_hidden_by_default(self, pw_browser, frontend_server):
        """field.html: #agronomo-bloque-principal must be hidden in farmer mode."""
        ctx, pg = open_page_farmer(pw_browser, frontend_server, "field.html", "farmer")
        try:
            hidden = pg.evaluate(
                """() => {
                    const el = document.getElementById('agronomo-bloque-principal');
                    if (!el) return null;
                    return el.hidden || el.getAttribute('hidden') !== null ||
                           window.getComputedStyle(el).display === 'none';
                }"""
            )
        finally:
            ctx.close()
        assert hidden is not None, "field.html: #agronomo-bloque-principal not found"
        assert hidden, "field.html: #agronomo-bloque-principal should be hidden in farmer mode"

    @pytest.mark.parametrize("filename,route", [
        ("index.html", "/"),
        ("notifications.html", "/notificaciones"),
        ("knowledge.html", "/conocimiento"),
    ])
    def test_nav_agronomo_extras_hidden_by_default(self, pw_browser, frontend_server, filename, route):
        """.nav-agronomo-extras must be hidden in farmer mode."""
        ctx, pg = open_page_farmer(pw_browser, frontend_server, filename, "farmer")
        try:
            hidden = pg.evaluate(
                """() => {
                    const el = document.querySelector('.nav-agronomo-extras');
                    if (!el) return null;
                    return el.hidden || el.getAttribute('hidden') !== null ||
                           window.getComputedStyle(el).display === 'none';
                }"""
            )
        finally:
            ctx.close()
        assert hidden is not None, f"{filename}: .nav-agronomo-extras not found"
        assert hidden, f"{filename} ({route}): .nav-agronomo-extras should be hidden in farmer mode"


# ---------------------------------------------------------------------------
# T4 — Agronomist mode: agronomo content visible
# ---------------------------------------------------------------------------


class TestF8AgronomistMode:
    """In agronomist mode (localStorage='agronomist'), hidden elements must become visible."""

    def test_field_agronomo_only_visible_in_agronomo_mode(self, pw_browser, frontend_server):
        """field.html: #agronomo-bloque-principal must be visible in agronomist mode."""
        ctx, pg = open_page_farmer(pw_browser, frontend_server, "field.html", "agronomist")
        try:
            visible = pg.evaluate(
                """() => {
                    const el = document.getElementById('agronomo-bloque-principal');
                    if (!el) return null;
                    const hidden = el.hidden || el.getAttribute('hidden') !== null ||
                                   window.getComputedStyle(el).display === 'none';
                    return !hidden;
                }"""
            )
        finally:
            ctx.close()
        assert visible is not None, "field.html: #agronomo-bloque-principal not found"
        assert visible, "field.html: #agronomo-bloque-principal should be VISIBLE in agronomist mode"

    @pytest.mark.parametrize("filename,route", [
        ("index.html", "/"),
        ("notifications.html", "/notificaciones"),
        ("knowledge.html", "/conocimiento"),
    ])
    def test_nav_agronomo_extras_visible_in_agronomo_mode(self, pw_browser, frontend_server, filename, route):
        """.nav-agronomo-extras must be visible when agronomist mode is active."""
        ctx, pg = open_page_farmer(pw_browser, frontend_server, filename, "agronomist")
        try:
            visible = pg.evaluate(
                """() => {
                    const el = document.querySelector('.nav-agronomo-extras');
                    if (!el) return null;
                    const hidden = el.hidden || el.getAttribute('hidden') !== null ||
                                   window.getComputedStyle(el).display === 'none';
                    return !hidden;
                }"""
            )
        finally:
            ctx.close()
        assert visible is not None, f"{filename}: .nav-agronomo-extras not found"
        assert visible, f"{filename} ({route}): .nav-agronomo-extras should be VISIBLE in agronomist mode"


# ---------------------------------------------------------------------------
# T5 — Toggle click flips mode and saves to localStorage
# ---------------------------------------------------------------------------


class TestF8ToggleClickBehavior:
    """Clicking #agronomo-toggle must flip mode and persist to localStorage."""

    def test_click_from_farmer_to_agronomist(self, pw_browser, frontend_server):
        """Clicking toggle in farmer mode saves 'agronomist' to localStorage."""
        ctx, pg = open_page_farmer(pw_browser, frontend_server, "index.html", "farmer")
        try:
            pg.click("#agronomo-toggle")
            mode = pg.evaluate(
                "() => window.localStorage.getItem('cultivos_view_mode')"
            )
        finally:
            ctx.close()
        assert mode == "agronomist", (
            f"After click from farmer mode, expected localStorage='agronomist', got '{mode}'"
        )

    def test_click_from_agronomist_to_farmer(self, pw_browser, frontend_server):
        """Clicking toggle in agronomist mode saves 'farmer' to localStorage."""
        ctx, pg = open_page_farmer(pw_browser, frontend_server, "index.html", "agronomist")
        try:
            pg.click("#agronomo-toggle")
            mode = pg.evaluate(
                "() => window.localStorage.getItem('cultivos_view_mode')"
            )
        finally:
            ctx.close()
        assert mode == "farmer", (
            f"After click from agronomist mode, expected localStorage='farmer', got '{mode}'"
        )


# ---------------------------------------------------------------------------
# T6 — Persistence across page reload
# ---------------------------------------------------------------------------


class TestF8Persistence:
    """Agronomist mode set via click must persist across page reload."""

    def test_agronomo_mode_persists_reload(self, pw_browser, frontend_server):
        """Set mode to agronomist, reload page, nav-agronomo-extras still visible."""
        ctx, pg = open_page_farmer(pw_browser, frontend_server, "index.html", "farmer")
        try:
            # Click to switch to agronomo mode
            pg.click("#agronomo-toggle")
            # Reload same page
            pg.reload(wait_until="domcontentloaded", timeout=12000)
            visible = pg.evaluate(
                """() => {
                    const el = document.querySelector('.nav-agronomo-extras');
                    if (!el) return null;
                    const hidden = el.hidden || el.getAttribute('hidden') !== null ||
                                   window.getComputedStyle(el).display === 'none';
                    return !hidden;
                }"""
            )
        finally:
            ctx.close()
        assert visible is not None, "index.html: .nav-agronomo-extras not found after reload"
        assert visible, (
            "index.html: .nav-agronomo-extras should remain VISIBLE after reload when agronomist mode set"
        )

    def test_farmer_mode_persists_reload(self, pw_browser, frontend_server):
        """Default farmer mode persists across reload (nav-agronomo-extras stays hidden)."""
        ctx, pg = open_page_farmer(pw_browser, frontend_server, "index.html", "farmer")
        try:
            pg.reload(wait_until="domcontentloaded", timeout=12000)
            hidden = pg.evaluate(
                """() => {
                    const el = document.querySelector('.nav-agronomo-extras');
                    if (!el) return null;
                    return el.hidden || el.getAttribute('hidden') !== null ||
                           window.getComputedStyle(el).display === 'none';
                }"""
            )
        finally:
            ctx.close()
        assert hidden is not None, "index.html: .nav-agronomo-extras not found after reload"
        assert hidden, (
            "index.html: .nav-agronomo-extras should remain HIDDEN after reload in farmer mode"
        )
