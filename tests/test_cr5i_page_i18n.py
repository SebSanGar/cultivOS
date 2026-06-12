"""
CR5i — Wire 8 pages into i18n: page titles, subtitles, stat labels, h2 sections, buttons.
Source-inspection tests (no server). Pages: regional, reporte-anual, reportes, resiliencia,
roi-tratamientos, soil-history, soil-import, yield.
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


# ── regional.html ─────────────────────────────────────────────────────────────

def test_regional_title_has_data_i18n():
    html = _html('regional.html')
    assert _has_attr(html, 'regional.title'), \
        "regional.html: <h1> missing data-i18n='regional.title'"


def test_regional_subtitle_has_data_i18n():
    html = _html('regional.html')
    assert _has_attr(html, 'regional.subtitle'), \
        "regional.html: subtitle <p> missing data-i18n='regional.subtitle'"


def test_regional_stat_regions_has_data_i18n():
    html = _html('regional.html')
    assert _has_attr(html, 'regional.statRegions'), \
        "regional.html: 'Regiones' stat label missing data-i18n='regional.statRegions'"


def test_regional_stat_farms_has_data_i18n():
    html = _html('regional.html')
    assert _has_attr(html, 'regional.statFarms'), \
        "regional.html: 'Granjas' stat label missing data-i18n='regional.statFarms'"


def test_regional_stat_fields_has_data_i18n():
    html = _html('regional.html')
    assert _has_attr(html, 'regional.statFields'), \
        "regional.html: 'Campos' stat label missing data-i18n='regional.statFields'"


def test_regional_stat_hectares_has_data_i18n():
    html = _html('regional.html')
    assert _has_attr(html, 'regional.statHectares'), \
        "regional.html: 'Hectareas' stat label missing data-i18n='regional.statHectares'"


def test_regional_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'regional.title', 'regional.subtitle',
        'regional.statRegions', 'regional.statFarms',
        'regional.statFields', 'regional.statHectares',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_regional_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'regional.title', 'regional.subtitle',
        'regional.statRegions', 'regional.statFarms',
        'regional.statFields', 'regional.statHectares',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── reporte-anual.html ────────────────────────────────────────────────────────

def test_reporte_anual_title_has_data_i18n():
    html = _html('reporte-anual.html')
    assert _has_attr(html, 'reporteAnual.title'), \
        "reporte-anual.html: <h1> missing data-i18n='reporteAnual.title'"


def test_reporte_anual_subtitle_has_data_i18n():
    html = _html('reporte-anual.html')
    assert _has_attr(html, 'reporteAnual.subtitle'), \
        "reporte-anual.html: subtitle <p> missing data-i18n='reporteAnual.subtitle'"


def test_reporte_anual_best_field_has_data_i18n():
    html = _html('reporte-anual.html')
    assert _has_attr(html, 'reporteAnual.bestField'), \
        "reporte-anual.html: 'Mejor campo' label missing data-i18n='reporteAnual.bestField'"


def test_reporte_anual_most_improved_has_data_i18n():
    html = _html('reporte-anual.html')
    assert _has_attr(html, 'reporteAnual.mostImproved'), \
        "reporte-anual.html: 'Mas mejorado' label missing data-i18n='reporteAnual.mostImproved'"


def test_reporte_anual_co2e_has_data_i18n():
    html = _html('reporte-anual.html')
    assert _has_attr(html, 'reporteAnual.co2e'), \
        "reporte-anual.html: 'CO2e secuestrado' label missing data-i18n='reporteAnual.co2e'"


def test_reporte_anual_treatments_has_data_i18n():
    html = _html('reporte-anual.html')
    assert _has_attr(html, 'reporteAnual.treatments'), \
        "reporte-anual.html: 'Tratamientos aplicados' label missing data-i18n='reporteAnual.treatments'"


def test_reporte_anual_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'reporteAnual.title', 'reporteAnual.subtitle',
        'reporteAnual.bestField', 'reporteAnual.mostImproved',
        'reporteAnual.co2e', 'reporteAnual.treatments',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_reporte_anual_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'reporteAnual.title', 'reporteAnual.subtitle',
        'reporteAnual.bestField', 'reporteAnual.mostImproved',
        'reporteAnual.co2e', 'reporteAnual.treatments',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── reportes.html ─────────────────────────────────────────────────────────────

def test_reportes_title_has_data_i18n():
    html = _html('reportes.html')
    assert _has_attr(html, 'reportes.title'), \
        "reportes.html: <h1> missing data-i18n='reportes.title'"


def test_reportes_subtitle_has_data_i18n():
    html = _html('reportes.html')
    assert _has_attr(html, 'reportes.subtitle'), \
        "reportes.html: subtitle <p> missing data-i18n='reportes.subtitle'"


def test_reportes_config_h2_has_data_i18n():
    html = _html('reportes.html')
    assert _has_attr(html, 'reportes.configH2'), \
        "reportes.html: 'Configurar Reporte' h2 missing data-i18n='reportes.configH2'"


def test_reportes_generate_btn_has_data_i18n():
    html = _html('reportes.html')
    assert _has_attr(html, 'reportes.generateBtn'), \
        "reportes.html: 'Generar Reporte PDF' button missing data-i18n='reportes.generateBtn'"


def test_reportes_stat_farms_has_data_i18n():
    html = _html('reportes.html')
    assert _has_attr(html, 'reportes.statFarms'), \
        "reportes.html: 'Granjas' stat label missing data-i18n='reportes.statFarms'"


def test_reportes_stat_hectares_has_data_i18n():
    html = _html('reportes.html')
    assert _has_attr(html, 'reportes.statHectares'), \
        "reportes.html: 'Hectareas' stat label missing data-i18n='reportes.statHectares'"


def test_reportes_stat_parcelas_has_data_i18n():
    html = _html('reportes.html')
    assert _has_attr(html, 'reportes.statParcelas'), \
        "reportes.html: 'Parcelas' stat label missing data-i18n='reportes.statParcelas'"


def test_reportes_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'reportes.title', 'reportes.subtitle',
        'reportes.configH2', 'reportes.generateBtn',
        'reportes.statFarms', 'reportes.statHectares', 'reportes.statParcelas',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_reportes_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'reportes.title', 'reportes.subtitle',
        'reportes.configH2', 'reportes.generateBtn',
        'reportes.statFarms', 'reportes.statHectares', 'reportes.statParcelas',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── resiliencia.html ──────────────────────────────────────────────────────────

def test_resiliencia_title_has_data_i18n():
    html = _html('resiliencia.html')
    assert _has_attr(html, 'resiliencia.title'), \
        "resiliencia.html: <h1> missing data-i18n='resiliencia.title'"


def test_resiliencia_farm_label_has_data_i18n():
    html = _html('resiliencia.html')
    assert _has_attr(html, 'resiliencia.farmLabel'), \
        "resiliencia.html: 'Finca' label missing data-i18n='resiliencia.farmLabel'"


def test_resiliencia_field_label_has_data_i18n():
    html = _html('resiliencia.html')
    assert _has_attr(html, 'resiliencia.fieldLabel'), \
        "resiliencia.html: 'Campo' label missing data-i18n='resiliencia.fieldLabel'"


def test_resiliencia_comp_health_has_data_i18n():
    html = _html('resiliencia.html')
    assert _has_attr(html, 'resiliencia.compHealth'), \
        "resiliencia.html: 'Salud' comp label missing data-i18n='resiliencia.compHealth'"


def test_resiliencia_comp_soil_ph_has_data_i18n():
    html = _html('resiliencia.html')
    assert _has_attr(html, 'resiliencia.compSoilPh'), \
        "resiliencia.html: 'pH del suelo' comp label missing data-i18n='resiliencia.compSoilPh'"


def test_resiliencia_comp_water_stress_has_data_i18n():
    html = _html('resiliencia.html')
    assert _has_attr(html, 'resiliencia.compWaterStress'), \
        "resiliencia.html: 'Estres hidrico inv.' label missing data-i18n='resiliencia.compWaterStress'"


def test_resiliencia_comp_disease_risk_has_data_i18n():
    html = _html('resiliencia.html')
    assert _has_attr(html, 'resiliencia.compDiseaseRisk'), \
        "resiliencia.html: 'Riesgo enfermedad inv.' label missing data-i18n='resiliencia.compDiseaseRisk'"


def test_resiliencia_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'resiliencia.title', 'resiliencia.farmLabel', 'resiliencia.fieldLabel',
        'resiliencia.compHealth', 'resiliencia.compSoilPh',
        'resiliencia.compWaterStress', 'resiliencia.compDiseaseRisk',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_resiliencia_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'resiliencia.title', 'resiliencia.farmLabel', 'resiliencia.fieldLabel',
        'resiliencia.compHealth', 'resiliencia.compSoilPh',
        'resiliencia.compWaterStress', 'resiliencia.compDiseaseRisk',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── roi-tratamientos.html ─────────────────────────────────────────────────────

def test_roi_trat_title_has_data_i18n():
    html = _html('roi-tratamientos.html')
    assert _has_attr(html, 'roiTrat.title'), \
        "roi-tratamientos.html: <h1> missing data-i18n='roiTrat.title'"


def test_roi_trat_subtitle_has_data_i18n():
    html = _html('roi-tratamientos.html')
    assert _has_attr(html, 'roiTrat.subtitle'), \
        "roi-tratamientos.html: subtitle <p> missing data-i18n='roiTrat.subtitle'"


def test_roi_trat_best_roi_has_data_i18n():
    html = _html('roi-tratamientos.html')
    assert _has_attr(html, 'roiTrat.bestRoi'), \
        "roi-tratamientos.html: 'Mejor ROI' label missing data-i18n='roiTrat.bestRoi'"


def test_roi_trat_worst_roi_has_data_i18n():
    html = _html('roi-tratamientos.html')
    assert _has_attr(html, 'roiTrat.worstRoi'), \
        "roi-tratamientos.html: 'Peor ROI' label missing data-i18n='roiTrat.worstRoi'"


def test_roi_trat_recommendation_has_data_i18n():
    html = _html('roi-tratamientos.html')
    assert _has_attr(html, 'roiTrat.recommendation'), \
        "roi-tratamientos.html: 'Recomendacion' label missing data-i18n='roiTrat.recommendation'"


def test_roi_trat_empty_has_data_i18n():
    html = _html('roi-tratamientos.html')
    assert _has_attr(html, 'roiTrat.empty'), \
        "roi-tratamientos.html: empty state missing data-i18n='roiTrat.empty'"


def test_roi_trat_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'roiTrat.title', 'roiTrat.subtitle',
        'roiTrat.bestRoi', 'roiTrat.worstRoi',
        'roiTrat.recommendation', 'roiTrat.empty',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_roi_trat_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'roiTrat.title', 'roiTrat.subtitle',
        'roiTrat.bestRoi', 'roiTrat.worstRoi',
        'roiTrat.recommendation', 'roiTrat.empty',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── soil-history.html ─────────────────────────────────────────────────────────

def test_soil_hist_title_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.title'), \
        "soil-history.html: <h1> missing data-i18n='soilHist.title'"


def test_soil_hist_subtitle_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.subtitle'), \
        "soil-history.html: subtitle <p> missing data-i18n='soilHist.subtitle'"


def test_soil_hist_update_btn_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.updateBtn'), \
        "soil-history.html: 'Actualizar' button missing data-i18n='soilHist.updateBtn'"


def test_soil_hist_stat_samples_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.statSamples'), \
        "soil-history.html: 'Muestras' stat label missing data-i18n='soilHist.statSamples'"


def test_soil_hist_stat_ph_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.statPh'), \
        "soil-history.html: 'Ultimo pH' stat label missing data-i18n='soilHist.statPh'"


def test_soil_hist_stat_om_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.statOm'), \
        "soil-history.html: 'Materia Organica %' stat label missing data-i18n='soilHist.statOm'"


def test_soil_hist_stat_n_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.statN'), \
        "soil-history.html: 'Nitrogeno (ppm)' stat label missing data-i18n='soilHist.statN'"


def test_soil_hist_chart_ph_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.chartPh'), \
        "soil-history.html: 'pH del Suelo' chart title missing data-i18n='soilHist.chartPh'"


def test_soil_hist_chart_om_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.chartOm'), \
        "soil-history.html: 'Materia Organica (%)' chart title missing data-i18n='soilHist.chartOm'"


def test_soil_hist_chart_npk_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.chartNpk'), \
        "soil-history.html: 'Nutrientes NPK (ppm)' chart title missing data-i18n='soilHist.chartNpk'"


def test_soil_hist_table_title_has_data_i18n():
    html = _html('soil-history.html')
    assert _has_attr(html, 'soilHist.tableTitle'), \
        "soil-history.html: 'Registros de Analisis' section title missing data-i18n='soilHist.tableTitle'"


def test_soil_hist_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'soilHist.title', 'soilHist.subtitle', 'soilHist.updateBtn',
        'soilHist.statSamples', 'soilHist.statPh', 'soilHist.statOm', 'soilHist.statN',
        'soilHist.chartPh', 'soilHist.chartOm', 'soilHist.chartNpk', 'soilHist.tableTitle',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_soil_hist_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'soilHist.title', 'soilHist.subtitle', 'soilHist.updateBtn',
        'soilHist.statSamples', 'soilHist.statPh', 'soilHist.statOm', 'soilHist.statN',
        'soilHist.chartPh', 'soilHist.chartOm', 'soilHist.chartNpk', 'soilHist.tableTitle',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── soil-import.html ──────────────────────────────────────────────────────────

def test_soil_import_title_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.title'), \
        "soil-import.html: <h1> missing data-i18n='soilImport.title'"


def test_soil_import_subtitle_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.subtitle'), \
        "soil-import.html: subtitle <p> missing data-i18n='soilImport.subtitle'"


def test_soil_import_step1_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.step1'), \
        "soil-import.html: step 1 h2 missing data-i18n='soilImport.step1'"


def test_soil_import_step2_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.step2'), \
        "soil-import.html: step 2 h2 missing data-i18n='soilImport.step2'"


def test_soil_import_step3_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.step3'), \
        "soil-import.html: step 3 h2 missing data-i18n='soilImport.step3'"


def test_soil_import_farm_label_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.farmLabel'), \
        "soil-import.html: 'Granja' label missing data-i18n='soilImport.farmLabel'"


def test_soil_import_field_label_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.fieldLabel'), \
        "soil-import.html: 'Parcela' label missing data-i18n='soilImport.fieldLabel'"


def test_soil_import_file_btn_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.fileBtn'), \
        "soil-import.html: file label 'Seleccionar archivo' missing data-i18n='soilImport.fileBtn'"


def test_soil_import_import_btn_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.importBtn'), \
        "soil-import.html: 'Importar Datos' button missing data-i18n='soilImport.importBtn'"


def test_soil_import_results_title_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.resultsTitle'), \
        "soil-import.html: 'Resultado de Importacion' h2 missing data-i18n='soilImport.resultsTitle'"


def test_soil_import_imported_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.imported'), \
        "soil-import.html: 'Registros importados' label missing data-i18n='soilImport.imported'"


def test_soil_import_skipped_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.skipped'), \
        "soil-import.html: 'Duplicados omitidos' label missing data-i18n='soilImport.skipped'"


def test_soil_import_errors_label_has_data_i18n():
    html = _html('soil-import.html')
    assert _has_attr(html, 'soilImport.errors'), \
        "soil-import.html: 'Filas con errores' label missing data-i18n='soilImport.errors'"


def test_soil_import_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'soilImport.title', 'soilImport.subtitle',
        'soilImport.step1', 'soilImport.step2', 'soilImport.step3',
        'soilImport.farmLabel', 'soilImport.fieldLabel',
        'soilImport.fileBtn', 'soilImport.importBtn',
        'soilImport.resultsTitle', 'soilImport.imported',
        'soilImport.skipped', 'soilImport.errors',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_soil_import_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'soilImport.title', 'soilImport.subtitle',
        'soilImport.step1', 'soilImport.step2', 'soilImport.step3',
        'soilImport.farmLabel', 'soilImport.fieldLabel',
        'soilImport.fileBtn', 'soilImport.importBtn',
        'soilImport.resultsTitle', 'soilImport.imported',
        'soilImport.skipped', 'soilImport.errors',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"


# ── yield.html ────────────────────────────────────────────────────────────────

def test_yield_title_has_data_i18n():
    html = _html('yield.html')
    assert _has_attr(html, 'yieldPred.title'), \
        "yield.html: <h1> missing data-i18n='yieldPred.title'"


def test_yield_subtitle_has_data_i18n():
    html = _html('yield.html')
    assert _has_attr(html, 'yieldPred.subtitle'), \
        "yield.html: subtitle <p> missing data-i18n='yieldPred.subtitle'"


def test_yield_predict_btn_has_data_i18n():
    html = _html('yield.html')
    assert _has_attr(html, 'yieldPred.predictBtn'), \
        "yield.html: 'Predecir' button missing data-i18n='yieldPred.predictBtn'"


def test_yield_stat_estimate_has_data_i18n():
    html = _html('yield.html')
    assert _has_attr(html, 'yieldPred.statEstimate'), \
        "yield.html: 'Estimacion (kg/ha)' stat label missing data-i18n='yieldPred.statEstimate'"


def test_yield_stat_range_has_data_i18n():
    html = _html('yield.html')
    assert _has_attr(html, 'yieldPred.statRange'), \
        "yield.html: 'Rango (min — max)' stat label missing data-i18n='yieldPred.statRange'"


def test_yield_stat_total_has_data_i18n():
    html = _html('yield.html')
    assert _has_attr(html, 'yieldPred.statTotal'), \
        "yield.html: 'Total Estimado (kg)' stat label missing data-i18n='yieldPred.statTotal'"


def test_yield_empty_has_data_i18n():
    html = _html('yield.html')
    assert _has_attr(html, 'yieldPred.empty'), \
        "yield.html: empty state missing data-i18n='yieldPred.empty'"


def test_yield_keys_in_i18n_es():
    i18n = _i18n()
    for key in (
        'yieldPred.title', 'yieldPred.subtitle', 'yieldPred.predictBtn',
        'yieldPred.statEstimate', 'yieldPred.statRange', 'yieldPred.statTotal',
        'yieldPred.empty',
    ):
        assert _has_key_es(i18n, key), f"i18n.js es block missing '{key}'"


def test_yield_keys_in_i18n_en():
    i18n = _i18n()
    for key in (
        'yieldPred.title', 'yieldPred.subtitle', 'yieldPred.predictBtn',
        'yieldPred.statEstimate', 'yieldPred.statRange', 'yieldPred.statTotal',
        'yieldPred.empty',
    ):
        assert _has_key_en(i18n, key), f"i18n.js en block missing '{key}'"
