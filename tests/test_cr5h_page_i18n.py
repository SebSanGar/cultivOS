"""
CR5h — Wire 8 pages into i18n: page titles, subtitles, stat labels, h2 sections.
Source-inspection tests (no server). Pages: irrigation, microbiome, precision-ia,
prediccion-salud, preparacion-fodecijal, prioridad-riesgo, ranking-miembros, regenerative.
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


# ── irrigation.html ───────────────────────────────────────────────────────────

def test_irrigation_title_has_data_i18n():
    html = _html('irrigation.html')
    assert _has_attr(html, 'irrigation.title'), \
        "irrigation.html: <h1> missing data-i18n='irrigation.title'"


def test_irrigation_subtitle_has_data_i18n():
    html = _html('irrigation.html')
    assert _has_attr(html, 'irrigation.subtitle'), \
        "irrigation.html: subtitle <p> missing data-i18n='irrigation.subtitle'"


def test_irrigation_query_btn_has_data_i18n():
    html = _html('irrigation.html')
    assert _has_attr(html, 'irrigation.queryBtn'), \
        "irrigation.html: 'Consultar Riego' button missing data-i18n='irrigation.queryBtn'"


def test_irrigation_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('irrigation.title', 'irrigation.subtitle', 'irrigation.queryBtn'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_irrigation_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('irrigation.title', 'irrigation.subtitle', 'irrigation.queryBtn'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── microbiome.html ───────────────────────────────────────────────────────────

def test_microbiome_title_has_data_i18n():
    html = _html('microbiome.html')
    assert _has_attr(html, 'microbiome.title'), \
        "microbiome.html: <h1> missing data-i18n='microbiome.title'"


def test_microbiome_subtitle_has_data_i18n():
    html = _html('microbiome.html')
    assert _has_attr(html, 'microbiome.subtitle'), \
        "microbiome.html: subtitle <p> missing data-i18n='microbiome.subtitle'"


def test_microbiome_update_btn_has_data_i18n():
    html = _html('microbiome.html')
    assert _has_attr(html, 'microbiome.updateBtn'), \
        "microbiome.html: 'Actualizar' button missing data-i18n='microbiome.updateBtn'"


def test_microbiome_respiration_h2_has_data_i18n():
    html = _html('microbiome.html')
    assert _has_attr(html, 'microbiome.respiration'), \
        "microbiome.html: 'Tendencia de Respiracion del Suelo' h2 missing data-i18n='microbiome.respiration'"


def test_microbiome_respiration_sub_has_data_i18n():
    html = _html('microbiome.html')
    assert _has_attr(html, 'microbiome.respirationSub'), \
        "microbiome.html: respiration subtitle <p> missing data-i18n='microbiome.respirationSub'"


def test_microbiome_fungi_ratio_h2_has_data_i18n():
    html = _html('microbiome.html')
    assert _has_attr(html, 'microbiome.fungiRatio'), \
        "microbiome.html: 'Relacion Hongos/Bacterias' h2 missing data-i18n='microbiome.fungiRatio'"


def test_microbiome_fungi_ratio_sub_has_data_i18n():
    html = _html('microbiome.html')
    assert _has_attr(html, 'microbiome.fungiRatioSub'), \
        "microbiome.html: fungi ratio subtitle <p> missing data-i18n='microbiome.fungiRatioSub'"


def test_microbiome_biomas_c_h2_has_data_i18n():
    html = _html('microbiome.html')
    assert _has_attr(html, 'microbiome.biomasC'), \
        "microbiome.html: 'Carbono de Biomasa Microbiana' h2 missing data-i18n='microbiome.biomasC'"


def test_microbiome_biomas_c_sub_has_data_i18n():
    html = _html('microbiome.html')
    assert _has_attr(html, 'microbiome.biomasCsub'), \
        "microbiome.html: biomass carbon subtitle <p> missing data-i18n='microbiome.biomasCsub'"


def test_microbiome_sample_history_h2_has_data_i18n():
    html = _html('microbiome.html')
    assert _has_attr(html, 'microbiome.sampleHistory'), \
        "microbiome.html: 'Historial de Muestras' h2 missing data-i18n='microbiome.sampleHistory'"


def test_microbiome_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'microbiome.title', 'microbiome.subtitle', 'microbiome.updateBtn',
        'microbiome.respiration', 'microbiome.respirationSub',
        'microbiome.fungiRatio', 'microbiome.fungiRatioSub',
        'microbiome.biomasC', 'microbiome.biomasCsub', 'microbiome.sampleHistory',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_microbiome_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'microbiome.title', 'microbiome.subtitle', 'microbiome.updateBtn',
        'microbiome.respiration', 'microbiome.respirationSub',
        'microbiome.fungiRatio', 'microbiome.fungiRatioSub',
        'microbiome.biomasC', 'microbiome.biomasCsub', 'microbiome.sampleHistory',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── precision-ia.html ─────────────────────────────────────────────────────────

def test_precision_ia_title_has_data_i18n():
    html = _html('precision-ia.html')
    assert _has_attr(html, 'precisionIA.title'), \
        "precision-ia.html: <h1> missing data-i18n='precisionIA.title'"


def test_precision_ia_subtitle_has_data_i18n():
    html = _html('precision-ia.html')
    assert _has_attr(html, 'precisionIA.subtitle'), \
        "precision-ia.html: subtitle <p> missing data-i18n='precisionIA.subtitle'"


def test_precision_ia_recent_error_h2_has_data_i18n():
    html = _html('precision-ia.html')
    assert _has_attr(html, 'precisionIA.recentError'), \
        "precision-ia.html: 'Predicciones Recientes — Error por Prediccion' h2 missing data-i18n"


def test_precision_ia_by_type_h2_has_data_i18n():
    html = _html('precision-ia.html')
    assert _has_attr(html, 'precisionIA.byType'), \
        "precision-ia.html: 'Precision por Tipo de Prediccion' h2 missing data-i18n"


def test_precision_ia_recent_h2_has_data_i18n():
    html = _html('precision-ia.html')
    assert _has_attr(html, 'precisionIA.recent'), \
        "precision-ia.html: 'Predicciones Recientes' h2 missing data-i18n"


def test_precision_ia_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'precisionIA.title', 'precisionIA.subtitle',
        'precisionIA.recentError', 'precisionIA.byType', 'precisionIA.recent',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_precision_ia_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'precisionIA.title', 'precisionIA.subtitle',
        'precisionIA.recentError', 'precisionIA.byType', 'precisionIA.recent',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── regenerative.html ─────────────────────────────────────────────────────────

def test_regen_score_title_has_data_i18n():
    html = _html('regenerative.html')
    assert _has_attr(html, 'regenScore.title'), \
        "regenerative.html: <h1> missing data-i18n='regenScore.title'"


def test_regen_score_subtitle_has_data_i18n():
    html = _html('regenerative.html')
    assert _has_attr(html, 'regenScore.subtitle'), \
        "regenerative.html: subtitle <p> missing data-i18n='regenScore.subtitle'"


def test_regen_score_update_btn_has_data_i18n():
    html = _html('regenerative.html')
    assert _has_attr(html, 'regenScore.updateBtn'), \
        "regenerative.html: 'Actualizar' button missing data-i18n='regenScore.updateBtn'"


def test_regen_score_breakdown_h2_has_data_i18n():
    html = _html('regenerative.html')
    assert _has_attr(html, 'regenScore.breakdown'), \
        "regenerative.html: 'Desglose de Componentes' h2 missing data-i18n='regenScore.breakdown'"


def test_regen_score_improve_h2_has_data_i18n():
    html = _html('regenerative.html')
    assert _has_attr(html, 'regenScore.improve'), \
        "regenerative.html: 'Recomendaciones para Mejorar' h2 missing data-i18n='regenScore.improve'"


def test_regen_score_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'regenScore.title', 'regenScore.subtitle', 'regenScore.updateBtn',
        'regenScore.breakdown', 'regenScore.improve',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_regen_score_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'regenScore.title', 'regenScore.subtitle', 'regenScore.updateBtn',
        'regenScore.breakdown', 'regenScore.improve',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── prediccion-salud.html ─────────────────────────────────────────────────────

def test_pred_salud_title_has_data_i18n():
    html = _html('prediccion-salud.html')
    assert _has_attr(html, 'predSalud.title'), \
        "prediccion-salud.html: <h1> missing data-i18n='predSalud.title'"


def test_pred_salud_subtitle_has_data_i18n():
    html = _html('prediccion-salud.html')
    assert _has_attr(html, 'predSalud.subtitle'), \
        "prediccion-salud.html: subtitle <p> missing data-i18n='predSalud.subtitle'"


def test_pred_salud_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('predSalud.title', 'predSalud.subtitle'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_pred_salud_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('predSalud.title', 'predSalud.subtitle'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── preparacion-fodecijal.html ────────────────────────────────────────────────

def test_fodecijal_title_has_data_i18n():
    html = _html('preparacion-fodecijal.html')
    assert _has_attr(html, 'fodecijal.title'), \
        "preparacion-fodecijal.html: <h1> missing data-i18n='fodecijal.title'"


def test_fodecijal_subtitle_has_data_i18n():
    html = _html('preparacion-fodecijal.html')
    assert _has_attr(html, 'fodecijal.subtitle'), \
        "preparacion-fodecijal.html: subtitle <p> missing data-i18n='fodecijal.subtitle'"


def test_fodecijal_pillars_h2_has_data_i18n():
    html = _html('preparacion-fodecijal.html')
    assert _has_attr(html, 'fodecijal.pillars'), \
        "preparacion-fodecijal.html: 'Pilares de Evaluacion' h2 missing data-i18n='fodecijal.pillars'"


def test_fodecijal_coop_label_has_data_i18n():
    html = _html('preparacion-fodecijal.html')
    assert _has_attr(html, 'lbl.cooperative'), \
        "preparacion-fodecijal.html: Cooperativa label missing data-i18n='lbl.cooperative'"


def test_fodecijal_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('fodecijal.title', 'fodecijal.subtitle', 'fodecijal.pillars'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_fodecijal_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('fodecijal.title', 'fodecijal.subtitle', 'fodecijal.pillars'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── prioridad-riesgo.html ─────────────────────────────────────────────────────

def test_prio_risk_title_has_data_i18n():
    html = _html('prioridad-riesgo.html')
    assert _has_attr(html, 'prioRisk.title'), \
        "prioridad-riesgo.html: <h1> missing data-i18n='prioRisk.title'"


def test_prio_risk_subtitle_has_data_i18n():
    html = _html('prioridad-riesgo.html')
    assert _has_attr(html, 'prioRisk.subtitle'), \
        "prioridad-riesgo.html: subtitle <p> missing data-i18n='prioRisk.subtitle'"


def test_prio_risk_farm_label_has_data_i18n():
    html = _html('prioridad-riesgo.html')
    assert _has_attr(html, 'lbl.farm'), \
        "prioridad-riesgo.html: Finca label missing data-i18n='lbl.farm'"


def test_prio_risk_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('prioRisk.title', 'prioRisk.subtitle'):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_prio_risk_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('prioRisk.title', 'prioRisk.subtitle'):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── ranking-miembros.html ─────────────────────────────────────────────────────

def test_ranking_miembros_title_has_data_i18n():
    html = _html('ranking-miembros.html')
    assert _has_attr(html, 'rankingMiembros.title'), \
        "ranking-miembros.html: <h1> missing data-i18n='rankingMiembros.title'"


def test_ranking_miembros_coop_label_has_data_i18n():
    html = _html('ranking-miembros.html')
    assert _has_attr(html, 'lbl.cooperative'), \
        "ranking-miembros.html: Cooperativa label missing data-i18n='lbl.cooperative'"


def test_ranking_miembros_keys_in_i18n_es():
    i18n = _i18n()
    assert _has_key_es(i18n, 'rankingMiembros.title'), \
        "i18n.js es block missing 'rankingMiembros.title'"


def test_ranking_miembros_keys_in_i18n_en():
    i18n = _i18n()
    assert _has_key_en(i18n, 'rankingMiembros.title'), \
        "i18n.js en block missing 'rankingMiembros.title'"
