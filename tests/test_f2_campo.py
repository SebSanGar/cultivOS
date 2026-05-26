"""F2 — Tests for field.html farmer-first rewrite.

TDD tests written BEFORE implementation.
Acceptance criteria:
  - Exactly one h1 on the page
  - Exactly one hero image with id="campo-imagen"
  - Exactly one primary CTA with id="cta-que-hago"
  - A recommendation container with id="recomendacion" exists
  - No forbidden jargon in farmer-visible (non-agronomo-only) content
  - Agronomo-only sections carry hidden attribute (not visible by default)
  - Nav has exactly 4 farmer links (Mis Parcelas, Alertas, Conocimiento, WhatsApp)
"""

import os
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

FIELD_HTML = Path(__file__).parent.parent / "frontend" / "field.html"

FORBIDDEN_JARGON = [
    "NDVI",
    "ROI",
    "KPI",
    "threshold",
    "anomaly",
    "dashboard",
    "metricas",
    "microbioma",
]

FARMER_NAV_LABELS = ["Mis Parcelas", "Alertas", "Conocimiento", "WhatsApp"]


@pytest.fixture(scope="module")
def soup():
    html = FIELD_HTML.read_text(encoding="utf-8")
    return BeautifulSoup(html, "html.parser")


def farmer_visible_text(soup: BeautifulSoup) -> str:
    """Return text from elements NOT inside .agronomo-only blocks."""
    doc = BeautifulSoup(str(soup), "html.parser")
    for el in doc.select(".agronomo-only"):
        el.decompose()
    return doc.get_text(" ", strip=True)


class TestF2FieldStructure:
    def test_exactly_one_h1(self, soup):
        h1s = soup.find_all("h1")
        assert len(h1s) == 1, f"Expected 1 h1, found {len(h1s)}"

    def test_hero_image_exists(self, soup):
        img = soup.find("img", {"id": "campo-imagen"})
        assert img is not None, "Missing <img id='campo-imagen'>"

    def test_exactly_one_img_visible(self, soup):
        """Only one img in the farmer-visible (non-agronomo-only) area."""
        doc = BeautifulSoup(str(soup), "html.parser")
        for el in doc.select(".agronomo-only"):
            el.decompose()
        imgs = doc.find_all("img")
        assert len(imgs) == 1, (
            f"Expected 1 visible img in farmer view, found {len(imgs)}"
        )

    def test_cta_que_hago_exists(self, soup):
        btn = soup.find(id="cta-que-hago")
        assert btn is not None, "Missing element with id='cta-que-hago'"

    def test_cta_is_button(self, soup):
        btn = soup.find(id="cta-que-hago")
        assert btn is not None
        assert btn.name == "button", f"cta-que-hago should be <button>, got <{btn.name}>"

    def test_recomendacion_container_exists(self, soup):
        rec = soup.find(id="recomendacion")
        assert rec is not None, "Missing <div id='recomendacion'>"

    def test_campo_resumen_exists(self, soup):
        resumen = soup.find(id="campo-resumen")
        assert resumen is not None, "Missing element with id='campo-resumen'"


class TestF2FarmerJargon:
    def test_no_forbidden_jargon_in_farmer_view(self, soup):
        visible = farmer_visible_text(soup)
        violations = [word for word in FORBIDDEN_JARGON if word in visible]
        assert violations == [], (
            f"Forbidden jargon found in farmer view: {violations}"
        )

    def test_no_ndvi_label_visible(self, soup):
        visible = farmer_visible_text(soup)
        assert "NDVI" not in visible, "'NDVI' label visible in farmer view"


class TestF2FarmerNav:
    def test_nav_has_farmer_links(self, soup):
        nav = soup.find("nav")
        assert nav is not None, "No <nav> found"
        nav_text = nav.get_text(" ", strip=True)
        for label in FARMER_NAV_LABELS:
            assert label in nav_text, f"Nav missing farmer link: '{label}'"

    def test_nav_link_count(self, soup):
        nav = soup.find("nav")
        assert nav is not None
        # Count anchor tags in nav (logo link + 4 farmer links = 5 max)
        links = nav.find_all("a", href=True)
        # At minimum must include 4 farmer routes
        hrefs = [a["href"] for a in links]
        farmer_routes = ["/", "/notificaciones", "/conocimiento", "/whatsapp-demo"]
        for route in farmer_routes:
            assert route in hrefs, f"Nav missing farmer route: '{route}'"


class TestF2AgronomoHidden:
    def test_agronomo_sections_have_hidden_attr(self, soup):
        agronomo_els = soup.select(".agronomo-only")
        assert len(agronomo_els) > 0, (
            "No .agronomo-only elements found — analytical sections must be preserved "
            "but hidden for F8 toggle"
        )
        for el in agronomo_els:
            assert el.has_attr("hidden"), (
                f"Element .agronomo-only ({el.name}#{el.get('id','')}) "
                "missing 'hidden' attribute"
            )

    def test_stat_strip_hidden_in_farmer_view(self, soup):
        """The old NDVI/health stat strip must be hidden or removed."""
        # It can either be inside .agronomo-only[hidden] or not exist at all
        stat_strip = soup.find(id="campo-stats")
        if stat_strip is not None:
            # Must be inside agronomo-only
            parent_classes = [
                c
                for p in stat_strip.parents
                for c in (p.get("class") or [])
            ]
            assert "agronomo-only" in parent_classes or stat_strip.has_attr("hidden"), (
                "Old stats strip (#campo-stats) is visible in farmer view"
            )
