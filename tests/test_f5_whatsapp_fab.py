"""F5 — Tests for floating WhatsApp button on farmer pages.

TDD tests written BEFORE implementation.
Acceptance criteria:
  - FAB present on farmer pages: /, /campo, /notificaciones, /conocimiento
    → index.html, field.html, notifications.html, knowledge.html
  - FAB absent from analytics pages: /intel, /vuelos, /estado
    → intel.html, flights.html, status.html
  - FAB link: href="/whatsapp-demo", target="_self"
  - FAB has id="whatsapp-fab"
"""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

FRONTEND = Path(__file__).parent.parent / "frontend"

FARMER_PAGES = [
    ("index.html", "/"),
    ("field.html", "/campo"),
    ("notifications.html", "/notificaciones"),
    ("knowledge.html", "/conocimiento"),
]

ANALYTICS_PAGES = [
    ("intel.html", "/intel"),
    ("flights.html", "/vuelos"),
    ("status.html", "/estado"),
]


def load(filename: str) -> BeautifulSoup:
    path = FRONTEND / filename
    assert path.exists(), f"HTML file not found: {path}"
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


# ---------------------------------------------------------------------------
# FAB present on farmer pages
# ---------------------------------------------------------------------------

class TestF5FabPresentOnFarmerPages:
    @pytest.mark.parametrize("filename,route", FARMER_PAGES)
    def test_fab_element_exists(self, filename, route):
        soup = load(filename)
        fab = soup.find(id="whatsapp-fab")
        assert fab is not None, (
            f"Missing #whatsapp-fab on {filename} ({route})"
        )

    @pytest.mark.parametrize("filename,route", FARMER_PAGES)
    def test_fab_href_points_to_whatsapp_demo(self, filename, route):
        soup = load(filename)
        fab = soup.find(id="whatsapp-fab")
        assert fab is not None, f"Missing #whatsapp-fab on {filename}"
        href = fab.get("href") or fab.find("a", href=True)
        if isinstance(href, str):
            assert href == "/whatsapp-demo", (
                f"{filename}: FAB href should be '/whatsapp-demo', got '{href}'"
            )
        else:
            # fab itself may be a container; find the <a> inside
            link = fab if fab.name == "a" else fab.find("a", href=True)
            assert link is not None, f"{filename}: No <a> found in/on #whatsapp-fab"
            assert link.get("href") == "/whatsapp-demo", (
                f"{filename}: FAB href should be '/whatsapp-demo', got '{link.get('href')}'"
            )

    @pytest.mark.parametrize("filename,route", FARMER_PAGES)
    def test_fab_target_self(self, filename, route):
        soup = load(filename)
        fab = soup.find(id="whatsapp-fab")
        assert fab is not None, f"Missing #whatsapp-fab on {filename}"
        # The element with id may be an <a> or contain one
        link = fab if fab.name == "a" else fab.find("a", href=True)
        assert link is not None, f"{filename}: No <a> found in/on #whatsapp-fab"
        assert link.get("target") == "_self", (
            f"{filename}: FAB target should be '_self', got '{link.get('target')}'"
        )

    @pytest.mark.parametrize("filename,route", FARMER_PAGES)
    def test_fab_is_anchor_or_contains_anchor(self, filename, route):
        soup = load(filename)
        fab = soup.find(id="whatsapp-fab")
        assert fab is not None, f"Missing #whatsapp-fab on {filename}"
        is_anchor = fab.name == "a"
        has_anchor = fab.find("a") is not None
        assert is_anchor or has_anchor, (
            f"{filename}: #whatsapp-fab should be or contain an <a> tag"
        )


# ---------------------------------------------------------------------------
# FAB absent from analytics pages
# ---------------------------------------------------------------------------

class TestF5FabAbsentOnAnalyticsPages:
    @pytest.mark.parametrize("filename,route", ANALYTICS_PAGES)
    def test_fab_not_present(self, filename, route):
        soup = load(filename)
        fab = soup.find(id="whatsapp-fab")
        assert fab is None, (
            f"#whatsapp-fab should NOT appear on analytics page {filename} ({route})"
        )
