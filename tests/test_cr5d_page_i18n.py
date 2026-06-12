"""
CR5d — Wire 8 pages into i18n: page titles, subtitles, stat labels, section headings.
Source-inspection tests (no server). Pages: alertas-clima, alineacion-tek, completitud,
completitud-global, confianza-tratamientos, correlacion-ndvi, calendario, coop-evidencia.
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


# ── alertas-clima.html ────────────────────────────────────────────────────────

def test_alertas_clima_title_has_data_i18n():
    html = _html('alertas-clima.html')
    assert _has_attr(html, 'alertasClima.title'), \
        "alertas-clima.html: <h1> missing data-i18n='alertasClima.title'"


def test_alertas_clima_window_label_has_data_i18n():
    html = _html('alertas-clima.html')
    assert _has_attr(html, 'alertasClima.window'), \
        "alertas-clima.html: Ventana label missing data-i18n='alertasClima.window'"


def test_alertas_clima_chart_heading_has_data_i18n():
    html = _html('alertas-clima.html')
    assert _has_attr(html, 'alertasClima.byType'), \
        "alertas-clima.html: <h2> chart heading missing data-i18n='alertasClima.byType'"


def test_alertas_clima_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('alertasClima.title', 'alertasClima.window', 'alertasClima.byType'):
        assert _has_key_en(i18n, key), \
            f"i18n.js en block missing key '{key}'"


def test_alertas_clima_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('alertasClima.title', 'alertasClima.window', 'alertasClima.byType'):
        assert _has_key_es(i18n, key), \
            f"i18n.js es block missing key '{key}'"


# ── alineacion-tek.html ───────────────────────────────────────────────────────

def test_tek_align_title_has_data_i18n():
    html = _html('alineacion-tek.html')
    assert _has_attr(html, 'tekAlign.title'), \
        "alineacion-tek.html: <h1> missing data-i18n='tekAlign.title'"


def test_tek_align_month_label_has_data_i18n():
    html = _html('alineacion-tek.html')
    assert _has_attr(html, 'tekAlign.month'), \
        "alineacion-tek.html: Mes label missing data-i18n='tekAlign.month'"


def test_tek_align_score_label_has_data_i18n():
    html = _html('alineacion-tek.html')
    assert _has_attr(html, 'tekAlign.scoreLabel'), \
        "alineacion-tek.html: Alineacion % label missing data-i18n='tekAlign.scoreLabel'"


def test_tek_align_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('tekAlign.title', 'tekAlign.month', 'tekAlign.scoreLabel'):
        assert _has_key_en(i18n, key), \
            f"i18n.js en block missing key '{key}'"


# ── lbl.* shared labels ────────────────────────────────────────────────────────

def test_lbl_farm_in_alertas_clima():
    html = _html('alertas-clima.html')
    assert _has_attr(html, 'lbl.farm'), \
        "alertas-clima.html: Finca label missing data-i18n='lbl.farm'"


def test_lbl_field_in_alertas_clima():
    html = _html('alertas-clima.html')
    assert _has_attr(html, 'lbl.field'), \
        "alertas-clima.html: Campo label missing data-i18n='lbl.field'"


def test_lbl_farm_in_alineacion_tek():
    html = _html('alineacion-tek.html')
    assert _has_attr(html, 'lbl.farm'), \
        "alineacion-tek.html: Finca label missing data-i18n='lbl.farm'"


def test_lbl_field_in_alineacion_tek():
    html = _html('alineacion-tek.html')
    assert _has_attr(html, 'lbl.field'), \
        "alineacion-tek.html: Campo label missing data-i18n='lbl.field'"


def test_lbl_farm_in_correlacion_ndvi():
    html = _html('correlacion-ndvi.html')
    assert _has_attr(html, 'lbl.farm'), \
        "correlacion-ndvi.html: Finca label missing data-i18n='lbl.farm'"


def test_lbl_field_in_correlacion_ndvi():
    html = _html('correlacion-ndvi.html')
    assert _has_attr(html, 'lbl.field'), \
        "correlacion-ndvi.html: Parcela label missing data-i18n='lbl.field'"


def test_lbl_cooperative_in_coop_evidencia():
    html = _html('coop-evidencia.html')
    assert _has_attr(html, 'lbl.cooperative'), \
        "coop-evidencia.html: Cooperativa label missing data-i18n='lbl.cooperative'"


def test_lbl_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('lbl.farm', 'lbl.field', 'lbl.cooperative'):
        assert _has_key_en(i18n, key), \
            f"i18n.js en block missing key '{key}'"


def test_lbl_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('lbl.farm', 'lbl.field', 'lbl.cooperative'):
        assert _has_key_es(i18n, key), \
            f"i18n.js es block missing key '{key}'"


# ── completitud.html ───────────────────────────────────────────────────────────

def test_completitud_title_has_data_i18n():
    html = _html('completitud.html')
    assert _has_attr(html, 'completitud.title'), \
        "completitud.html: <h1> missing data-i18n='completitud.title'"


def test_completitud_subtitle_has_data_i18n():
    html = _html('completitud.html')
    assert _has_attr(html, 'completitud.subtitle'), \
        "completitud.html: subtitle missing data-i18n='completitud.subtitle'"


def test_completitud_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('completitud.title', 'completitud.subtitle'):
        assert _has_key_en(i18n, key), \
            f"i18n.js en block missing key '{key}'"


def test_completitud_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('completitud.title', 'completitud.subtitle'):
        assert _has_key_es(i18n, key), \
            f"i18n.js es block missing key '{key}'"


# ── completitud-global.html ────────────────────────────────────────────────────

def test_completitud_global_title_has_data_i18n():
    html = _html('completitud-global.html')
    assert _has_attr(html, 'completitudGlobal.title'), \
        "completitud-global.html: <h1> missing data-i18n='completitudGlobal.title'"


def test_completitud_global_subtitle_has_data_i18n():
    html = _html('completitud-global.html')
    assert _has_attr(html, 'completitudGlobal.subtitle'), \
        "completitud-global.html: subtitle missing data-i18n='completitudGlobal.subtitle'"


def test_completitud_global_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('completitudGlobal.title', 'completitudGlobal.subtitle'):
        assert _has_key_en(i18n, key), \
            f"i18n.js en block missing key '{key}'"


# ── confianza-tratamientos.html ────────────────────────────────────────────────

def test_confianza_title_has_data_i18n():
    html = _html('confianza-tratamientos.html')
    assert _has_attr(html, 'confianza.title'), \
        "confianza-tratamientos.html: <h1> missing data-i18n='confianza.title'"


def test_confianza_subtitle_has_data_i18n():
    html = _html('confianza-tratamientos.html')
    assert _has_attr(html, 'confianza.subtitle'), \
        "confianza-tratamientos.html: subtitle missing data-i18n='confianza.subtitle'"


def test_confianza_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('confianza.title', 'confianza.subtitle'):
        assert _has_key_en(i18n, key), \
            f"i18n.js en block missing key '{key}'"


# ── correlacion-ndvi.html ──────────────────────────────────────────────────────

def test_correlacion_ndvi_title_has_data_i18n():
    html = _html('correlacion-ndvi.html')
    assert _has_attr(html, 'correlacionNdvi.title'), \
        "correlacion-ndvi.html: <h1> missing data-i18n='correlacionNdvi.title'"


def test_correlacion_ndvi_keys_in_i18n_en():
    i18n = _i18n()
    assert _has_key_en(i18n, 'correlacionNdvi.title'), \
        "i18n.js en block missing key 'correlacionNdvi.title'"


def test_correlacion_ndvi_keys_in_i18n_es():
    i18n = _i18n()
    assert _has_key_es(i18n, 'correlacionNdvi.title'), \
        "i18n.js es block missing key 'correlacionNdvi.title'"


# ── calendario.html ────────────────────────────────────────────────────────────

def test_calendario_title_has_data_i18n():
    html = _html('calendario.html')
    assert _has_attr(html, 'calendario.title'), \
        "calendario.html: <h1> missing data-i18n='calendario.title'"


def test_calendario_subtitle_has_data_i18n():
    html = _html('calendario.html')
    assert _has_attr(html, 'calendario.subtitle'), \
        "calendario.html: subtitle missing data-i18n='calendario.subtitle'"


def test_calendario_stat_crops_has_data_i18n():
    html = _html('calendario.html')
    assert _has_attr(html, 'calendario.statCrops'), \
        "calendario.html: 'Cultivos' stat label missing data-i18n='calendario.statCrops'"


def test_calendario_stat_days_has_data_i18n():
    html = _html('calendario.html')
    assert _has_attr(html, 'calendario.statDays'), \
        "calendario.html: 'Dias Max Ciclo' stat label missing data-i18n='calendario.statDays'"


def test_calendario_stat_stage_has_data_i18n():
    html = _html('calendario.html')
    assert _has_attr(html, 'calendario.statStage'), \
        "calendario.html: 'Etapa Actual' stat label missing data-i18n='calendario.statStage'"


def test_calendario_field_status_has_data_i18n():
    html = _html('calendario.html')
    assert _has_attr(html, 'calendario.fieldStatus'), \
        "calendario.html: 'Estado del Campo' h3 missing data-i18n='calendario.fieldStatus'"


def test_calendario_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('calendario.title', 'calendario.subtitle', 'calendario.statCrops',
                'calendario.statDays', 'calendario.statStage', 'calendario.fieldStatus'):
        assert _has_key_en(i18n, key), \
            f"i18n.js en block missing key '{key}'"


def test_calendario_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('calendario.title', 'calendario.subtitle', 'calendario.statCrops',
                'calendario.statDays', 'calendario.statStage', 'calendario.fieldStatus'):
        assert _has_key_es(i18n, key), \
            f"i18n.js es block missing key '{key}'"


# ── coop-evidencia.html ────────────────────────────────────────────────────────

def test_coop_evidencia_title_has_data_i18n():
    html = _html('coop-evidencia.html')
    assert _has_attr(html, 'coopEvidencia.title'), \
        "coop-evidencia.html: <h1> missing data-i18n='coopEvidencia.title'"


def test_coop_evidencia_strength_has_data_i18n():
    html = _html('coop-evidencia.html')
    assert _has_attr(html, 'coopEvidencia.strength'), \
        "coop-evidencia.html: 'Fortaleza principal' h3 missing data-i18n='coopEvidencia.strength'"


def test_coop_evidencia_weakness_has_data_i18n():
    html = _html('coop-evidencia.html')
    assert _has_attr(html, 'coopEvidencia.weakness'), \
        "coop-evidencia.html: 'Debilidad principal' h3 missing data-i18n='coopEvidencia.weakness'"


def test_coop_evidencia_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('coopEvidencia.title', 'coopEvidencia.strength', 'coopEvidencia.weakness'):
        assert _has_key_en(i18n, key), \
            f"i18n.js en block missing key '{key}'"


def test_coop_evidencia_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('coopEvidencia.title', 'coopEvidencia.strength', 'coopEvidencia.weakness'):
        assert _has_key_es(i18n, key), \
            f"i18n.js es block missing key '{key}'"
