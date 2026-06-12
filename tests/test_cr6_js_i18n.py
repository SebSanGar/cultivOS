"""
CR6 — Spanish literals in JS renderers → t() keys.
Source-inspection tests (no server). Checks that hardcoded Spanish strings
in dynamic render paths are replaced with t() calls, and that keys exist
in i18n.js (ES + EN).

Target files: efectividad.js, disease.js, fusion-page.js, timeline.js, trayectoria.js
"""

import os

FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')
I18N_JS = os.path.join(FRONTEND, 'i18n.js')


def _js(name: str) -> str:
    with open(os.path.join(FRONTEND, name), 'r', encoding='utf-8') as f:
        return f.read()


def _i18n() -> str:
    with open(I18N_JS, 'r', encoding='utf-8') as f:
        return f.read()


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


# ── efectividad.js ─────────────────────────────────────────────────────────────

def test_efectividad_no_tratamientos_evaluados():
    js = _js('efectividad.js')
    assert 'Tratamientos evaluados' not in js, \
        "efectividad.js: 'Tratamientos evaluados' must be replaced with t('eff.stat.evaluated')"


def test_efectividad_no_aplicaciones_totales():
    js = _js('efectividad.js')
    assert 'Aplicaciones totales' not in js, \
        "efectividad.js: 'Aplicaciones totales' must be replaced with t('eff.stat.applications')"


def test_efectividad_no_delta_promedio():
    js = _js('efectividad.js')
    assert 'Delta promedio de salud' not in js, \
        "efectividad.js: 'Delta promedio de salud' must be replaced with t('eff.stat.avgDelta')"


def test_efectividad_no_mejor_tratamiento():
    js = _js('efectividad.js')
    assert 'Mejor tratamiento' not in js, \
        "efectividad.js: 'Mejor tratamiento' must be replaced with t('eff.stat.bestTreatment')"


def test_efectividad_no_aplicaciones_suffix():
    js = _js('efectividad.js')
    assert "' aplicaciones'" not in js and '" aplicaciones"' not in js, \
        "efectividad.js: ' aplicaciones' suffix must be replaced with t('eff.suffix.apps')"


def test_efectividad_no_mejor_para():
    js = _js('efectividad.js')
    assert 'Mejor para: ' not in js, \
        "efectividad.js: 'Mejor para: ' must be replaced with t('eff.prefix.bestFor')"


def test_eff_stat_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('eff.stat.evaluated', 'eff.stat.applications', 'eff.stat.avgDelta', 'eff.stat.bestTreatment'):
        assert _has_key_es(i18n, key), \
            f"i18n.js missing ES key '{key}'"


def test_eff_stat_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('eff.stat.evaluated', 'eff.stat.applications', 'eff.stat.avgDelta', 'eff.stat.bestTreatment'):
        assert _has_key_en(i18n, key), \
            f"i18n.js missing EN key '{key}'"


# ── disease.js ─────────────────────────────────────────────────────────────────

def test_disease_no_seleccione_granja():
    js = _js('disease.js')
    assert 'Seleccione una granja y un campo para consultar el riesgo' not in js, \
        "disease.js: select prompt must be replaced with t('dis.selectPrompt')"


def test_disease_no_no_se_pudo_evaluacion():
    js = _js('disease.js')
    assert 'No se pudo obtener la evaluacion de riesgo' not in js, \
        "disease.js: fetch error must be replaced with t('dis.fetchError')"


def test_disease_no_sin_evaluacion():
    js = _js('disease.js')
    assert 'Sin evaluacion disponible' not in js, \
        "disease.js: no-assessment fallback must be replaced with t('dis.noAssessment')"


def test_disease_no_sin_riesgos():
    js = _js('disease.js')
    assert 'Sin riesgos detectados para este campo' not in js, \
        "disease.js: no-risks message must be replaced with t('dis.noRisks')"


def test_disease_no_buscando():
    js = _js('disease.js')
    assert 'Buscando...' not in js, \
        "disease.js: 'Buscando...' must be replaced with t('dis.searching')"


def test_disease_no_sin_coincidencias():
    js = _js('disease.js')
    assert 'Sin coincidencias encontradas' not in js, \
        "disease.js: no-matches message must be replaced with t('dis.noMatches')"


def test_dis_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('dis.selectPrompt', 'dis.fetchError', 'dis.noAssessment', 'dis.noRisks',
                'dis.searching', 'dis.noMatches', 'dis.severity', 'dis.symptoms', 'dis.treatments'):
        assert _has_key_es(i18n, key), \
            f"i18n.js missing ES key '{key}'"


def test_dis_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('dis.selectPrompt', 'dis.fetchError', 'dis.noAssessment', 'dis.noRisks',
                'dis.searching', 'dis.noMatches', 'dis.severity', 'dis.symptoms', 'dis.treatments'):
        assert _has_key_en(i18n, key), \
            f"i18n.js missing EN key '{key}'"


# ── fusion-page.js ─────────────────────────────────────────────────────────────

def test_fusion_no_termico_in_sensor_labels():
    js = _js('fusion-page.js')
    # sensorLabels should use t() not bare Spanish
    assert '"Termico"' not in js and "'Termico'" not in js, \
        "fusion-page.js: 'Termico' sensorLabel must be replaced with t('fus.sensor.thermal')"


def test_fusion_no_suelo_in_sensor_labels():
    js = _js('fusion-page.js')
    assert '"Suelo"' not in js and "'Suelo'" not in js, \
        "fusion-page.js: 'Suelo' sensorLabel must be replaced with t('fus.sensor.soil')"


