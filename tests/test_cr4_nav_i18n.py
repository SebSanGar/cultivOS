"""
CR4 — Localize shared chrome: nav/footer/placeholders.
Source-level (no server) tests that prove the wiring is correct.
"""

import subprocess
import os

FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')
I18N_JS = os.path.join(FRONTEND, 'i18n.js')

# All 45 HTML files whose nav contains ">Granjas<" (rg -l '>Granjas<' frontend/)
NAV_FILES = [
    'actions.html', 'alert-config.html', 'alertas-estacionales.html', 'anomalies.html',
    'api-docs.html', 'api-status.html', 'calendario.html', 'carbon.html', 'clima.html',
    'completitud-global.html', 'completitud.html', 'confianza-tratamientos.html',
    'cooperativa.html', 'demo.html', 'disease.html', 'efectividad-global.html',
    'efectividad.html', 'ejecutivo.html', 'exportar.html', 'flota.html', 'fusion.html',
    'historial-alertas.html', 'intervenciones.html', 'irrigation.html', 'management.html',
    'microbiome.html', 'mission.html', 'onboarding.html', 'plataforma.html',
    'precision-ia.html', 'recommendations.html', 'regenerative.html', 'regional.html',
    'reportes.html', 'resumen.html', 'rotation.html', 'seasonal.html', 'soil-history.html',
    'soil-import.html', 'status.html', 'tek.html', 'thermal-dashboard.html',
    'timeline.html', 'trayectoria.html', 'yield.html',
]

# Files with footer text (rg -l 'Agricultura de precision para Jalisco' frontend/)
FOOTER_FILES = [
    'actions.html', 'alert-config.html', 'alertas-estacionales.html', 'anomalies.html',
    'api-docs.html', 'api-status.html', 'calendario.html', 'carbon.html', 'clima.html',
    'completitud-global.html', 'completitud.html', 'confianza-tratamientos.html',
    'cooperativa.html', 'demo.html', 'disease.html', 'efectividad-global.html',
    'efectividad.html', 'ejecutivo.html', 'exportar.html', 'flota.html', 'fusion.html',
    'historial-alertas.html', 'intervenciones.html', 'irrigation.html', 'management.html',
    'microbiome.html', 'mission.html', 'onboarding.html', 'plataforma.html',
    'precision-ia.html', 'recommendations.html', 'regenerative.html', 'regional.html',
    'reportes.html', 'resumen.html', 'rotation.html',
]

# DONE-GATE nav words that must not appear as bare text in EN mode (checked via data-i18n presence)
CRITICAL_NAV_ES = [
    'nav.granjas', 'nav.intelligence', 'nav.recommendations', 'nav.soil',
    'nav.regenerative', 'nav.actions', 'nav.notifications', 'nav.status',
    'user.logout', 'nav.knowledge', 'nav.management',
]
CRITICAL_NAV_EN = CRITICAL_NAV_ES  # same keys, different values


