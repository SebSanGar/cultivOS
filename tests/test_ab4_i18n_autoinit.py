"""
AB4 — i18n auto-init on mapa.html and economic-impact.html.

Both pages were translated to English (AB3) but don't load i18n.js,
so the stored lang preference never applies.  Adds:
  - <script src="/i18n.js"> to both pages
  - data-i18n attrs on mapa.html nav links (so they respond to lang switch)
  - data-i18n on missing nav links in economic-impact.html
"""
import pytest
from pathlib import Path

FRONTEND = Path(__file__).parent.parent / "frontend"

MAPA_HTML = (FRONTEND / "mapa.html").read_text()
ECON_HTML = (FRONTEND / "economic-impact.html").read_text()


# ── mapa.html ─────────────────────────────────────────────────────────────────

def test_mapa_loads_i18n_js():
    assert 'src="/i18n.js"' in MAPA_HTML, "mapa.html must load /i18n.js"


def test_mapa_farms_nav_has_data_i18n():
    assert 'data-i18n="nav.farms"' in MAPA_HTML


def test_mapa_intel_nav_has_data_i18n():
    assert 'data-i18n="nav.intel"' in MAPA_HTML


def test_mapa_map_nav_active_has_data_i18n():
    assert 'data-i18n="nav.map"' in MAPA_HTML


def test_mapa_notifications_nav_has_data_i18n():
    assert 'data-i18n="nav.alerts"' in MAPA_HTML


def test_mapa_status_nav_has_data_i18n():
    assert 'data-i18n="nav.status"' in MAPA_HTML


def test_mapa_logout_has_data_i18n():
    assert 'data-i18n="user.logout"' in MAPA_HTML


# ── economic-impact.html ──────────────────────────────────────────────────────

def test_econ_loads_i18n_js():
    assert 'src="/i18n.js"' in ECON_HTML, "economic-impact.html must load /i18n.js"


def test_econ_recommendations_nav_has_data_i18n():
    """nav link to /recomendaciones was hardcoded English without data-i18n."""
    assert 'data-i18n="nav.recommendations"' in ECON_HTML


def test_econ_economic_impact_nav_has_data_i18n():
    """Active nav link for this page should have data-i18n."""
    assert 'data-i18n="nav.economic_impact"' in ECON_HTML


def test_econ_all_nav_links_have_data_i18n():
    """Every <a> inside .nav-tabs should carry a data-i18n attr."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(ECON_HTML, "html.parser")
    nav = soup.find("nav", class_="intel-nav")
    assert nav is not None, "intel-nav not found"
    tabs = nav.find("ul", class_="nav-tabs")
    assert tabs is not None, "nav-tabs not found"
    links = tabs.find_all("a")
    assert len(links) >= 6, "expected ≥6 nav links"
    missing = [a.get_text(strip=True) for a in links if not a.get("data-i18n")]
    assert not missing, f"nav links missing data-i18n: {missing}"


# ── i18n.js dict completeness ─────────────────────────────────────────────────

def test_i18n_dict_has_nav_map_key():
    I18N = (FRONTEND / "i18n.js").read_text()
    assert "'nav.map'" in I18N or '"nav.map"' in I18N, "i18n.js must have nav.map key in both dicts"


def test_i18n_dict_has_nav_recommendations_key():
    I18N = (FRONTEND / "i18n.js").read_text()
    assert "'nav.recommendations'" in I18N or '"nav.recommendations"' in I18N


def test_i18n_dict_has_nav_economic_impact_key():
    I18N = (FRONTEND / "i18n.js").read_text()
    assert "'nav.economic_impact'" in I18N or '"nav.economic_impact"' in I18N