def test_fusion_no_clima_in_sensor_labels():
    js = _js('fusion-page.js')
    assert '"Clima"' not in js and "'Clima'" not in js, \
        "fusion-page.js: 'Clima' sensorLabel must be replaced with t('fus.sensor.weather')"


def test_fusion_no_cargando():
    js = _js('fusion-page.js')
    assert 'Cargando...' not in js, \
        "fusion-page.js: 'Cargando...' must be replaced with t('dash.loadingGeneric') or equivalent"


def test_fusion_no_no_se_pudo_fusion():
    js = _js('fusion-page.js')
    assert 'No se pudo obtener los datos de fusion' not in js, \
        "fusion-page.js: fetch error must be replaced with t('fus.fetchError')"


def test_fusion_no_inconsistente():
    js = _js('fusion-page.js')
    assert '"Inconsistente"' not in js and "'Inconsistente'" not in js, \
        "fusion-page.js: 'Inconsistente' must be replaced with t('fus.status.inconsistent')"


def test_fusion_no_sin_contradicciones():
    js = _js('fusion-page.js')
    assert 'Sin contradicciones detectadas' not in js, \
        "fusion-page.js: no-contradictions message must be replaced with t('fus.noContradictions')"


def test_fus_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('fus.sensor.thermal', 'fus.sensor.soil', 'fus.sensor.weather',
                'fus.fetchError', 'fus.status.inconsistent', 'fus.status.consistent',
                'fus.noContradictions', 'fus.noFieldCards'):
        assert _has_key_es(i18n, key), \
            f"i18n.js missing ES key '{key}'"


def test_fus_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('fus.sensor.thermal', 'fus.sensor.soil', 'fus.sensor.weather',
                'fus.fetchError', 'fus.status.inconsistent', 'fus.status.consistent',
                'fus.noContradictions', 'fus.noFieldCards'):
        assert _has_key_en(i18n, key), \
            f"i18n.js missing EN key '{key}'"


# ── timeline.js ────────────────────────────────────────────────────────────────

def test_timeline_no_mejorando_in_trend_labels():
    js = _js('timeline.js')
    assert "'Mejorando'" not in js and '"Mejorando"' not in js, \
        "timeline.js: 'Mejorando' TREND_LABEL must be replaced with t('tl.trend.improving')"


def test_timeline_no_estable_in_trend_labels():
    js = _js('timeline.js')
    assert "'Estable'" not in js and '"Estable"' not in js, \
        "timeline.js: 'Estable' TREND_LABEL must be replaced with t('tl.trend.stable')"


def test_timeline_no_no_hay_datos():
    js = _js('timeline.js')
    assert 'No hay datos de salud ni tratamientos' not in js, \
        "timeline.js: no-data message must be replaced with t('tl.noData')"


def test_timeline_no_puntuacion_salud():
    js = _js('timeline.js')
    assert 'Puntuacion de Salud: ' not in js, \
        "timeline.js: 'Puntuacion de Salud: ' must be replaced with t('tl.healthScore')"


def test_tl_trend_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('tl.trend.improving', 'tl.trend.stable', 'tl.trend.declining', 'tl.trend.insufficient'):
        assert _has_key_es(i18n, key), \
            f"i18n.js missing ES key '{key}'"


def test_tl_trend_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('tl.trend.improving', 'tl.trend.stable', 'tl.trend.declining', 'tl.trend.insufficient'):
        assert _has_key_en(i18n, key), \
            f"i18n.js missing EN key '{key}'"


def test_tl_render_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('tl.noData', 'tl.healthScore', 'tl.sources', 'tl.notes', 'tl.problem', 'tl.healthAt'):
        assert _has_key_es(i18n, key), \
            f"i18n.js missing ES key '{key}'"


def test_tl_render_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('tl.noData', 'tl.healthScore', 'tl.sources', 'tl.notes', 'tl.problem', 'tl.healthAt'):
        assert _has_key_en(i18n, key), \
            f"i18n.js missing EN key '{key}'"


# ── trayectoria.js ─────────────────────────────────────────────────────────────

def test_trayectoria_no_mejorando_in_trend_labels():
    js = _js('trayectoria.js')
    assert "'Mejorando'" not in js and '"Mejorando"' not in js, \
        "trayectoria.js: 'Mejorando' TREND_LABEL must be replaced with t('tl.trend.improving')"


def test_trayectoria_no_datos_insuficientes_proyeccion():
    js = _js('trayectoria.js')
    assert 'Datos insuficientes para proyeccion' not in js, \
        "trayectoria.js: projection-insufficient must be replaced with t('traj.insufficientData')"


def test_trayectoria_no_sin_fecha():
    js = _js('trayectoria.js')
    assert "'Sin fecha'" not in js and '"Sin fecha"' not in js, \
        "trayectoria.js: 'Sin fecha' must be replaced with t('traj.noDate')"


def test_trayectoria_no_no_hay_tratamientos():
    js = _js('trayectoria.js')
    assert 'No hay tratamientos con correlacion de salud' not in js, \
        "trayectoria.js: no-treatments message must be replaced with t('traj.noTreatments')"


def test_traj_keys_in_i18n_es():
    i18n = _i18n()
    for key in ('traj.insufficientData', 'traj.noDate', 'traj.noTreatments',
                'traj.noRange', 'traj.chart.health', 'traj.chart.treatments'):
        assert _has_key_es(i18n, key), \
            f"i18n.js missing ES key '{key}'"


def test_traj_keys_in_i18n_en():
    i18n = _i18n()
    for key in ('traj.insufficientData', 'traj.noDate', 'traj.noTreatments',
                'traj.noRange', 'traj.chart.health', 'traj.chart.treatments'):
        assert _has_key_en(i18n, key), \
            f"i18n.js missing EN key '{key}'"
