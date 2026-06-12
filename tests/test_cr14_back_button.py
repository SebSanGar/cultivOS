"""CR14 — /campo back button falls back to '/' when no history.

The back button currently calls history.back() directly, which navigates to
about:blank when the page is opened directly (no referrer / no history entry).
Fix: fall back to '/' when history.length <= 1.
"""

from pathlib import Path

ROOT = Path(__file__).parent.parent
FIELD_HTML = ROOT / "frontend" / "field.html"


class TestBackButtonFallback:
    def test_back_button_does_not_call_bare_history_back(self):
        """onclick should NOT be the bare `history.back()` call."""
        src = FIELD_HTML.read_text()
        assert 'onclick="history.back()"' not in src, (
            "campo back button still calls history.back() with no fallback — "
            "navigates to about:blank when opened directly"
        )

    def test_back_button_has_root_fallback(self):
        """onclick or a called function must reference '/' as fallback."""
        src = FIELD_HTML.read_text()
        # Acceptable patterns:
        #   history.length > 1 ? history.back() : location.href='/'
        #   goBack() helper that does the same
        # Either way, the literal '/' must appear in the back-button handler
        # OR a goBack-style helper must be defined somewhere on the page.
        has_root_in_onclick = (
            "location.href = '/'" in src
            or "location.href='/'" in src
            or "location.replace('/')" in src
            or "location.assign('/')" in src
        )
        has_go_back_helper = (
            "function goBack" in src
            or "const goBack" in src
            or "let goBack" in src
        )
        assert has_root_in_onclick or has_go_back_helper, (
            "campo back button has no '/' fallback — must fall back to '/' "
            "when history.length <= 1"
        )

    def test_back_button_uses_history_length_check(self):
        """history.length must be checked so we don't blindly call history.back()."""
        src = FIELD_HTML.read_text()
        assert "history.length" in src, (
            "campo back button must check history.length before calling history.back()"
        )
