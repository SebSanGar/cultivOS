"""
EN-leak sweep — Canada-first/English-first leaked Spanish chrome strings.

Source-inspection tests (no server) in the CR5/CR6 style: assert the leaked
chrome string is routed through i18n (data-i18n attribute on HTML, or t()/_t()
call in JS), and that every new key exists in BOTH the ES and EN dicts of
i18n.js with the right language value.

Also covers the /campo direct-load graceful fallback.

Confirmed-DATA (NOT chrome, intentionally left): "Aplicar ..." treatment text
on /regional and /intel, and the "Sorgo: ... Cultivo resistente ..." seasonal
alert message on /regional — these are DB-sourced recommendation/alert values,
not UI chrome.
"""

import os

FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')
I18N_JS = os.path.join(FRONTEND, 'i18n.js')


def _read(name: str) -> str:
    with open(os.path.join(FRONTEND, name), 'r', encoding='utf-8') as f:
        return f.read()


def _i18n() -> str:
    return _read('i18n.js')


def _has_attr(html: str, key: str) -> bool:
    return f'data-i18n="{key}"' in html or f"data-i18n='{key}'" in html


def _has_ph_attr(html: str, key: str) -> bool:
    return f'data-i18n-placeholder="{key}"' in html


def _en_block(content: str) -> str:
    idx = content.find('en: {')
    assert idx != -1, "i18n.js: EN dict not found"
    return content[idx:]


def _es_block(content: str) -> str:
    es_idx = content.find('es: {')
    en_idx = content.find('en: {')
    assert es_idx != -1 and en_idx != -1
    return content[es_idx:en_idx]


def _key_value(block: str, key: str):
    """Return the raw value string for `key` within a dict block, or None."""
    import re
    for q in ("'", '"'):
        m = re.search(re.escape(q + key + q) + r'\s*:\s*([\'"])(.*?)\1', block)
        if m:
            return m.group(2)
    return None


def _en_value(key: str):
    return _key_value(_en_block(_i18n()), key)


def _es_value(key: str):
    return _key_value(_es_block(_i18n()), key)


def _assert_bilingual(key: str, en_must_be: str = None, es_must_be: str = None):
    ev = _en_value(key)
    sv = _es_value(key)
    assert ev is not None, f"i18n.js EN dict missing key '{key}'"
    assert sv is not None, f"i18n.js ES dict missing key '{key}'"
    if en_must_be is not None:
        assert ev == en_must_be, f"EN '{key}' = {ev!r}, expected {en_must_be!r}"
    if es_must_be is not None:
        assert sv == es_must_be, f"ES '{key}' = {sv!r}, expected {es_must_be!r}"


# ── /plataforma — full card grid + stats + filter wired ────────────────────────

PLAT_CARD_KEYS = [
    'pf.anomalias.t', 'pf.enfermedades.t', 'pf.recomendaciones.t', 'pf.riego.t',
    'pf.resumen.t', 'pf.efectividadglobal.t', 'pf.comparar.t', 'pf.mision.t',
    'pf.rotacion.t', 'pf.gestion.t', 'pf.intel.t', 'pf.calendario.t',
]


def test_plataforma_cards_have_data_i18n():
    html = _read('plataforma.html')
    for key in PLAT_CARD_KEYS:
        assert _has_attr(html, key), f"plataforma.html: card missing data-i18n='{key}'"


def test_plataforma_no_unwired_card_titles():
    html = _read('plataforma.html')
    assert 'page-card-title">' not in html, "plataforma.html: a page-card-title has no data-i18n"
    assert 'page-card-desc">' not in html, "plataforma.html: a page-card-desc has no data-i18n"
    assert 'category-desc">' not in html, "plataforma.html: a category-desc has no data-i18n"


def test_plataforma_filter_options_wired():
    html = _read('plataforma.html')
    for key in ('plataforma.crops', 'plataforma.cerebro', 'plataforma.operations'):
        assert _has_attr(html, key), f"plataforma.html: filter option missing data-i18n='{key}'"


def test_plataforma_stats_and_search_wired():
    html = _read('plataforma.html')
    for key in ('pf.statPages', 'pf.statEndpoints', 'pf.statTests', 'pf.statSources'):
        assert _has_attr(html, key), f"plataforma.html: kpi label missing data-i18n='{key}'"
    assert _has_ph_attr(html, 'pf.searchPlaceholder'), \
        "plataforma.html: search input missing data-i18n-placeholder"


