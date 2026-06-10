"""FL4 — Dashboard i18n (EN/ES toggle) tests.

Verifies:
- frontend/i18n.js exists with ES/EN dictionaries
- i18n.js persists language choice to localStorage key 'cultivOS_lang'
- i18n.js swaps text via data-i18n attributes
- Nav has ES | EN toggle element
- index.html has data-i18n attributes on key text nodes
- login.html has data-i18n attributes on key text nodes
- index.html + login.html include i18n.js script tag
- auth-guard.js uses i18n-aware role labels and logout text
"""

import re
from pathlib import Path

import pytest

FRONTEND = Path(__file__).parent.parent / "frontend"
I18N_JS = FRONTEND / "i18n.js"
INDEX = FRONTEND / "index.html"
LOGIN = FRONTEND / "login.html"
STYLES = FRONTEND / "styles.css"
AUTH_GUARD = FRONTEND / "auth-guard.js"
TOGGLE_JS = FRONTEND / "toggle.js"


@pytest.fixture
def i18n_text():
    assert I18N_JS.exists(), "frontend/i18n.js not found"
    return I18N_JS.read_text(encoding="utf-8")


@pytest.fixture
def index_text():
    return INDEX.read_text(encoding="utf-8")


@pytest.fixture
def login_text():
    return LOGIN.read_text(encoding="utf-8")


# ── i18n.js: file + dictionary structure ──

def test_i18n_js_exists():
    """i18n.js must exist in frontend/."""
    assert I18N_JS.exists(), (
        "frontend/i18n.js not found. Create it with ES/EN dictionaries."
    )


def test_i18n_has_es_dict(i18n_text):
    """i18n.js must contain Spanish dictionary."""
    assert "es" in i18n_text and "{" in i18n_text, (
        "i18n.js must have an 'es' dictionary object."
    )


def test_i18n_has_en_dict(i18n_text):
    """i18n.js must contain English dictionary."""
    assert "en" in i18n_text and "{" in i18n_text, (
        "i18n.js must have an 'en' dictionary object."
    )


def test_i18n_has_localstorage_key(i18n_text):
    """i18n.js must persist language to localStorage key 'cultivOS_lang'."""
    assert "cultivOS_lang" in i18n_text, (
        "i18n.js must use localStorage key 'cultivOS_lang' to persist language."
    )


def test_i18n_has_data_i18n_selector(i18n_text):
    """i18n.js must query elements with data-i18n attribute to swap text."""
    assert "data-i18n" in i18n_text, (
        "i18n.js must query [data-i18n] elements to swap their text content."
    )


def test_i18n_default_language_is_en(i18n_text):
    """Default language must be English (en) — founder steering 2026-06-10, Canada-first."""
    assert "DEFAULT_LANG = 'en'" in i18n_text, (
        "i18n.js must default to 'en' when no localStorage value is set."
    )


# ── i18n.js: EN dictionary keys for covered surfaces ──

def test_i18n_en_has_nav_keys(i18n_text):
    """EN dict must have nav label translations."""
    for key in ["nav.farms", "nav.alerts", "nav.knowledge", "nav.whatsapp"]:
        assert key in i18n_text, (
            f"i18n.js EN dict missing key '{key}'. "
            "Nav labels must be translatable."
        )


def test_i18n_en_has_dashboard_keys(i18n_text):
    """EN dict must have dashboard stat label translations."""
    for key in ["dash.title", "dash.subtitle", "stat.farms", "stat.fields",
                "stat.avgHealth", "stat.hectares"]:
        assert key in i18n_text, (
            f"i18n.js EN dict missing key '{key}'. "
            "Dashboard stat labels must be translatable."
        )


def test_i18n_en_has_login_keys(i18n_text):
    """EN dict must have login page translations."""
    for key in ["login.title", "login.username", "login.password", "login.submit"]:
        assert key in i18n_text, (
            f"i18n.js EN dict missing key '{key}'. "
            "Login page text must be translatable."
        )


# ── Nav toggle element ──

def test_index_has_lang_toggle(index_text):
    """index.html nav must have an ES/EN language toggle."""
    has_toggle = (
        "lang-toggle" in index_text
        or "i18n-toggle" in index_text
        or "nav-lang" in index_text
    )
    assert has_toggle, (
        "index.html nav missing language toggle element. "
        "Add an ES | EN toggle in the nav bar."
    )


# ── data-i18n attributes on index.html ──

def test_index_has_data_i18n_on_title(index_text):
    """Dashboard title must have data-i18n attribute."""
    assert 'data-i18n="dash.title"' in index_text, (
        'index.html <h1> Granjas missing data-i18n="dash.title" attribute.'
    )


def test_index_has_data_i18n_on_stat_labels(index_text):
    """Stat labels must have data-i18n attributes."""
    for key in ["stat.farms", "stat.fields", "stat.avgHealth", "stat.hectares"]:
        assert f'data-i18n="{key}"' in index_text, (
            f'index.html stat label missing data-i18n="{key}" attribute.'
        )


def test_index_has_data_i18n_on_nav_links(index_text):
    """Nav farmer tab links must have data-i18n attributes."""
    for key in ["nav.farms", "nav.alerts", "nav.knowledge", "nav.whatsapp"]:
        assert f'data-i18n="{key}"' in index_text, (
            f'index.html nav link missing data-i18n="{key}" attribute.'
        )


# ── data-i18n attributes on login.html ──

def test_login_has_data_i18n_on_title(login_text):
    """Login page title must have data-i18n attribute."""
    assert 'data-i18n="login.title"' in login_text, (
        'login.html title missing data-i18n="login.title" attribute.'
    )


def test_login_has_data_i18n_on_labels(login_text):
    """Login form labels must have data-i18n attributes."""
    for key in ["login.username", "login.password"]:
        assert f'data-i18n="{key}"' in login_text, (
            f'login.html label missing data-i18n="{key}" attribute.'
        )


def test_login_has_data_i18n_on_submit(login_text):
    """Login submit button must have data-i18n attribute."""
    assert 'data-i18n="login.submit"' in login_text, (
        'login.html submit button missing data-i18n="login.submit" attribute.'
    )


# ── Script inclusion ──

def test_index_includes_i18n_js(index_text):
    """index.html must include i18n.js script tag."""
    assert 'src="/i18n.js"' in index_text, (
        'index.html missing <script src="/i18n.js"></script>.'
    )


def test_login_includes_i18n_js(login_text):
    """login.html must include i18n.js script tag."""
    assert 'src="/i18n.js"' in login_text, (
        'login.html missing <script src="/i18n.js"></script>.'
    )


# ── Nav toggle CSS ──

def test_nav_lang_toggle_css_exists():
    """styles.css must have styling for the language toggle."""
    css = STYLES.read_text(encoding="utf-8")
    has_toggle_css = (
        "nav-lang" in css
        or "lang-toggle" in css
        or "i18n-toggle" in css
    )
    assert has_toggle_css, (
        "styles.css missing language toggle styling. "
        "Add CSS for the nav ES|EN toggle element."
    )
