"""
CR5e — Wire 8 pages into i18n: page titles, subtitles, stat labels, table headers, buttons.
Source-inspection tests (no server). Pages: trayectoria, timeline, tek, fusion,
thermal-dashboard, seasonal, demo, walkthrough.
"""

import os

FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')
I18N_JS = os.path.join(FRONTEND, 'i18n.js')


def _html(name: str) -> str:
    with open(os.path.join(FRONTEND, name), 'r', encoding='utf-8') as f:
        return f.read()


def _i18n() -> str:
    with open(I18N_JS, 'r', encoding='utf-8') as f:
        return f.read()


def _has_attr(html: str, key: str) -> bool:
    return f'data-i18n="{key}"' in html or f"data-i18n='{key}'" in html


def _has_key_en(content: str, key: str) -> bool:
    en_idx = content.find("en: {")
    if en_idx == -1:
        en_idx = content.find('en:{')
    if en_idx == -1:
        return False
    en_block = content[en_idx:]
    return f"'{key}'" in en_block or f'"{key}"' in en_block


def _has_key_es(content: str, key: str) -> bool:
    es_idx = content.find("es: {")
    if es_idx == -1:
        es_idx = content.find('es:{')
    if es_idx == -1:
        return False
    en_idx = content.find("en: {")
    es_block = content[es_idx:en_idx] if en_idx != -1 else content[es_idx:]
    return f"'{key}'" in es_block or f'"{key}"' in es_block


# ── trayectoria.html ──────────────────────────────────────────────────────────

def test_trayectoria_title_has_data_i18n():
    html = _html('trayectoria.html')
    assert _has_attr(html, 'trayectoria.title'), \
        "trayectoria.html: <h1> missing data-i18n='trayectoria.title'"


def test_trayectoria_subtitle_has_data_i18n():
    html = _html('trayectoria.html')
    assert _has_attr(html, 'trayectoria.subtitle'), \
        "trayectoria.html: subtitle <p> missing data-i18n='trayectoria.subtitle'"


def test_trayectoria_analyze_btn_has_data_i18n():
    html = _html('trayectoria.html')
    assert _has_attr(html, 'trayectoria.analyzeBtn'), \
        "trayectoria.html: Analizar button missing data-i18n='trayectoria.analyzeBtn'"


def test_trayectoria_stat_labels_have_data_i18n():
    html = _html('trayectoria.html')
    for key in ('trayectoria.statCurrent', 'trayectoria.statTrend',
                 'trayectoria.statProjection', 'trayectoria.statRange'):
        assert _has_attr(html, key), \
            f"trayectoria.html: stat label missing data-i18n='{key}'"


def test_trayectoria_chart_headings_have_data_i18n():
    html = _html('trayectoria.html')
    for key in ('trayectoria.chartTimeline', 'trayectoria.chartProjection',
                 'trayectoria.chartRange', 'trayectoria.chartCorrelation'):
        assert _has_attr(html, key), \
            f"trayectoria.html: chart <h2> missing data-i18n='{key}'"


