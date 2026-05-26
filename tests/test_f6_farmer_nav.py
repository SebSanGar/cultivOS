"""F6 — Tests for farmer nav hiding analytical screens.

TDD tests written BEFORE implementation.
Acceptance criteria:
  - Farmer nav on /, /notificaciones, /conocimiento = exactly 4 links
  - 4 links: Mis Parcelas (/), Alertas (/notificaciones),
    Conocimiento (/conocimiento), WhatsApp (/whatsapp-demo)
  - Analytical hrefs (/intel, /vuelos, /estado, /mapa, /plataforma)
    absent from visible farmer nav on those pages
  - Analytical links present in a nav-agronomo-extras[hidden] block (F8-ready)
  - field.html farmer nav (from F2) still intact — not broken
"""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

FRONTEND = Path(__file__).parent.parent / "frontend"

FARMER_PAGES = [
    "index.html",
    "notifications.html",
    "knowledge.html",
    "field.html",
]

EXPECTED_FARMER_LINKS = [
    ("/", "Mis Parcelas"),
    ("/notificaciones", "Alertas"),
    ("/conocimiento", "Conocimiento"),
    ("/whatsapp-demo", "WhatsApp"),
]

ANALYTICAL_HREFS = ["/intel", "/vuelos", "/estado", "/mapa", "/plataforma"]


def load(filename: str) -> BeautifulSoup:
    path = FRONTEND / filename
    assert path.exists(), f"HTML file not found: {path}"
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def get_farmer_nav(soup: BeautifulSoup):
    """Return the nav-farmer-tabs <ul> element."""
    return soup.find("ul", class_="nav-farmer-tabs")


# ---------------------------------------------------------------------------
# nav-farmer-tabs structure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", FARMER_PAGES)
def test_farmer_nav_tabs_present(filename):
    """Every farmer page has a nav-farmer-tabs ul."""
    soup = load(filename)
    nav = get_farmer_nav(soup)
    assert nav is not None, f"{filename}: nav-farmer-tabs not found"


@pytest.mark.parametrize("filename", FARMER_PAGES)
def test_farmer_nav_has_exactly_4_links(filename):
    """Farmer nav contains exactly 4 <a> links — no analytical extras."""
    soup = load(filename)
    nav = get_farmer_nav(soup)
    assert nav is not None, f"{filename}: nav-farmer-tabs not found"
    links = nav.find_all("a")
    assert len(links) == 4, (
        f"{filename}: expected 4 farmer nav links, got {len(links)}: "
        + str([a.get("href") for a in links])
    )


# ---------------------------------------------------------------------------
# Correct hrefs and labels
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", FARMER_PAGES)
@pytest.mark.parametrize("href,label", EXPECTED_FARMER_LINKS)
def test_farmer_nav_has_correct_link(filename, href, label):
    """Each expected farmer link is present with correct href."""
    soup = load(filename)
    nav = get_farmer_nav(soup)
    assert nav is not None, f"{filename}: nav-farmer-tabs not found"
    link = nav.find("a", href=href)
    assert link is not None, (
        f"{filename}: farmer nav missing link href='{href}' (label: {label})"
    )


# ---------------------------------------------------------------------------
# Analytical links absent from farmer nav
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", ["index.html", "notifications.html", "knowledge.html"])
@pytest.mark.parametrize("analytical_href", ANALYTICAL_HREFS)
def test_analytical_href_absent_from_farmer_nav(filename, analytical_href):
    """Analytical routes must not appear in the visible farmer nav."""
    soup = load(filename)
    nav = get_farmer_nav(soup)
    assert nav is not None, f"{filename}: nav-farmer-tabs not found"
    bad = nav.find("a", href=analytical_href)
    assert bad is None, (
        f"{filename}: analytical link '{analytical_href}' found in farmer nav — must be hidden"
    )


# ---------------------------------------------------------------------------
# Analytical links in hidden block (F8-ready)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", ["index.html", "notifications.html", "knowledge.html"])
def test_agronomo_extras_block_exists(filename):
    """nav-agronomo-extras hidden block exists for F8 agronomist toggle."""
    soup = load(filename)
    extras = soup.find("ul", class_="nav-agronomo-extras")
    assert extras is not None, (
        f"{filename}: nav-agronomo-extras block not found — needed for F8 agronomist toggle"
    )


@pytest.mark.parametrize("filename", ["index.html", "notifications.html", "knowledge.html"])
def test_agronomo_extras_is_hidden_by_default(filename):
    """nav-agronomo-extras must have hidden attribute by default."""
    soup = load(filename)
    extras = soup.find("ul", class_="nav-agronomo-extras")
    assert extras is not None, f"{filename}: nav-agronomo-extras block not found"
    assert extras.get("hidden") is not None or extras.get("hidden") == "", (
        f"{filename}: nav-agronomo-extras must have hidden attribute by default"
    )


@pytest.mark.parametrize("filename", ["index.html", "notifications.html", "knowledge.html"])
def test_analytical_links_in_agronomo_extras(filename):
    """At least one analytical link (/intel or /vuelos) exists in agronomo extras."""
    soup = load(filename)
    extras = soup.find("ul", class_="nav-agronomo-extras")
    assert extras is not None, f"{filename}: nav-agronomo-extras block not found"
    hrefs = [a.get("href") for a in extras.find_all("a")]
    analytical_found = [h for h in hrefs if h in ANALYTICAL_HREFS]
    assert len(analytical_found) >= 1, (
        f"{filename}: no analytical links found in nav-agronomo-extras: {hrefs}"
    )
