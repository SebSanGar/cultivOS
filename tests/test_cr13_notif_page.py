"""CR13 — /notificaciones: unresolved notif.pageTitle key, dead agronomo toggle, Spanish notification bodies.

Three sub-problems:
(a) <title data-i18n="notif.pageTitle"> resolves to literal key — missing from dict
(b) Agronomist toggle has no visible DOM change — no .agronomo-only content on page
(c) Notification body text is Spanish (seed templates) — anglicize seed
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
I18N_JS = ROOT / "frontend" / "i18n.js"
NOTIF_HTML = ROOT / "frontend" / "notifications.html"
SEED_PY = ROOT / "scripts" / "seed_demo.py"


# ── (a) notif.pageTitle key in i18n dict ─────────────────────────────────────

class TestNotifPageTitleKey:
    def test_pageTitle_key_in_es_dict(self):
        """notif.pageTitle must exist in the ES (Spanish) dict section."""
        src = I18N_JS.read_text()
        # ES dict is the first dict block. The key must appear before the EN dict.
        # Simple check: the key appears at least once in the file.
        assert '"notif.pageTitle"' in src or "'notif.pageTitle'" in src, (
            "notif.pageTitle key missing from i18n.js — title shows literal key"
        )

    def test_pageTitle_key_in_en_dict(self):
        """notif.pageTitle must appear in both ES and EN dict sections."""
        src = I18N_JS.read_text()
        # Count occurrences — must appear in both ES and EN blocks (at least 2)
        count = src.count('"notif.pageTitle"') + src.count("'notif.pageTitle'")
        assert count >= 2, (
            f"notif.pageTitle appears {count} time(s) — needs entry in both ES and EN dicts"
        )

    def test_pageTitle_en_value_contains_notification(self):
        """EN notif.pageTitle value should contain 'Notification'."""
        src = I18N_JS.read_text()
        # Find the EN dict block (second occurrence of the key)
        # Check that after the second occurrence, the value contains 'Notification'
        occurrences = []
        pos = 0
        while True:
            idx = src.find("notif.pageTitle", pos)
            if idx == -1:
                break
            occurrences.append(idx)
            pos = idx + 1

        assert len(occurrences) >= 2, "notif.pageTitle must appear in both dicts"

        # Extract value near the second occurrence
        snippet = src[occurrences[1]:occurrences[1] + 120]
        assert "Notification" in snippet or "notification" in snippet, (
            f"EN notif.pageTitle value should contain 'Notification', got: {snippet!r}"
        )

    def test_pageTitle_es_value_contains_notificaciones(self):
        """ES notif.pageTitle value should contain 'Notificaciones' or 'Historial'."""
        src = I18N_JS.read_text()
        occurrences = []
        pos = 0
        while True:
            idx = src.find("notif.pageTitle", pos)
            if idx == -1:
                break
            occurrences.append(idx)
            pos = idx + 1

        assert len(occurrences) >= 2, "notif.pageTitle must appear in both dicts"

        # First occurrence should be in ES dict
        snippet = src[occurrences[0]:occurrences[0] + 120]
        assert (
            "Notificaciones" in snippet or "Historial" in snippet or "cultivOS" in snippet
        ), f"ES notif.pageTitle value looks wrong: {snippet!r}"


# ── (b) Agronomist toggle has visible DOM change ──────────────────────────────

class TestAgronomistToggleVisible:
    def test_notifications_html_has_agronomo_only_section(self):
        """notifications.html must have at least one .agronomo-only element."""
        src = NOTIF_HTML.read_text()
        assert "agronomo-only" in src, (
            "notifications.html has no .agronomo-only elements — "
            "toggle click produces zero visible DOM change beyond button label"
        )

    def test_agronomo_only_section_has_hidden_attr(self):
        """The .agronomo-only element should start hidden (hidden attribute)."""
        src = NOTIF_HTML.read_text()
        assert re.search(r'class="[^"]*agronomo-only[^"]*"[^>]*hidden', src) or \
               re.search(r'hidden[^>]*class="[^"]*agronomo-only', src), (
            ".agronomo-only element must have hidden attribute so it's hidden in farmer mode"
        )

    def test_agronomo_only_section_has_visible_label(self):
        """The .agronomo-only section must contain visible text content."""
        src = NOTIF_HTML.read_text()
        # Find the agronomo-only section and check it has non-empty text
        match = re.search(
            r'class="[^"]*agronomo-only[^"]*"[^>]*>(.*?)</(?:div|section)',
            src, re.DOTALL
        )
        assert match, ".agronomo-only element not found or malformed"
        inner = match.group(1).strip()
        # Should have more than just whitespace/empty
        assert len(inner) > 10, (
            f"agronomo-only section appears empty: {inner!r}"
        )


# ── (c) Seed notification messages are English ───────────────────────────────

class TestSeedAlertsEnglish:
    """seed_demo.py alert templates must be in English (not Spanish)."""

    SPANISH_MARKERS = [
        "Salud del campo por debajo del umbral",
        "Deficit hidrico detectado",
        "Patron de NDVI irregular sugiere posible plaga",
        "Condiciones optimas para aplicar composta",
        "Pronostico de helada para manana",
        "Ventana optima para sembrar cultivo de cobertura",
    ]

    ENGLISH_MARKERS = [
        "Field health below threshold",
        "Water deficit detected",
        "Irregular NDVI pattern",
        "Optimal conditions to apply compost",
    ]

    def test_seed_alerts_no_spanish_messages(self):
        """Alert template messages in seed_demo.py must not be Spanish."""
        src = SEED_PY.read_text()
        for marker in self.SPANISH_MARKERS:
            assert marker not in src, (
                f"Spanish alert message still in seed_demo.py: {marker!r}"
            )

    def test_seed_alerts_have_english_messages(self):
        """Alert template messages in seed_demo.py must contain English strings."""
        src = SEED_PY.read_text()
        found = sum(1 for m in self.ENGLISH_MARKERS if m in src)
        assert found >= 3, (
            f"Only {found}/{len(self.ENGLISH_MARKERS)} English alert markers found in seed_demo.py"
        )

    def test_ontario_seed_alerts_english(self):
        """Ontario-specific alert templates must be English."""
        src = SEED_PY.read_text()
        # Ontario region has frost warning — check English version
        assert "Frost forecast" in src or "frost forecast" in src, (
            "Ontario frost warning message must be in English"
        )

    def test_jalisco_seed_alerts_english(self):
        """Jalisco-specific alert templates must be English."""
        src = SEED_PY.read_text()
        # Jalisco has irrigation message — check English version
        assert "Water deficit" in src or "thermal sensor" in src, (
            "Jalisco irrigation alert must be in English"
        )

    def test_cover_crop_seed_alert_english(self):
        """Cover crop recommendation must be in English."""
        src = SEED_PY.read_text()
        assert "cover crop" in src.lower() or "Optimal window" in src, (
            "Cover crop recommendation must be in English"
        )
