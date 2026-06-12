"""
CR5f — Wire 8 pages into i18n: page titles, subtitles, stat labels, table headers, buttons.
Source-inspection tests (no server). Pages: calendario-campo, cerebro-analytics, comparar,
coop-progreso-mensual, diversidad-cultivos, economic-impact, efectividad-global,
efectividad-intervenciones.
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


# ── calendario-campo.html ─────────────────────────────────────────────────────

def test_calCampo_title_has_data_i18n():
    html = _html('calendario-campo.html')
    assert _has_attr(html, 'calCampo.title'), \
        "calendario-campo.html: <h1> missing data-i18n='calCampo.title'"


def test_calCampo_label_farm_has_data_i18n():
    html = _html('calendario-campo.html')
    assert _has_attr(html, 'calCampo.labelFarm'), \
        "calendario-campo.html: Finca label missing data-i18n='calCampo.labelFarm'"


def test_calCampo_kpi_total_has_data_i18n():
    html = _html('calendario-campo.html')
    assert _has_attr(html, 'calCampo.kpiTotal'), \
        "calendario-campo.html: 'Total de eventos' KPI missing data-i18n='calCampo.kpiTotal'"


def test_calCampo_kpi_busiest_has_data_i18n():
    html = _html('calendario-campo.html')
    assert _has_attr(html, 'calCampo.kpiBusiest'), \
        "calendario-campo.html: 'Mes más activo' KPI missing data-i18n='calCampo.kpiBusiest'"


def test_calCampo_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('calCampo.title', 'calCampo.labelFarm', 'calCampo.kpiTotal', 'calCampo.kpiBusiest'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_calCampo_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('calCampo.title', 'calCampo.labelFarm', 'calCampo.kpiTotal', 'calCampo.kpiBusiest'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── cerebro-analytics.html ────────────────────────────────────────────────────

def test_cerebro_title_has_data_i18n():
    html = _html('cerebro-analytics.html')
    assert _has_attr(html, 'cerebro.title'), \
        "cerebro-analytics.html: <h1> missing data-i18n='cerebro.title'"


def test_cerebro_subtitle_has_data_i18n():
    html = _html('cerebro-analytics.html')
    assert _has_attr(html, 'cerebro.subtitle'), \
        "cerebro-analytics.html: subtitle <p> missing data-i18n='cerebro.subtitle'"


def test_cerebro_stat_labels_have_data_i18n():
    html = _html('cerebro-analytics.html')
    for key in ('cerebro.statTotal', 'cerebro.statRecommendations',
                 'cerebro.statAnalyses', 'cerebro.statFarms', 'cerebro.statAccuracy'):
        assert _has_attr(html, key), \
            f"cerebro-analytics.html: stat label missing data-i18n='{key}'"


def test_cerebro_chart_headings_have_data_i18n():
    html = _html('cerebro-analytics.html')
    for key in ('cerebro.chartDecisions', 'cerebro.chartByType', 'cerebro.chartAccuracy'):
        assert _has_attr(html, key), \
            f"cerebro-analytics.html: chart heading missing data-i18n='{key}'"


def test_cerebro_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('cerebro.title', 'cerebro.subtitle', 'cerebro.statTotal',
                 'cerebro.statRecommendations', 'cerebro.statAnalyses',
                 'cerebro.statFarms', 'cerebro.statAccuracy',
                 'cerebro.chartDecisions', 'cerebro.chartByType', 'cerebro.chartAccuracy'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_cerebro_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('cerebro.title', 'cerebro.subtitle', 'cerebro.statTotal',
                 'cerebro.statRecommendations', 'cerebro.statAnalyses',
                 'cerebro.statFarms', 'cerebro.statAccuracy',
                 'cerebro.chartDecisions', 'cerebro.chartByType', 'cerebro.chartAccuracy'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── comparar.html (Compare Farms) ─────────────────────────────────────────────

def test_compareF_title_has_data_i18n():
    html = _html('comparar.html')
    assert _has_attr(html, 'compareF.title'), \
        "comparar.html: <h1> missing data-i18n='compareF.title'"


def test_compareF_subtitle_has_data_i18n():
    html = _html('comparar.html')
    assert _has_attr(html, 'compareF.subtitle'), \
        "comparar.html: subtitle <p> missing data-i18n='compareF.subtitle'"


def test_compareF_compare_btn_has_data_i18n():
    html = _html('comparar.html')
    assert _has_attr(html, 'compareF.compareBtn'), \
        "comparar.html: Compare button missing data-i18n='compareF.compareBtn'"


def test_compareF_chart_headings_have_data_i18n():
    html = _html('comparar.html')
    for key in ('compareF.headingSummary', 'compareF.headingHealth',
                 'compareF.headingYield', 'compareF.headingHistory'):
        assert _has_attr(html, key), \
            f"comparar.html: heading missing data-i18n='{key}'"


def test_compareF_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('compareF.title', 'compareF.subtitle', 'compareF.compareBtn',
                 'compareF.headingSummary', 'compareF.headingHealth',
                 'compareF.headingYield', 'compareF.headingHistory'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_compareF_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('compareF.title', 'compareF.subtitle', 'compareF.compareBtn',
                 'compareF.headingSummary', 'compareF.headingHealth',
                 'compareF.headingYield', 'compareF.headingHistory'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── coop-progreso-mensual.html ────────────────────────────────────────────────

def test_coopProg_title_has_data_i18n():
    html = _html('coop-progreso-mensual.html')
    assert _has_attr(html, 'coopProg.title'), \
        "coop-progreso-mensual.html: <h1> missing data-i18n='coopProg.title'"


def test_coopProg_subtitle_has_data_i18n():
    html = _html('coop-progreso-mensual.html')
    assert _has_attr(html, 'coopProg.subtitle'), \
        "coop-progreso-mensual.html: subtitle <p> missing data-i18n='coopProg.subtitle'"


def test_coopProg_table_headers_have_data_i18n():
    html = _html('coop-progreso-mensual.html')
    for key in ('coopProg.colMonth', 'coopProg.colHealth',
                 'coopProg.colRegen', 'coopProg.colMoM', 'coopProg.colTreatments'):
        assert _has_attr(html, key), \
            f"coop-progreso-mensual.html: table <th> missing data-i18n='{key}'"


def test_coopProg_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('coopProg.title', 'coopProg.subtitle',
                 'coopProg.colMonth', 'coopProg.colHealth',
                 'coopProg.colRegen', 'coopProg.colMoM', 'coopProg.colTreatments'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_coopProg_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('coopProg.title', 'coopProg.subtitle',
                 'coopProg.colMonth', 'coopProg.colHealth',
                 'coopProg.colRegen', 'coopProg.colMoM', 'coopProg.colTreatments'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── diversidad-cultivos.html ──────────────────────────────────────────────────

def test_cropDiv_title_has_data_i18n():
    html = _html('diversidad-cultivos.html')
    assert _has_attr(html, 'cropDiv.title'), \
        "diversidad-cultivos.html: <h1> missing data-i18n='cropDiv.title'"


def test_cropDiv_subtitle_has_data_i18n():
    html = _html('diversidad-cultivos.html')
    assert _has_attr(html, 'cropDiv.subtitle'), \
        "diversidad-cultivos.html: subtitle <p> missing data-i18n='cropDiv.subtitle'"


def test_cropDiv_kpi_shannon_has_data_i18n():
    html = _html('diversidad-cultivos.html')
    assert _has_attr(html, 'cropDiv.kpiShannon'), \
        "diversidad-cultivos.html: Shannon KPI label missing data-i18n='cropDiv.kpiShannon'"


def test_cropDiv_table_headers_have_data_i18n():
    html = _html('diversidad-cultivos.html')
    for key in ('cropDiv.colFarm', 'cropDiv.colDistinct', 'cropDiv.colTypes'):
        assert _has_attr(html, key), \
            f"diversidad-cultivos.html: table <th> missing data-i18n='{key}'"


def test_cropDiv_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('cropDiv.title', 'cropDiv.subtitle', 'cropDiv.kpiShannon',
                 'cropDiv.colFarm', 'cropDiv.colDistinct', 'cropDiv.colTypes'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_cropDiv_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('cropDiv.title', 'cropDiv.subtitle', 'cropDiv.kpiShannon',
                 'cropDiv.colFarm', 'cropDiv.colDistinct', 'cropDiv.colTypes'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── economic-impact.html ──────────────────────────────────────────────────────

def test_econImpact_title_has_data_i18n():
    html = _html('economic-impact.html')
    assert _has_attr(html, 'econImpact.title'), \
        "economic-impact.html: <h1> missing data-i18n='econImpact.title'"


def test_econImpact_subtitle_has_data_i18n():
    html = _html('economic-impact.html')
    assert _has_attr(html, 'econImpact.subtitle'), \
        "economic-impact.html: subtitle <p> missing data-i18n='econImpact.subtitle'"


def test_econImpact_refresh_btn_has_data_i18n():
    html = _html('economic-impact.html')
    assert _has_attr(html, 'econImpact.refreshBtn'), \
        "economic-impact.html: Refresh button missing data-i18n='econImpact.refreshBtn'"


def test_econImpact_stat_labels_have_data_i18n():
    html = _html('economic-impact.html')
    for key in ('econImpact.statTotal', 'econImpact.statHectares',
                 'econImpact.statWater', 'econImpact.statFertilizer', 'econImpact.statYield'):
        assert _has_attr(html, key), \
            f"economic-impact.html: stat label missing data-i18n='{key}'"


def test_econImpact_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('econImpact.title', 'econImpact.subtitle', 'econImpact.refreshBtn',
                 'econImpact.statTotal', 'econImpact.statHectares',
                 'econImpact.statWater', 'econImpact.statFertilizer', 'econImpact.statYield'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_econImpact_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('econImpact.title', 'econImpact.subtitle', 'econImpact.refreshBtn',
                 'econImpact.statTotal', 'econImpact.statHectares',
                 'econImpact.statWater', 'econImpact.statFertilizer', 'econImpact.statYield'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── efectividad-global.html ───────────────────────────────────────────────────

def test_effGlobal_title_has_data_i18n():
    html = _html('efectividad-global.html')
    assert _has_attr(html, 'effGlobal.title'), \
        "efectividad-global.html: <h1> missing data-i18n='effGlobal.title'"


def test_effGlobal_subtitle_has_data_i18n():
    html = _html('efectividad-global.html')
    assert _has_attr(html, 'effGlobal.subtitle'), \
        "efectividad-global.html: subtitle <p> missing data-i18n='effGlobal.subtitle'"


def test_effGlobal_stat_labels_have_data_i18n():
    html = _html('efectividad-global.html')
    for key in ('effGlobal.statTreatments', 'effGlobal.statApplications',
                 'effGlobal.statDelta', 'effGlobal.statBest'):
        assert _has_attr(html, key), \
            f"efectividad-global.html: stat label missing data-i18n='{key}'"


def test_effGlobal_chart_title_has_data_i18n():
    html = _html('efectividad-global.html')
    assert _has_attr(html, 'effGlobal.chartTitle'), \
        "efectividad-global.html: chart <h2> missing data-i18n='effGlobal.chartTitle'"


def test_effGlobal_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('effGlobal.title', 'effGlobal.subtitle',
                 'effGlobal.statTreatments', 'effGlobal.statApplications',
                 'effGlobal.statDelta', 'effGlobal.statBest', 'effGlobal.chartTitle'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_effGlobal_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('effGlobal.title', 'effGlobal.subtitle',
                 'effGlobal.statTreatments', 'effGlobal.statApplications',
                 'effGlobal.statDelta', 'effGlobal.statBest', 'effGlobal.chartTitle'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"


# ── efectividad-intervenciones.html ──────────────────────────────────────────

def test_effInterv_title_has_data_i18n():
    html = _html('efectividad-intervenciones.html')
    assert _has_attr(html, 'effInterv.title'), \
        "efectividad-intervenciones.html: <h1> missing data-i18n='effInterv.title'"


def test_effInterv_subtitle_has_data_i18n():
    html = _html('efectividad-intervenciones.html')
    assert _has_attr(html, 'effInterv.subtitle'), \
        "efectividad-intervenciones.html: subtitle <p> missing data-i18n='effInterv.subtitle'"


def test_effInterv_kpi_labels_have_data_i18n():
    html = _html('efectividad-intervenciones.html')
    for key in ('effInterv.kpiRate', 'effInterv.kpiTreatments'):
        assert _has_attr(html, key), \
            f"efectividad-intervenciones.html: KPI label missing data-i18n='{key}'"


def test_effInterv_card_titles_have_data_i18n():
    html = _html('efectividad-intervenciones.html')
    for key in ('effInterv.cardBest', 'effInterv.cardWorst'):
        assert _has_attr(html, key), \
            f"efectividad-intervenciones.html: card <h3> missing data-i18n='{key}'"


def test_effInterv_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('effInterv.title', 'effInterv.subtitle',
                 'effInterv.kpiRate', 'effInterv.kpiTreatments',
                 'effInterv.cardBest', 'effInterv.cardWorst'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing key '{key}'"


def test_effInterv_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('effInterv.title', 'effInterv.subtitle',
                 'effInterv.kpiRate', 'effInterv.kpiTreatments',
                 'effInterv.cardBest', 'effInterv.cardWorst'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing key '{key}'"
