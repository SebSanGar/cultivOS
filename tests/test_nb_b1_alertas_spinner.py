"""NB-B1 — /notificaciones 'Cargando' spinner never clears.

Root cause: notifications.js::checkAuth IIFE does
    document.getElementById('nav-username').textContent = user
but auth-guard.js (runs first) replaces #nav-user-info innerHTML, removing
#nav-username from the DOM. When cultivOS_user is in localStorage the line
throws TypeError → loadNotifications() never called → spinner frozen forever.

Acceptance:
  - Open notifications.html with cultivOS_token + cultivOS_user in localStorage
  - After JS settles, the .loading spinner inside #notif-list must be gone
  - Page shows either notification list OR empty-state (not spinner)

TDD: these tests FAIL before the fix and PASS after.
"""

import http.server
import socketserver
import threading
import time
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

FRONTEND = Path(__file__).parent.parent / "frontend"
VIEWPORT = {"width": 390, "height": 844}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


def open_notif_page(pw_browser, base_url, inject_user=True):
    """Open notifications.html at 390x844 with token + optionally user injected."""
    ctx = pw_browser.new_context(viewport=VIEWPORT)
    init_script = "window.localStorage.setItem('cultivOS_token', 'test-token-nb-b1');"
    if inject_user:
        # This is the scenario that triggers the bug — user is set in localStorage
        init_script += "window.localStorage.setItem('cultivOS_user', 'TestFarmer');"
    ctx.add_init_script(init_script)
    pg = ctx.new_page()
    pg.goto(f"{base_url}/notifications.html", wait_until="domcontentloaded", timeout=12000)
    return ctx, pg


# ---------------------------------------------------------------------------
# T1 — Spinner clears when cultivOS_user is in localStorage (the bug scenario)
# ---------------------------------------------------------------------------


class TestNbB1SpinnerClears:
    """Spinner must not be present after JS settles — even with cultivOS_user set."""

    def test_spinner_gone_with_user_in_localstorage(self, pw_browser, frontend_server):
        """Bug scenario: cultivOS_token + cultivOS_user both in localStorage.

        Before fix: checkAuth IIFE throws TypeError on null.textContent → spinner stuck.
        After fix: loadNotifications() runs → network error → empty state replaces spinner.
        """
        ctx, pg = open_notif_page(pw_browser, frontend_server, inject_user=True)
        try:
            # Wait for JS to settle
            pg.wait_for_timeout(800)
            spinner_visible = pg.evaluate(
                """() => {
                    const spinner = document.querySelector('#notif-list .loading');
                    if (!spinner) return false;
                    const style = window.getComputedStyle(spinner);
                    return style.display !== 'none' && style.visibility !== 'hidden';
                }"""
            )
        finally:
            ctx.close()

        assert not spinner_visible, (
            "NB-B1: .loading spinner still visible in #notif-list after 800ms. "
            "Root cause: notifications.js checkAuth IIFE throws when cultivOS_user "
            "is set and nav-username has been removed by auth-guard.js."
        )

    def test_spinner_gone_without_user_in_localstorage(self, pw_browser, frontend_server):
        """Sanity check: spinner also clears without cultivOS_user (should already pass)."""
        ctx, pg = open_notif_page(pw_browser, frontend_server, inject_user=False)
        try:
            pg.wait_for_timeout(800)
            spinner_visible = pg.evaluate(
                """() => {
                    const spinner = document.querySelector('#notif-list .loading');
                    if (!spinner) return false;
                    const style = window.getComputedStyle(spinner);
                    return style.display !== 'none' && style.visibility !== 'hidden';
                }"""
            )
        finally:
            ctx.close()

        assert not spinner_visible, (
            "NB-B1: .loading spinner still visible even without cultivOS_user set."
        )

    def test_notif_list_has_content_after_load(self, pw_browser, frontend_server):
        """#notif-list must contain non-spinner content after JS runs.

        Static server has no /api/farms route → fetchJSON returns null → empty-state renders.
        The important thing: it renders SOMETHING instead of the frozen spinner.
        """
        ctx, pg = open_notif_page(pw_browser, frontend_server, inject_user=True)
        try:
            pg.wait_for_timeout(800)
            result = pg.evaluate(
                """() => {
                    const list = document.getElementById('notif-list');
                    if (!list) return {found: false, text: '', hasSpinner: false};
                    const spinner = list.querySelector('.loading');
                    return {
                        found: true,
                        text: list.textContent.trim(),
                        hasSpinner: spinner !== null
                    };
                }"""
            )
        finally:
            ctx.close()

        assert result["found"], "NB-B1: #notif-list not found in DOM"
        assert not result["hasSpinner"], (
            f"NB-B1: #notif-list still contains .loading spinner. "
            f"Text content: {result['text'][:100]!r}"
        )

    def test_no_uncaught_js_exception_in_console(self, pw_browser, frontend_server):
        """Page must not emit TypeError to console — that's the symptom of the bug."""
        ctx, pg = open_notif_page(pw_browser, frontend_server, inject_user=True)
        errors = []
        pg.on("pageerror", lambda err: errors.append(str(err)))
        try:
            pg.wait_for_timeout(800)
        finally:
            ctx.close()

        type_errors = [e for e in errors if "TypeError" in e or "Cannot set properties of null" in e]
        assert not type_errors, (
            f"NB-B1: Uncaught TypeError in page: {type_errors}"
        )