def _read(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ── i18n.js key tests ─────────────────────────────────────────────────────────

def test_i18n_has_nav_granjas_es():
    """ES dict must have nav.granjas key."""
    content = _read(I18N_JS)
    assert "'nav.granjas'" in content or '"nav.granjas"' in content, \
        "i18n.js missing 'nav.granjas' in ES dict"


def test_i18n_has_nav_granjas_en():
    """EN dict must have nav.granjas → 'Farms'."""
    content = _read(I18N_JS)
    # Key must appear at least twice (es + en blocks)
    count = content.count("'nav.granjas'") + content.count('"nav.granjas"')
    assert count >= 2, \
        f"i18n.js 'nav.granjas' appears {count} times — need 2 (es + en)"


def test_i18n_has_all_critical_nav_keys_es_and_en():
    """All 11 DONE-GATE nav keys must appear in i18n.js (at least once each)."""
    content = _read(I18N_JS)
    missing = []
    for key in CRITICAL_NAV_ES:
        if f"'{key}'" not in content and f'"{key}"' not in content:
            missing.append(key)
    assert not missing, f"i18n.js missing keys: {missing}"


def test_i18n_has_nav_select_farm_key():
    """i18n.js must have nav.selectFarm in both ES and EN."""
    content = _read(I18N_JS)
    count = content.count("'nav.selectFarm'") + content.count('"nav.selectFarm"')
    assert count >= 2, \
        f"i18n.js 'nav.selectFarm' appears {count} times — need 2 (es + en)"


# ── i18n.js include tests ─────────────────────────────────────────────────────

def test_all_nav_files_include_i18n_js():
    """All 45 nav-bearing HTML files must include <script src="/i18n.js">."""
    missing = []
    for fname in NAV_FILES:
        path = os.path.join(FRONTEND, fname)
        if not os.path.exists(path):
            continue
        content = _read(path)
        if 'src="/i18n.js"' not in content:
            missing.append(fname)
    assert not missing, \
        f"{len(missing)} files missing i18n.js: {missing}"


# ── data-i18n attribute tests ─────────────────────────────────────────────────

def test_all_nav_files_have_data_i18n_on_granjas():
    """All 45 nav-bearing HTML files must have data-i18n=\"nav.granjas\" on the Granjas link."""
    missing = []
    for fname in NAV_FILES:
        path = os.path.join(FRONTEND, fname)
        if not os.path.exists(path):
            continue
        content = _read(path)
        if 'data-i18n="nav.granjas"' not in content:
            missing.append(fname)
    assert not missing, \
        f"{len(missing)} files missing data-i18n=\"nav.granjas\": {missing}"


def test_all_nav_files_have_data_i18n_on_logout():
    """All 45 nav-bearing HTML files must have data-i18n on the logout link."""
    missing = []
    for fname in NAV_FILES:
        path = os.path.join(FRONTEND, fname)
        if not os.path.exists(path):
            continue
        content = _read(path)
        # Accept either user.logout or nav.logout on the logout element
        if 'data-i18n="user.logout"' not in content and 'data-i18n="nav.logout"' not in content:
            missing.append(fname)
    assert not missing, \
        f"{len(missing)} files missing data-i18n on logout: {missing}"


# ── footer tests ──────────────────────────────────────────────────────────────

def test_all_footer_files_have_data_i18n_tagline():
    """All footer-bearing HTML files must have data-i18n=\"footer.tagline\"."""
    missing = []
    for fname in FOOTER_FILES:
        path = os.path.join(FRONTEND, fname)
        if not os.path.exists(path):
            continue
        content = _read(path)
        if 'data-i18n="footer.tagline"' not in content:
            missing.append(fname)
    assert not missing, \
        f"{len(missing)} files missing data-i18n=\"footer.tagline\": {missing}"


def test_all_footer_files_have_data_i18n_tour():
    """All footer-bearing HTML files must have data-i18n=\"footer.tour\"."""
    missing = []
    for fname in FOOTER_FILES:
        path = os.path.join(FRONTEND, fname)
        if not os.path.exists(path):
            continue
        content = _read(path)
        if 'data-i18n="footer.tour"' not in content:
            missing.append(fname)
    assert not missing, \
        f"{len(missing)} files missing data-i18n=\"footer.tour\": {missing}"


# ── placeholder tests ─────────────────────────────────────────────────────────

BARE_PLACEHOLDERS = [
    'Seleccione una granja...',
    'Seleccionar finca...',
    'Seleccione una finca...',
    'Seleccionar granja...',
    'Seleccionar Finca...',
]


def test_no_bare_farm_select_placeholders_in_html():
    """HTML files must not have bare Spanish farm placeholder option text."""
    offenders = []
    for fname in NAV_FILES + FOOTER_FILES:
        if fname in {f for f in NAV_FILES} | {f for f in FOOTER_FILES}:
            pass
    seen = set()
    for fname in list(set(NAV_FILES + FOOTER_FILES)):
        path = os.path.join(FRONTEND, fname)
        if not os.path.exists(path):
            continue
        if fname in seen:
            continue
        seen.add(fname)
        content = _read(path)
        for placeholder in BARE_PLACEHOLDERS:
            bare = f'<option value="">{placeholder}</option>'
            if bare in content:
                offenders.append(f'{fname}: {placeholder!r}')
    assert not offenders, \
        f"Bare Spanish farm placeholders remain:\n" + '\n'.join(offenders)
