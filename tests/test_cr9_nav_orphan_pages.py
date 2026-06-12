"""
CR9 — Add shared nav to 3 orphan full pages: nutrientes-suelo, prediccion-salud, plan-accion.
Done-gate: each route renders standard nav OR at minimum one working back/home link.
Source-inspection tests (no server).
"""

import os

FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')


def _html(name: str) -> str:
    with open(os.path.join(FRONTEND, name), 'r', encoding='utf-8') as f:
        return f.read()


# --- nutrientes-suelo.html ---

def test_nutrientes_suelo_has_nav():
    html = _html('nutrientes-suelo.html')
    assert '<nav class="intel-nav">' in html, 'nutrientes-suelo missing <nav class="intel-nav">'


def test_nutrientes_suelo_nav_has_logo():
    html = _html('nutrientes-suelo.html')
    assert 'nav-logo' in html, 'nutrientes-suelo nav missing logo link'


def test_nutrientes_suelo_nav_has_tabs():
    html = _html('nutrientes-suelo.html')
    assert html.count('class="nav-tab') >= 4, 'nutrientes-suelo nav has fewer than 4 tabs'


def test_nutrientes_suelo_nav_home_link():
    html = _html('nutrientes-suelo.html')
    assert 'href="/"' in html, 'nutrientes-suelo missing home link'


# --- prediccion-salud.html ---

def test_prediccion_salud_has_nav():
    html = _html('prediccion-salud.html')
    assert '<nav class="intel-nav">' in html, 'prediccion-salud missing <nav class="intel-nav">'


def test_prediccion_salud_nav_has_logo():
    html = _html('prediccion-salud.html')
    assert 'nav-logo' in html, 'prediccion-salud nav missing logo link'


def test_prediccion_salud_nav_has_tabs():
    html = _html('prediccion-salud.html')
    assert html.count('class="nav-tab') >= 4, 'prediccion-salud nav has fewer than 4 tabs'


def test_prediccion_salud_nav_home_link():
    html = _html('prediccion-salud.html')
    assert 'href="/"' in html, 'prediccion-salud missing home link'


# --- plan-accion.html ---

def test_plan_accion_has_back_or_nav():
    """Done-gate: back-link is sufficient (farmer-mode widget, documented embed)."""
    html = _html('plan-accion.html')
    has_nav = '<nav class="intel-nav">' in html
    has_back = 'href="/"' in html
    assert has_nav or has_back, 'plan-accion missing both nav and home/back link'


def test_plan_accion_back_link_exists():
    html = _html('plan-accion.html')
    assert 'href="/"' in html, 'plan-accion missing href="/" link'


def test_plan_accion_not_zero_links():
    """No zero-link pages per done-gate."""
    html = _html('plan-accion.html')
    import re
    links = re.findall(r'<a\s[^>]*href=', html)
    assert len(links) >= 1, 'plan-accion has zero <a href> links — stranded'