def test_plataforma_card_keys_bilingual_and_english():
    # English value must not equal the Spanish value for representative cards.
    _assert_bilingual('pf.anomalias.t', en_must_be='Anomaly Detection')
    _assert_bilingual('pf.enfermedades.t', en_must_be='Disease Risk')
    _assert_bilingual('pf.recomendaciones.t', en_must_be='Recommendations')
    _assert_bilingual('pf.riego.t', en_must_be='Irrigation Schedule')
    _assert_bilingual('pf.resumen.t', en_must_be='Executive Summary')
    _assert_bilingual('pf.mision.t', en_must_be='Mission Planner')


# ── /estado (status) ───────────────────────────────────────────────────────────

def test_status_strip_labels_wired():
    html = _read('status.html')
    for key in ('status.statApiVersion', 'status.statUptime', 'status.statFarms',
                'status.statFields', 'status.soilLabel', 'status.dbLabel'):
        assert _has_attr(html, key), f"status.html: missing data-i18n='{key}'"


def test_status_endpoint_names_routed_through_t():
    js = _read('status.js')
    assert '_t(r.key, r.name)' in js, "status.js: endpoint names must render via _t(r.key, r.name)"
    for key in ('status.epFarms', 'status.epCrops', 'status.epStatus'):
        assert f"'{key}'" in js, f"status.js: ENDPOINTS missing key '{key}'"


def test_status_keys_bilingual():
    _assert_bilingual('status.statFarms', en_must_be='Farms', es_must_be='Granjas')
    _assert_bilingual('status.soilLabel', en_must_be='Soil', es_must_be='Suelo')
    _assert_bilingual('status.epCrops', en_must_be='Crops', es_must_be='Cultivos')


# ── /regional (regional.js rendered chrome) ────────────────────────────────────

def test_regional_js_chrome_routed_through_t():
    js = _read('regional.js')
    assert "_t('regional.distribCrops'" in js
    assert "_t('regional.topTreatments'" in js
    assert "_t('regional.thTreatment'" in js
    assert "_t('regional.thApplications'" in js
    assert "_t('regional.thOrganic'" in js
    # The hardcoded Spanish headings must be gone.
    assert '>Distribucion de Cultivos<' not in js
    assert '>Tratamientos Principales<' not in js
    assert '<th>Tratamiento</th>' not in js


def test_regional_keys_bilingual():
    _assert_bilingual('regional.distribCrops', en_must_be='Crop Distribution')
    _assert_bilingual('regional.topTreatments', en_must_be='Top Treatments')
    _assert_bilingual('regional.thTreatment', en_must_be='Treatment', es_must_be='Tratamiento')


# ── /enfermedades (disease) ────────────────────────────────────────────────────

def test_disease_chrome_wired():
    html = _read('disease.html')
    assert _has_attr(html, 'dis.selectPrompt'), "disease.html: empty state missing data-i18n"
    assert _has_attr(html, 'dis.cropOptional'), "disease.html: 'Cultivo (opcional)' label not wired"
    assert _has_attr(html, 'dis.symptomsLabel')
    assert _has_attr(html, 'dis.evaluation')


def test_disease_keys_bilingual():
    _assert_bilingual('dis.cropOptional', en_must_be='Crop (optional)', es_must_be='Cultivo (opcional)')
    # dis.selectPrompt pre-existed; just confirm EN is English.
    assert _en_value('dis.selectPrompt') == 'Select a farm and field to view risk.'


# ── /riego (irrigation) ────────────────────────────────────────────────────────

def test_irrigation_chrome_wired():
    html = _read('irrigation.html')
    assert _has_attr(html, 'irrigation.emptyPrompt')
    assert _has_attr(html, 'irrigation.weeklyTitle')
    assert _has_attr(html, 'irrigation.recommendation')


def test_irrigation_js_routes_placeholder_and_empty():
    js = _read('irrigation.js')
    assert "_t('nav.selectField'" in js, "irrigation.js: field placeholder not routed through _t"
    assert "_t('irrigation.emptyPrompt'" in js
    assert 'Seleccione un campo' not in js
    assert 'para consultar el riego' not in js


