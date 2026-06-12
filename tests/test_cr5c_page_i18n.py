"""
CR5c — Wire 8 pages into i18n: page titles, subtitles, stat labels, section headings, buttons.
Source-inspection tests (no server). Pages: alert-config, alertas-estacionales,
benchmark-regional, calculadora-suelo, clima, disease, efectividad, intervenciones.
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


# ── alert-config.html ─────────────────────────────────────────────────────────

def test_alert_config_title_has_data_i18n():
    html = _html('alert-config.html')
    assert _has_attr(html, 'alert.title'), \
        "alert-config.html: <h1> missing data-i18n='alert.title'"


def test_alert_config_subtitle_has_data_i18n():
    html = _html('alert-config.html')
    assert _has_attr(html, 'alert.subtitle'), \
        "alert-config.html: subtitle missing data-i18n='alert.subtitle'"


def test_alert_config_threshold_sections_have_data_i18n():
    html = _html('alert-config.html')
    for key in ('alert.healthMin', 'alert.ndviMin', 'alert.tempMax'):
        assert _has_attr(html, key), \
            f"alert-config.html: section heading missing data-i18n='{key}'"


def test_alert_config_save_button_has_data_i18n():
    html = _html('alert-config.html')
    assert _has_attr(html, 'btn.save'), \
        "alert-config.html: save button missing data-i18n='btn.save'"


# ── alertas-estacionales.html ─────────────────────────────────────────────────

def test_alertas_estacionales_title_has_data_i18n():
    html = _html('alertas-estacionales.html')
    assert _has_attr(html, 'seasonal.title'), \
        "alertas-estacionales.html: <h1> missing data-i18n='seasonal.title'"


def test_alertas_estacionales_subtitle_has_data_i18n():
    html = _html('alertas-estacionales.html')
    assert _has_attr(html, 'seasonal.subtitle'), \
        "alertas-estacionales.html: subtitle missing data-i18n='seasonal.subtitle'"


def test_alertas_estacionales_empty_has_data_i18n():
    html = _html('alertas-estacionales.html')
    assert _has_attr(html, 'seasonal.empty'), \
        "alertas-estacionales.html: empty state missing data-i18n='seasonal.empty'"


# ── benchmark-regional.html ───────────────────────────────────────────────────

def test_benchmark_title_has_data_i18n():
    html = _html('benchmark-regional.html')
    assert _has_attr(html, 'benchmark.title'), \
        "benchmark-regional.html: <h1> missing data-i18n='benchmark.title'"


def test_benchmark_labels_have_data_i18n():
    html = _html('benchmark-regional.html')
    for key in ('benchmark.ownFarm', 'benchmark.regionalAvg', 'benchmark.noData'):
        assert _has_attr(html, key), \
            f"benchmark-regional.html: label missing data-i18n='{key}'"


# ── calculadora-suelo.html ────────────────────────────────────────────────────

def test_calculadora_title_has_data_i18n():
    html = _html('calculadora-suelo.html')
    assert _has_attr(html, 'calc.title'), \
        "calculadora-suelo.html: <h1> missing data-i18n='calc.title'"


def test_calculadora_subtitle_has_data_i18n():
    html = _html('calculadora-suelo.html')
    assert _has_attr(html, 'calc.subtitle'), \
        "calculadora-suelo.html: subtitle missing data-i18n='calc.subtitle'"


def test_calculadora_section_labels_have_data_i18n():
    html = _html('calculadora-suelo.html')
    for key in ('calc.currentLabel', 'calc.targetLabel'):
        assert _has_attr(html, key), \
            f"calculadora-suelo.html: section label missing data-i18n='{key}'"


def test_calculadora_button_has_data_i18n():
    html = _html('calculadora-suelo.html')
    assert _has_attr(html, 'btn.calculateAmendments'), \
        "calculadora-suelo.html: calc button missing data-i18n='btn.calculateAmendments'"


# ── clima.html ────────────────────────────────────────────────────────────────

def test_clima_title_has_data_i18n():
    html = _html('clima.html')
    assert _has_attr(html, 'climate.title'), \
        "clima.html: <h1> missing data-i18n='climate.title'"


def test_clima_subtitle_has_data_i18n():
    html = _html('clima.html')
    assert _has_attr(html, 'climate.subtitle'), \
        "clima.html: subtitle missing data-i18n='climate.subtitle'"


def test_clima_section_titles_have_data_i18n():
    html = _html('clima.html')
    for key in ('climate.forecastTitle', 'climate.historyTitle'):
        assert _has_attr(html, key), \
            f"clima.html: section title missing data-i18n='{key}'"


# ── disease.html ──────────────────────────────────────────────────────────────

def test_disease_title_has_data_i18n():
    html = _html('disease.html')
    assert _has_attr(html, 'disease.title'), \
        "disease.html: <h1> missing data-i18n='disease.title'"


def test_disease_subtitle_has_data_i18n():
    html = _html('disease.html')
    assert _has_attr(html, 'disease.subtitle'), \
        "disease.html: subtitle missing data-i18n='disease.subtitle'"


def test_disease_symptoms_section_has_data_i18n():
    html = _html('disease.html')
    assert _has_attr(html, 'disease.symptomsTitle'), \
        "disease.html: symptoms section title missing data-i18n='disease.symptomsTitle'"


def test_disease_buttons_have_data_i18n():
    html = _html('disease.html')
    for key in ('btn.assessRisk', 'disease.identifyButton'):
        assert _has_attr(html, key), \
            f"disease.html: button missing data-i18n='{key}'"


# ── efectividad.html ──────────────────────────────────────────────────────────

def test_efectividad_title_has_data_i18n():
    html = _html('efectividad.html')
    assert _has_attr(html, 'effectiveness.title'), \
        "efectividad.html: <h1> missing data-i18n='effectiveness.title'"


def test_efectividad_subtitle_has_data_i18n():
    html = _html('efectividad.html')
    assert _has_attr(html, 'effectiveness.subtitle'), \
        "efectividad.html: subtitle missing data-i18n='effectiveness.subtitle'"


def test_efectividad_load_button_has_data_i18n():
    html = _html('efectividad.html')
    assert _has_attr(html, 'effectiveness.loadButton'), \
        "efectividad.html: load button missing data-i18n='effectiveness.loadButton'"


# ── intervenciones.html ───────────────────────────────────────────────────────

def test_intervenciones_title_has_data_i18n():
    html = _html('intervenciones.html')
    assert _has_attr(html, 'interventions.title'), \
        "intervenciones.html: <h1> missing data-i18n='interventions.title'"


def test_intervenciones_empty_state_has_data_i18n():
    html = _html('intervenciones.html')
    assert _has_attr(html, 'interventions.empty'), \
        "intervenciones.html: empty state missing data-i18n='interventions.empty'"


def test_intervenciones_button_has_data_i18n():
    html = _html('intervenciones.html')
    assert _has_attr(html, 'btn.viewRanking'), \
        "intervenciones.html: view ranking button missing data-i18n='btn.viewRanking'"


# ── i18n.js EN key checks ─────────────────────────────────────────────────────

def test_i18n_has_alert_config_keys_en():
    content = _i18n()
    for key in ('alert.title', 'alert.subtitle', 'alert.healthMin',
                'alert.ndviMin', 'alert.tempMax', 'btn.save'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_seasonal_keys_en():
    content = _i18n()
    for key in ('seasonal.title', 'seasonal.subtitle', 'seasonal.empty'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_benchmark_keys_en():
    content = _i18n()
    for key in ('benchmark.title', 'benchmark.ownFarm',
                'benchmark.regionalAvg', 'benchmark.noData'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_calc_keys_en():
    content = _i18n()
    for key in ('calc.title', 'calc.subtitle', 'calc.currentLabel',
                'calc.targetLabel', 'btn.calculateAmendments'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_climate_keys_en():
    content = _i18n()
    for key in ('climate.title', 'climate.subtitle',
                'climate.forecastTitle', 'climate.historyTitle'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_disease_keys_en():
    content = _i18n()
    for key in ('disease.title', 'disease.subtitle', 'disease.symptomsTitle',
                'disease.identifyButton', 'btn.assessRisk'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_effectiveness_keys_en():
    content = _i18n()
    for key in ('effectiveness.title', 'effectiveness.subtitle',
                'effectiveness.loadButton'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_interventions_keys_en():
    content = _i18n()
    for key in ('interventions.title', 'interventions.empty', 'btn.viewRanking'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"
