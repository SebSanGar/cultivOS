"""
CR5b — Wire 8 pages into i18n: page titles, subtitles, stat labels, section headings, buttons.
Source-inspection tests (no server). Pages: management, flota, cooperativa, exportar,
onboarding, mission, recommendations, rotation.
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


# ── management.html ───────────────────────────────────────────────────────────

def test_management_title_has_data_i18n():
    html = _html('management.html')
    assert _has_attr(html, 'mgmt.title'), \
        "management.html: <h1> missing data-i18n='mgmt.title'"


def test_management_subtitle_has_data_i18n():
    html = _html('management.html')
    assert _has_attr(html, 'mgmt.subtitle'), \
        "management.html: subtitle missing data-i18n='mgmt.subtitle'"


def test_management_section_titles_have_data_i18n():
    html = _html('management.html')
    for key in ('mgmt.newFarm', 'mgmt.registeredFarms'):
        assert _has_attr(html, key), \
            f"management.html: section title missing data-i18n='{key}'"


def test_management_create_button_has_data_i18n():
    html = _html('management.html')
    assert _has_attr(html, 'btn.createFarm'), \
        "management.html: create button missing data-i18n='btn.createFarm'"


# ── flota.html ────────────────────────────────────────────────────────────────

def test_flota_title_has_data_i18n():
    html = _html('flota.html')
    assert _has_attr(html, 'fleet.title'), \
        "flota.html: <h1> missing data-i18n='fleet.title'"


def test_flota_subtitle_has_data_i18n():
    html = _html('flota.html')
    assert _has_attr(html, 'fleet.subtitle'), \
        "flota.html: subtitle missing data-i18n='fleet.subtitle'"


def test_flota_stat_labels_have_data_i18n():
    html = _html('flota.html')
    for key in ('fleet.total', 'fleet.operational', 'fleet.coverage', 'fleet.investment'):
        assert _has_attr(html, key), \
            f"flota.html: stat label missing data-i18n='{key}'"


def test_flota_summary_has_data_i18n():
    html = _html('flota.html')
    assert _has_attr(html, 'fleet.summary'), \
        "flota.html: summary card title missing data-i18n='fleet.summary'"


# ── cooperativa.html ──────────────────────────────────────────────────────────

def test_cooperativa_title_has_data_i18n():
    html = _html('cooperativa.html')
    assert _has_attr(html, 'coop.title'), \
        "cooperativa.html: <h1> missing data-i18n='coop.title'"


def test_cooperativa_subtitle_has_data_i18n():
    html = _html('cooperativa.html')
    assert _has_attr(html, 'coop.subtitle'), \
        "cooperativa.html: subtitle missing data-i18n='coop.subtitle'"


def test_cooperativa_stat_labels_have_data_i18n():
    html = _html('cooperativa.html')
    for key in ('coop.statCoops', 'stat.farms', 'stat.hectares', 'stat.avgHealth'):
        assert _has_attr(html, key), \
            f"cooperativa.html: stat label missing data-i18n='{key}'"


# ── exportar.html ─────────────────────────────────────────────────────────────

def test_exportar_title_has_data_i18n():
    html = _html('exportar.html')
    assert _has_attr(html, 'export.title'), \
        "exportar.html: <h1> missing data-i18n='export.title'"


def test_exportar_subtitle_has_data_i18n():
    html = _html('exportar.html')
    assert _has_attr(html, 'export.subtitle'), \
        "exportar.html: subtitle missing data-i18n='export.subtitle'"


def test_exportar_stat_labels_have_data_i18n():
    html = _html('exportar.html')
    for key in ('stat.farms', 'stat.hectares', 'stat.fields'):
        assert _has_attr(html, key), \
            f"exportar.html: stat label missing data-i18n='{key}'"


def test_exportar_section_titles_have_data_i18n():
    html = _html('exportar.html')
    for key in ('export.configTitle', 'export.categoriesTitle'):
        assert _has_attr(html, key), \
            f"exportar.html: section title missing data-i18n='{key}'"


def test_exportar_download_button_has_data_i18n():
    html = _html('exportar.html')
    assert _has_attr(html, 'btn.download'), \
        "exportar.html: download button missing data-i18n='btn.download'"


# ── onboarding.html ───────────────────────────────────────────────────────────

def test_onboarding_title_has_data_i18n():
    html = _html('onboarding.html')
    assert _has_attr(html, 'onboard.title'), \
        "onboarding.html: <h1> missing data-i18n='onboard.title'"


def test_onboarding_subtitle_has_data_i18n():
    html = _html('onboarding.html')
    assert _has_attr(html, 'onboard.subtitle'), \
        "onboarding.html: subtitle missing data-i18n='onboard.subtitle'"


def test_onboarding_step_labels_have_data_i18n():
    html = _html('onboarding.html')
    for key in ('onboard.stepFarm', 'onboard.stepFields', 'onboard.stepConfirm'):
        assert _has_attr(html, key), \
            f"onboarding.html: step label missing data-i18n='{key}'"


def test_onboarding_nav_buttons_have_data_i18n():
    html = _html('onboarding.html')
    for key in ('btn.next', 'btn.prev', 'btn.finish'):
        assert _has_attr(html, key), \
            f"onboarding.html: wizard button missing data-i18n='{key}'"


# ── mission.html ──────────────────────────────────────────────────────────────

def test_mission_title_has_data_i18n():
    html = _html('mission.html')
    assert _has_attr(html, 'mission.title'), \
        "mission.html: <h1> missing data-i18n='mission.title'"


def test_mission_subtitle_has_data_i18n():
    html = _html('mission.html')
    assert _has_attr(html, 'mission.subtitle'), \
        "mission.html: subtitle missing data-i18n='mission.subtitle'"


def test_mission_stat_labels_have_data_i18n():
    html = _html('mission.html')
    for key in ('mission.duration', 'mission.batteries'):
        assert _has_attr(html, key), \
            f"mission.html: stat label missing data-i18n='{key}'"


def test_mission_generate_button_has_data_i18n():
    html = _html('mission.html')
    assert _has_attr(html, 'btn.generateMission'), \
        "mission.html: generate button missing data-i18n='btn.generateMission'"


# ── recommendations.html ──────────────────────────────────────────────────────

def test_recommendations_title_has_data_i18n():
    html = _html('recommendations.html')
    assert _has_attr(html, 'recs.title'), \
        "recommendations.html: <h1> missing data-i18n='recs.title'"


def test_recommendations_subtitle_has_data_i18n():
    html = _html('recommendations.html')
    assert _has_attr(html, 'recs.subtitle'), \
        "recommendations.html: subtitle missing data-i18n='recs.subtitle'"


def test_recommendations_stat_labels_have_data_i18n():
    html = _html('recommendations.html')
    for key in ('recs.total', 'recs.urgent', 'recs.organic', 'recs.cost'):
        assert _has_attr(html, key), \
            f"recommendations.html: stat label missing data-i18n='{key}'"


# ── rotation.html ─────────────────────────────────────────────────────────────

def test_rotation_title_has_data_i18n():
    html = _html('rotation.html')
    assert _has_attr(html, 'rotation.title'), \
        "rotation.html: <h1> missing data-i18n='rotation.title'"


def test_rotation_subtitle_has_data_i18n():
    html = _html('rotation.html')
    assert _has_attr(html, 'rotation.subtitle'), \
        "rotation.html: subtitle missing data-i18n='rotation.subtitle'"


def test_rotation_stat_labels_have_data_i18n():
    html = _html('rotation.html')
    for key in ('rotation.lastCrop', 'rotation.seasons'):
        assert _has_attr(html, key), \
            f"rotation.html: stat label missing data-i18n='{key}'"


def test_rotation_multiyear_title_has_data_i18n():
    html = _html('rotation.html')
    assert _has_attr(html, 'rotation.multiYearPlan'), \
        "rotation.html: multi-year plan title missing data-i18n='rotation.multiYearPlan'"


def test_rotation_generate_button_has_data_i18n():
    html = _html('rotation.html')
    assert _has_attr(html, 'btn.generatePlan'), \
        "rotation.html: generate plan button missing data-i18n='btn.generatePlan'"


# ── i18n.js EN key checks ─────────────────────────────────────────────────────

def test_i18n_has_mgmt_keys_en():
    content = _i18n()
    for key in ('mgmt.title', 'mgmt.subtitle', 'mgmt.newFarm', 'mgmt.registeredFarms',
                'btn.createFarm'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_fleet_keys_en():
    content = _i18n()
    for key in ('fleet.title', 'fleet.subtitle', 'fleet.total', 'fleet.operational',
                'fleet.coverage', 'fleet.investment', 'fleet.summary'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_coop_keys_en():
    content = _i18n()
    for key in ('coop.title', 'coop.subtitle', 'coop.statCoops'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_export_keys_en():
    content = _i18n()
    for key in ('export.title', 'export.subtitle', 'export.configTitle',
                'export.categoriesTitle', 'btn.download'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_onboard_keys_en():
    content = _i18n()
    for key in ('onboard.title', 'onboard.subtitle', 'onboard.stepFarm',
                'onboard.stepFields', 'onboard.stepConfirm',
                'btn.next', 'btn.prev', 'btn.finish'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_mission_keys_en():
    content = _i18n()
    for key in ('mission.title', 'mission.subtitle', 'mission.duration',
                'mission.batteries', 'btn.generateMission'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_recs_keys_en():
    content = _i18n()
    for key in ('recs.title', 'recs.subtitle', 'recs.total', 'recs.urgent',
                'recs.organic', 'recs.cost'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"


def test_i18n_has_rotation_keys_en():
    content = _i18n()
    for key in ('rotation.title', 'rotation.subtitle', 'rotation.lastCrop',
                'rotation.seasons', 'rotation.multiYearPlan', 'btn.generatePlan'):
        assert _has_key_en(content, key), \
            f"i18n.js EN dict missing key '{key}'"