def test_trayectoria_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('trayectoria.title', 'trayectoria.subtitle', 'trayectoria.analyzeBtn',
                 'trayectoria.statCurrent', 'trayectoria.statTrend',
                 'trayectoria.statProjection', 'trayectoria.statRange',
                 'trayectoria.chartTimeline', 'trayectoria.chartProjection',
                 'trayectoria.chartRange', 'trayectoria.chartCorrelation'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_trayectoria_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('trayectoria.title', 'trayectoria.subtitle', 'trayectoria.analyzeBtn',
                 'trayectoria.statCurrent', 'trayectoria.statTrend',
                 'trayectoria.statProjection', 'trayectoria.statRange',
                 'trayectoria.chartTimeline', 'trayectoria.chartProjection',
                 'trayectoria.chartRange', 'trayectoria.chartCorrelation'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── timeline.html (Historial de Salud) ───────────────────────────────────────

def test_timeline_title_has_data_i18n():
    html = _html('timeline.html')
    assert _has_attr(html, 'timelineHist.title'), \
        "timeline.html: <h1> missing data-i18n='timelineHist.title'"


def test_timeline_subtitle_has_data_i18n():
    html = _html('timeline.html')
    assert _has_attr(html, 'timelineHist.subtitle'), \
        "timeline.html: subtitle <p> missing data-i18n='timelineHist.subtitle'"


def test_timeline_update_btn_has_data_i18n():
    html = _html('timeline.html')
    assert _has_attr(html, 'timelineHist.updateBtn'), \
        "timeline.html: Actualizar button missing data-i18n='timelineHist.updateBtn'"


def test_timeline_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('timelineHist.title', 'timelineHist.subtitle', 'timelineHist.updateBtn'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_timeline_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('timelineHist.title', 'timelineHist.subtitle', 'timelineHist.updateBtn'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── tek.html (Inteligencia Ancestral — Validacion) ────────────────────────────

def test_tek_title_has_data_i18n():
    html = _html('tek.html')
    assert _has_attr(html, 'tekVal.title'), \
        "tek.html: <h1> missing data-i18n='tekVal.title'"


def test_tek_subtitle_has_data_i18n():
    html = _html('tek.html')
    assert _has_attr(html, 'tekVal.subtitle'), \
        "tek.html: subtitle <p> missing data-i18n='tekVal.subtitle'"


def test_tek_query_btn_has_data_i18n():
    html = _html('tek.html')
    assert _has_attr(html, 'tekVal.queryBtn'), \
        "tek.html: Consultar Metodos button missing data-i18n='tekVal.queryBtn'"


def test_tek_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('tekVal.title', 'tekVal.subtitle', 'tekVal.queryBtn'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_tek_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('tekVal.title', 'tekVal.subtitle', 'tekVal.queryBtn'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── fusion.html (Validacion de Fusion de Sensores) ────────────────────────────

def test_fusion_title_has_data_i18n():
    html = _html('fusion.html')
    assert _has_attr(html, 'fusionVal.title'), \
        "fusion.html: <h1> missing data-i18n='fusionVal.title'"


def test_fusion_subtitle_has_data_i18n():
    html = _html('fusion.html')
    assert _has_attr(html, 'fusionVal.subtitle'), \
        "fusion.html: subtitle <p> missing data-i18n='fusionVal.subtitle'"


def test_fusion_analyze_btn_has_data_i18n():
    html = _html('fusion.html')
    assert _has_attr(html, 'fusionVal.analyzeBtn'), \
        "fusion.html: Analizar Sensores button missing data-i18n='fusionVal.analyzeBtn'"


def test_fusion_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('fusionVal.title', 'fusionVal.subtitle', 'fusionVal.analyzeBtn'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_fusion_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('fusionVal.title', 'fusionVal.subtitle', 'fusionVal.analyzeBtn'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── thermal-dashboard.html (Estres Termico) ───────────────────────────────────

def test_thermal_title_has_data_i18n():
    html = _html('thermal-dashboard.html')
    assert _has_attr(html, 'thermalDash.title'), \
        "thermal-dashboard.html: <h1> missing data-i18n='thermalDash.title'"


def test_thermal_subtitle_has_data_i18n():
    html = _html('thermal-dashboard.html')
    assert _has_attr(html, 'thermalDash.subtitle'), \
        "thermal-dashboard.html: subtitle missing data-i18n='thermalDash.subtitle'"


def test_thermal_update_btn_has_data_i18n():
    html = _html('thermal-dashboard.html')
    assert _has_attr(html, 'thermalDash.updateBtn'), \
        "thermal-dashboard.html: Actualizar button missing data-i18n='thermalDash.updateBtn'"


def test_thermal_table_headers_have_data_i18n():
    html = _html('thermal-dashboard.html')
    for key in ('thermalDash.colDate', 'thermalDash.colAvgTemp', 'thermalDash.colMinTemp',
                 'thermalDash.colMaxTemp', 'thermalDash.colStdDev', 'thermalDash.colStress',
                 'thermalDash.colPixels', 'thermalDash.colIrrDef'):
        assert _has_attr(html, key), \
            f"thermal-dashboard.html: table <th> missing data-i18n='{key}'"


def test_thermal_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('thermalDash.title', 'thermalDash.subtitle', 'thermalDash.updateBtn',
                 'thermalDash.colDate', 'thermalDash.colAvgTemp', 'thermalDash.colMinTemp',
                 'thermalDash.colMaxTemp', 'thermalDash.colStdDev', 'thermalDash.colStress',
                 'thermalDash.colPixels', 'thermalDash.colIrrDef'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_thermal_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('thermalDash.title', 'thermalDash.subtitle', 'thermalDash.updateBtn',
                 'thermalDash.colDate', 'thermalDash.colAvgTemp', 'thermalDash.colMinTemp',
                 'thermalDash.colMaxTemp', 'thermalDash.colStdDev', 'thermalDash.colStress',
                 'thermalDash.colPixels', 'thermalDash.colIrrDef'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── seasonal.html (Comparacion Estacional) ────────────────────────────────────

def test_seasonal_cmp_title_has_data_i18n():
    html = _html('seasonal.html')
    assert _has_attr(html, 'seasonalCmp.title'), \
        "seasonal.html: <h1> missing data-i18n='seasonalCmp.title'"


def test_seasonal_cmp_subtitle_has_data_i18n():
    html = _html('seasonal.html')
    assert _has_attr(html, 'seasonalCmp.subtitle'), \
        "seasonal.html: subtitle missing data-i18n='seasonalCmp.subtitle'"


def test_seasonal_cmp_compare_btn_has_data_i18n():
    html = _html('seasonal.html')
    assert _has_attr(html, 'seasonalCmp.compareBtn'), \
        "seasonal.html: Comparar button missing data-i18n='seasonalCmp.compareBtn'"


def test_seasonal_cmp_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('seasonalCmp.title', 'seasonalCmp.subtitle', 'seasonalCmp.compareBtn'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_seasonal_cmp_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('seasonalCmp.title', 'seasonalCmp.subtitle', 'seasonalCmp.compareBtn'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── demo.html (Marketing Demo Page) ──────────────────────────────────────────

def test_demo_page_hero_sub_has_data_i18n():
    html = _html('demo.html')
    assert _has_attr(html, 'demoPage.heroSub'), \
        "demo.html: hero-sub missing data-i18n='demoPage.heroSub'"


def test_demo_page_hero_tagline_has_data_i18n():
    html = _html('demo.html')
    assert _has_attr(html, 'demoPage.heroTagline'), \
        "demo.html: hero-tagline missing data-i18n='demoPage.heroTagline'"


def test_demo_page_stat_labels_have_data_i18n():
    html = _html('demo.html')
    for key in ('demoPage.statTests', 'demoPage.statEndpoints',
                 'demoPage.statFarms', 'demoPage.statMethods'):
        assert _has_attr(html, key), \
            f"demo.html: stat label missing data-i18n='{key}'"


def test_demo_page_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('demoPage.heroSub', 'demoPage.heroTagline',
                 'demoPage.statTests', 'demoPage.statEndpoints',
                 'demoPage.statFarms', 'demoPage.statMethods'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_demo_page_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('demoPage.heroSub', 'demoPage.heroTagline',
                 'demoPage.statTests', 'demoPage.statEndpoints',
                 'demoPage.statFarms', 'demoPage.statMethods'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── walkthrough.html (Recorrido FODECIJAL) ────────────────────────────────────

def test_walkthrough_start_btn_has_data_i18n():
    html = _html('walkthrough.html')
    assert _has_attr(html, 'walkthru.startBtn'), \
        "walkthrough.html: 'Iniciar Tour Guiado' button missing data-i18n='walkthru.startBtn'"


def test_walkthrough_prev_btn_has_data_i18n():
    html = _html('walkthrough.html')
    assert _has_attr(html, 'walkthru.prevBtn'), \
        "walkthrough.html: 'Anterior' button missing data-i18n='walkthru.prevBtn'"


def test_walkthrough_next_btn_has_data_i18n():
    html = _html('walkthrough.html')
    assert _has_attr(html, 'walkthru.nextBtn'), \
        "walkthrough.html: 'Siguiente' button missing data-i18n='walkthru.nextBtn'"


def test_walkthrough_explore_farms_has_data_i18n():
    html = _html('walkthrough.html')
    assert _has_attr(html, 'walkthru.exploreFarmsBtn'), \
        "walkthrough.html: 'Explorar el Panel de Granjas' link missing data-i18n='walkthru.exploreFarmsBtn'"


def test_walkthrough_intel_btn_has_data_i18n():
    html = _html('walkthrough.html')
    assert _has_attr(html, 'walkthru.intelBtn'), \
        "walkthrough.html: 'Panel de Inteligencia' link missing data-i18n='walkthru.intelBtn'"


def test_walkthrough_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('walkthru.startBtn', 'walkthru.prevBtn', 'walkthru.nextBtn',
                 'walkthru.exploreFarmsBtn', 'walkthru.intelBtn'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_walkthrough_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('walkthru.startBtn', 'walkthru.prevBtn', 'walkthru.nextBtn',
                 'walkthru.exploreFarmsBtn', 'walkthru.intelBtn'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"
