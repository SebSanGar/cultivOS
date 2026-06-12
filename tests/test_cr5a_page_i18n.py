"""
CR5a — Wire 8 high-priority pages into i18n: page titles, subtitles, stat labels.
Source-inspection tests (no server). Pages: ejecutivo, resumen, status, carbon,
anomalies, actions, plataforma, demo-fodecijal.
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


# ── ejecutivo.html ────────────────────────────────────────────────────────────

def test_ejecutivo_title_has_data_i18n():
    html = _html('ejecutivo.html')
    assert _has_attr(html, 'exec.title'), \
        "ejecutivo.html: <h1> missing data-i18n='exec.title'"


def test_ejecutivo_subtitle_has_data_i18n():
    html = _html('ejecutivo.html')
    assert _has_attr(html, 'exec.subtitle'), \
        "ejecutivo.html: subtitle missing data-i18n='exec.subtitle'"


def test_ejecutivo_stat_labels_have_data_i18n():
    html = _html('ejecutivo.html')
    for key in ('stat.farms', 'stat.avgHealth', 'stat.treatments', 'stat.alerts'):
        assert _has_attr(html, key), \
            f"ejecutivo.html: stat label missing data-i18n='{key}'"


def test_ejecutivo_chart_titles_have_data_i18n():
    html = _html('ejecutivo.html')
    for key in ('exec.activity30', 'exec.farmsTable'):
        assert _has_attr(html, key), \
            f"ejecutivo.html: chart/table title missing data-i18n='{key}'"


# ── resumen.html ──────────────────────────────────────────────────────────────

def test_resumen_title_has_data_i18n():
    html = _html('resumen.html')
    assert _has_attr(html, 'resumen.title'), \
        "resumen.html: title missing data-i18n='resumen.title'"


def test_resumen_subtitle_has_data_i18n():
    html = _html('resumen.html')
    assert _has_attr(html, 'resumen.subtitle'), \
        "resumen.html: subtitle missing data-i18n='resumen.subtitle'"


def test_resumen_buttons_have_data_i18n():
    html = _html('resumen.html')
    for key in ('btn.exportCsv', 'btn.refresh'):
        assert _has_attr(html, key), \
            f"resumen.html: button missing data-i18n='{key}'"


def test_resumen_stat_labels_have_data_i18n():
    html = _html('resumen.html')
    for key in ('stat.farms', 'stat.avgHealth', 'resumen.totalSavings', 'resumen.projectedRoi'):
        assert _has_attr(html, key), \
            f"resumen.html: stat label missing data-i18n='{key}'"


def test_resumen_panel_titles_have_data_i18n():
    html = _html('resumen.html')
    for key in ('resumen.healthDist', 'resumen.farmPortfolio'):
        assert _has_attr(html, key), \
            f"resumen.html: panel title missing data-i18n='{key}'"


# ── status.html ───────────────────────────────────────────────────────────────

def test_status_title_has_data_i18n():
    html = _html('status.html')
    assert _has_attr(html, 'status.title'), \
        "status.html: title missing data-i18n='status.title'"


def test_status_subtitle_has_data_i18n():
    html = _html('status.html')
    assert _has_attr(html, 'status.subtitle'), \
        "status.html: subtitle missing data-i18n='status.subtitle'"


def test_status_panel_titles_have_data_i18n():
    html = _html('status.html')
    for key in ('status.connectivity', 'status.dataFreshness', 'status.activeEndpoints'):
        assert _has_attr(html, key), \
            f"status.html: panel title missing data-i18n='{key}'"


# ── carbon.html ───────────────────────────────────────────────────────────────

def test_carbon_title_has_data_i18n():
    html = _html('carbon.html')
    assert _has_attr(html, 'carbon.title'), \
        "carbon.html: title missing data-i18n='carbon.title'"


def test_carbon_subtitle_has_data_i18n():
    html = _html('carbon.html')
    assert _has_attr(html, 'carbon.subtitle'), \
        "carbon.html: subtitle missing data-i18n='carbon.subtitle'"


def test_carbon_card_titles_have_data_i18n():
    html = _html('carbon.html')
    for key in ('carbon.socTrend', 'carbon.summary', 'carbon.fieldBreakdown'):
        assert _has_attr(html, key), \
            f"carbon.html: card title missing data-i18n='{key}'"


# ── anomalies.html ────────────────────────────────────────────────────────────

def test_anomalies_title_has_data_i18n():
    html = _html('anomalies.html')
    assert _has_attr(html, 'anomaly.title'), \
        "anomalies.html: title missing data-i18n='anomaly.title'"


def test_anomalies_subtitle_has_data_i18n():
    html = _html('anomalies.html')
    assert _has_attr(html, 'anomaly.subtitle'), \
        "anomalies.html: subtitle missing data-i18n='anomaly.subtitle'"


def test_anomalies_section_titles_have_data_i18n():
    html = _html('anomalies.html')
    for key in ('anomaly.healthSection', 'anomaly.ndviSection', 'anomaly.recommendations'):
        assert _has_attr(html, key), \
            f"anomalies.html: section title missing data-i18n='{key}'"


# ── actions.html ──────────────────────────────────────────────────────────────

def test_actions_title_has_data_i18n():
    html = _html('actions.html')
    assert _has_attr(html, 'actions.title'), \
        "actions.html: title missing data-i18n='actions.title'"


def test_actions_subtitle_has_data_i18n():
    html = _html('actions.html')
    assert _has_attr(html, 'actions.subtitle'), \
        "actions.html: subtitle missing data-i18n='actions.subtitle'"


def test_actions_button_has_data_i18n():
    html = _html('actions.html')
    assert _has_attr(html, 'btn.analyze'), \
        "actions.html: Analizar button missing data-i18n='btn.analyze'"


# ── plataforma.html ───────────────────────────────────────────────────────────

def test_plataforma_title_has_data_i18n():
    html = _html('plataforma.html')
    assert _has_attr(html, 'plataforma.title'), \
        "plataforma.html: title missing data-i18n='plataforma.title'"


def test_plataforma_subtitle_has_data_i18n():
    html = _html('plataforma.html')
    assert _has_attr(html, 'plataforma.subtitle'), \
        "plataforma.html: subtitle missing data-i18n='plataforma.subtitle'"


def test_plataforma_category_titles_have_data_i18n():
    html = _html('plataforma.html')
    for key in ('plataforma.cerebro', 'plataforma.crops', 'plataforma.drone',
                'plataforma.alerts', 'plataforma.reports', 'plataforma.operations'):
        assert _has_attr(html, key), \
            f"plataforma.html: category title missing data-i18n='{key}'"


# ── demo-fodecijal.html ───────────────────────────────────────────────────────

def test_demo_fodecijal_title_has_data_i18n():
    html = _html('demo-fodecijal.html')
    assert _has_attr(html, 'demo.title'), \
        "demo-fodecijal.html: <h1> missing data-i18n='demo.title'"


def test_demo_fodecijal_stat_labels_have_data_i18n():
    html = _html('demo-fodecijal.html')
    for key in ('demo.steps', 'demo.completed', 'demo.remaining'):
        assert _has_attr(html, key), \
            f"demo-fodecijal.html: stat label missing data-i18n='{key}'"


def test_demo_fodecijal_step_titles_have_data_i18n():
    html = _html('demo-fodecijal.html')
    for key in ('demo.step1', 'demo.step4', 'demo.step8'):
        assert _has_attr(html, key), \
            f"demo-fodecijal.html: step title missing data-i18n='{key}'"


# ── i18n.js EN key checks ─────────────────────────────────────────────────────

def test_i18n_has_exec_keys_en():
    content = _i18n()
    for key in ('exec.title', 'exec.subtitle', 'exec.activity30', 'exec.farmsTable'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_resumen_keys_en():
    content = _i18n()
    for key in ('resumen.title', 'resumen.subtitle', 'resumen.healthDist',
                'resumen.farmPortfolio', 'resumen.totalSavings', 'resumen.projectedRoi'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_status_keys_en():
    content = _i18n()
    for key in ('status.title', 'status.subtitle',
                'status.connectivity', 'status.dataFreshness', 'status.activeEndpoints'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_carbon_keys_en():
    content = _i18n()
    for key in ('carbon.title', 'carbon.subtitle',
                'carbon.socTrend', 'carbon.summary', 'carbon.fieldBreakdown'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_anomaly_keys_en():
    content = _i18n()
    for key in ('anomaly.title', 'anomaly.subtitle',
                'anomaly.healthSection', 'anomaly.ndviSection', 'anomaly.recommendations'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_actions_keys_en():
    content = _i18n()
    for key in ('actions.title', 'actions.subtitle', 'btn.analyze'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_plataforma_keys_en():
    content = _i18n()
    for key in ('plataforma.title', 'plataforma.subtitle', 'plataforma.cerebro',
                'plataforma.crops', 'plataforma.drone', 'plataforma.alerts',
                'plataforma.reports', 'plataforma.operations'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_demo_keys_en():
    content = _i18n()
    for key in ('demo.title', 'demo.steps', 'demo.completed', 'demo.remaining',
                'demo.step1', 'demo.step2', 'demo.step3', 'demo.step4',
                'demo.step5', 'demo.step6', 'demo.step7', 'demo.step8'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_btn_keys_en():
    content = _i18n()
    for key in ('btn.refresh', 'btn.exportCsv', 'btn.analyze'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"
