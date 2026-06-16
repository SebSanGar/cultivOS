"""Guard: the shared canonical nav (frontend/nav.js) is wired everywhere.

Root cause it locks down: every app page used to hand-roll its own <nav>, so the
tab set drifted page-to-page (10+ variants) and the agronomist toggle (toggle.js)
was live on only 4/87 pages. Fix = a single self-contained nav.js rendering the
dashboard nav on every app page. These tests assert that wiring stays intact.

nav.js must load BEFORE i18n.js so i18n's DOMContentLoaded localizes the rendered
nav labels and wires the ES/EN toggle.
"""
import glob
import os

FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
NAV_JS = '<script src="/nav.js"></script>'
I18N_JS = '<script src="/i18n.js"></script>'

# Pages that intentionally do NOT get the canonical nav:
#  - auth/public shells: login, demo, walkthrough
#  - farmer-minimal pages (founder decision — keep their own minimal nav):
#    field, impacto-agricultor
EXCLUDED = {
    "login.html",
    "demo.html",
    "walkthrough.html",
    "field.html",
    "impacto-agricultor.html",
}


def _app_pages():
    pages = [os.path.basename(p) for p in glob.glob(os.path.join(FRONTEND, "*.html"))]
    return [p for p in pages if p not in EXCLUDED]


def test_every_app_page_includes_nav_js():
    missing = []
    for page in _app_pages():
        with open(os.path.join(FRONTEND, page), encoding="utf-8") as f:
            if NAV_JS not in f.read():
                missing.append(page)
    assert not missing, f"pages missing shared nav.js: {missing}"


def test_nav_js_loads_before_i18n_js():
    """nav.js renders the DOM that i18n then localizes — order matters."""
    bad = []
    for page in _app_pages():
        with open(os.path.join(FRONTEND, page), encoding="utf-8") as f:
            src = f.read()
        if NAV_JS in src and I18N_JS in src:
            if src.index(NAV_JS) > src.index(I18N_JS):
                bad.append(page)
    assert not bad, f"nav.js must load before i18n.js on: {bad}"


def test_excluded_pages_do_not_get_canonical_nav():
    leaked = []
    for page in EXCLUDED:
        path = os.path.join(FRONTEND, page)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            if NAV_JS in f.read():
                leaked.append(page)
    assert not leaked, f"excluded pages should not include nav.js: {leaked}"


def test_toggle_js_only_remains_on_field():
    """toggle.js is superseded by nav.js everywhere except the farmer field page,
    which keeps its minimal nav + its own agronomist toggle."""
    offenders = []
    for page in [os.path.basename(p) for p in glob.glob(os.path.join(FRONTEND, "*.html"))]:
        if page == "field.html":
            continue
        with open(os.path.join(FRONTEND, page), encoding="utf-8") as f:
            if '<script src="/toggle.js"></script>' in f.read():
                offenders.append(page)
    assert not offenders, f"toggle.js should only remain on field.html, found on: {offenders}"


def test_nav_js_renders_canonical_tab_set():
    """nav.js must contain the founder-locked canonical tabs + agronomist extras."""
    with open(os.path.join(FRONTEND, "nav.js"), encoding="utf-8") as f:
        src = f.read()
    farmer = ["nav.farms", "nav.alerts", "nav.knowledge", "nav.whatsapp"]
    extras = ["nav.intel", "nav.map", "nav.flights", "nav.platform", "nav.status"]
    for key in farmer + extras:
        assert key in src, f"canonical nav key missing from nav.js: {key}"
    assert 'class="nav-agronomo-extras" hidden' in src, "agronomist extras must be hidden by default"
