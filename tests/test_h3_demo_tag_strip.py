"""H3 — Strip [DEMO] tag from farmer display (Playwright).

TDD tests written BEFORE implementation (all RED).
Acceptance criteria:
  1. Dashboard (/) renders farm cards with NO "[DEMO]" text visible
  2. /campo panel title has no "[DEMO]" substring
  3. /notificaciones farm-name labels have no "[DEMO]" substring

Approach: serve frontend static files, intercept /api/* via page.route()
to inject mock farm data containing "[DEMO]" names, then assert the
rendered page text has "[DEMO]" stripped.
"""

import http.server
import json
import re
import socketserver
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

FRONTEND = Path(__file__).parent.parent / "frontend"
VIEWPORT = {"width": 390, "height": 844}

# Mock farm data with [DEMO] names — same format as /api/farms response
MOCK_FARMS = {
    "data": [
        {
            "id": 1,
            "name": "Rancho Don Manuel [DEMO]",
            "municipality": "Tlajomulco",
            "state": "Jalisco",
            "total_hectares": 12.5,
            "owner_name": "Don Manuel",
        },
        {
            "id": 2,
            "name": "Aguacates La Joya [DEMO]",
            "municipality": "Zapotlanejo",
            "state": "Jalisco",
            "total_hectares": 8.0,
            "owner_name": "Rosa",
        },
    ],
    "meta": {"total": 2, "page": 1, "page_size": 20},
}

MOCK_FIELDS = [
    {
        "id": 1,
        "farm_id": 1,
        "name": "Parcela Norte",
        "crop_type": "aguacate",
        "hectares": 6.0,
    }
]

MOCK_HEALTH = {"score": 72, "label": "Bueno", "status": "good"}

MOCK_NOTIFICATIONS = [
    {
        "id": 1,
        "type": "alert",
        "message": "Prueba alerta",
        "severity": "low",
        "created_at": "2026-05-26T10:00:00",
        "acknowledged": False,
    }
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def frontend_server():
    """Serve frontend/ over HTTP."""
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
    """Single Chromium browser for the module."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


def _route_api(page):
    """Intercept all /api/* calls and return mock data."""

    def handler(route, request):
        url = request.url
        if re.search(r"/api/farms/\d+/fields/\d+/health", url):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(MOCK_HEALTH),
            )
        elif re.search(r"/api/farms/\d+/fields", url):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(MOCK_FIELDS),
            )
        elif re.search(r"/api/farms/\d+/notifications", url):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(MOCK_NOTIFICATIONS),
            )
        elif re.search(r"/api/farms/\d+/", url):
            # single-farm summary endpoint — return minimal dict
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "farm": MOCK_FARMS["data"][0],
                        "fields": MOCK_FIELDS,
                    }
                ),
            )
        elif "/api/farms" in url:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(MOCK_FARMS),
            )
        else:
            # Let unknown endpoints 404 silently
            route.fulfill(status=404, body="")

    page.route("**/api/**", handler)


def open_page(pw_browser, base_url: str, filename: str):
    ctx = pw_browser.new_context(viewport=VIEWPORT)
    ctx.add_init_script("""
        window.localStorage.setItem('cultivOS_token', 'test-token-h3');
        window.localStorage.setItem('cultivOS_user', 'TestUser');
    """)
    pg = ctx.new_page()
    _route_api(pg)
    pg.goto(f"{base_url}/{filename}", wait_until="domcontentloaded", timeout=12000)
    return ctx, pg


# ---------------------------------------------------------------------------
# T1 — Dashboard renders NO [DEMO] text in farm cards
# ---------------------------------------------------------------------------


class TestH3DashboardNoDemoTag:
    """Farm cards on dashboard must NOT show '[DEMO]' in any visible text."""

    def test_dashboard_farm_card_no_demo(self, pw_browser, frontend_server):
        ctx, pg = open_page(pw_browser, frontend_server, "index.html")
        try:
            # Wait for farm cards to render (farms load async)
            pg.wait_for_selector(".farm-card", timeout=5000)
            page_text = pg.evaluate("() => document.body.textContent")
        finally:
            ctx.close()
        assert "[DEMO]" not in page_text, (
            "Dashboard shows '[DEMO]' in page text — strip suffix in renderFarmCard"
        )

    def test_dashboard_farm_name_element_no_demo(self, pw_browser, frontend_server):
        ctx, pg = open_page(pw_browser, frontend_server, "index.html")
        try:
            pg.wait_for_selector(".farm-name", timeout=5000)
            farm_names = pg.evaluate(
                "() => Array.from(document.querySelectorAll('.farm-name')).map(el => el.textContent)"
            )
        finally:
            ctx.close()
        for name in farm_names:
            assert "[DEMO]" not in name, (
                f"Farm name '{name}' contains '[DEMO]' — must be stripped before display"
            )


# ---------------------------------------------------------------------------
# T2 — Field panel title on /campo has no [DEMO]
# ---------------------------------------------------------------------------


class TestH3CampoNoDemoTag:
    """/campo field panel title must strip [DEMO] from farm name."""

    def test_campo_panel_title_no_demo(self, pw_browser, frontend_server):
        ctx, pg = open_page(pw_browser, frontend_server, "field.html")
        try:
            # field.html loads with ?farm=1&field=1; simulate click flow or just
            # check that [DEMO] never appears in the visible body text after API mock
            pg.wait_for_timeout(500)
            page_text = pg.evaluate("() => document.body.textContent")
        finally:
            ctx.close()
        assert "[DEMO]" not in page_text, (
            "/campo page shows '[DEMO]' in page text — strip suffix in field name rendering"
        )


# ---------------------------------------------------------------------------
# T3 — /notificaciones farm-name labels have no [DEMO]
# ---------------------------------------------------------------------------


class TestH3NotificacionesNoDemoTag:
    """/notificaciones notif-farm-name elements must strip [DEMO] from farm name."""

    def test_notificaciones_farm_name_no_demo(self, pw_browser, frontend_server):
        ctx, pg = open_page(pw_browser, frontend_server, "notifications.html")
        try:
            pg.wait_for_timeout(800)  # allow async load
            page_text = pg.evaluate("() => document.body.textContent")
        finally:
            ctx.close()
        assert "[DEMO]" not in page_text, (
            "/notificaciones shows '[DEMO]' in page text — strip suffix in farm_name assignment"
        )