def test_irrigation_keys_bilingual():
    _assert_bilingual('irrigation.weeklyTitle', en_must_be='Weekly Irrigation Schedule')
    _assert_bilingual('irrigation.recommendation', en_must_be='Recommendation', es_must_be='Recomendacion')


# ── /intervenciones ────────────────────────────────────────────────────────────

def test_interventions_subtitle_wired():
    html = _read('intervenciones.html')
    assert _has_attr(html, 'interventions.subtitle'), \
        "intervenciones.html: subtitle (Tratamientos...) not wired"
    _assert_bilingual('interventions.subtitle')
    assert 'Treatments ranked' in (_en_value('interventions.subtitle') or '')


# ── /trayectoria ───────────────────────────────────────────────────────────────

def test_trajectory_empty_wired():
    html = _read('trayectoria.html')
    assert _has_attr(html, 'traj.emptyPrompt')
    _assert_bilingual('traj.emptyPrompt')
    assert (_en_value('traj.emptyPrompt') or '').startswith('Select a farm and field')


# ── /calendario ────────────────────────────────────────────────────────────────

def test_calendario_legend_wired():
    html = _read('calendario.html')
    for key in ('cal.stage.siembra', 'cal.stage.vegetativo', 'cal.stage.floracion',
                'cal.stage.fructificacion', 'cal.stage.cosecha'):
        assert _has_attr(html, key), f"calendario.html: legend missing data-i18n='{key}'"


def test_calendario_keys_bilingual():
    _assert_bilingual('cal.stage.cosecha', en_must_be='Harvest', es_must_be='Cosecha')
    _assert_bilingual('cal.stage.siembra', en_must_be='Sowing', es_must_be='Siembra')


# ── /impacto-economico ─────────────────────────────────────────────────────────

def test_economic_confidence_localized_in_js():
    js = _read('economic-impact.js')
    assert 'econ.confEstimated' in js, "economic-impact.js: confidence label not routed through i18n key"
    # The default literal 'Estimado' assigned straight to textContent is gone.
    assert 'const label = data.confidence_label || "Estimado";' not in js


def test_economic_html_badges_and_heading_wired():
    html = _read('economic-impact.html')
    assert _has_attr(html, 'econ.confEstimated'), "economic-impact.html: estimate badge not wired"
    assert _has_attr(html, 'econ.scenarioTitle'), "economic-impact.html: 'Con cultivOS' heading not wired"


def test_economic_keys_bilingual():
    _assert_bilingual('econ.confEstimated', en_must_be='Estimated', es_must_be='Estimado')
    _assert_bilingual('econ.confMeasured', en_must_be='Measured')
    assert 'With cultivOS' in (_en_value('econ.scenarioTitle') or '')


def test_economic_chart_dataset_label_is_english():
    # Task: the Chart.js dataset label must read "With cultivOS", not Spanish.
    js = _read('economic-impact.js')
    assert 'With cultivOS' in js
    assert "label: 'Con cultivOS'" not in js


# ── /campo direct-load graceful fallback ───────────────────────────────────────

def test_campo_no_raw_error_heading():
    js = _read('field.js')
    # The raw "Error:" heading path must be replaced by auto-select / friendly msg.
    assert "t('field.errorMissingParams')" not in js, \
        "field.js: still shows raw error heading on missing params"
    assert "window.location.replace(`/campo?farm=" in js, \
        "field.js: missing auto-select redirect for param-less load"
    assert "field.noPlotTitle" in js and "field.noPlotLink" in js


def test_campo_fallback_keys_bilingual():
    _assert_bilingual('field.noPlotTitle')
    _assert_bilingual('field.noPlotLink')
    assert (_en_value('field.noPlotLink') or '') == 'View my crops'


# ── i18n.js integrity ──────────────────────────────────────────────────────────

def test_no_new_key_left_in_only_one_block():
    content = _i18n()
    es, en = _es_block(content), _en_block(content)
    for key in ('cal.stage.cosecha', 'regional.distribCrops', 'econ.confEstimated',
                'status.statFarms', 'pf.intel.t', 'irrigation.emptyPrompt',
                'traj.emptyPrompt', 'dis.cropOptional', 'interventions.subtitle',
                'field.noPlotTitle'):
        assert _key_value(es, key) is not None, f"ES dict missing '{key}'"
        assert _key_value(en, key) is not None, f"EN dict missing '{key}'"
