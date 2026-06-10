"""NB-EN — Intelligence Dashboard (intel.html / intel.js) English coverage.

Asserts intel.html has English default strings and no key Spanish UI labels.
JS empty-state messages and CSV headers must also be English.
"""

import re
from pathlib import Path

HTML = Path("frontend/intel.html").read_text()
JS = Path("frontend/intel.js").read_text()


# ── HTML title / header ──────────────────────────────────────────────────────

def test_page_title_is_english():
    assert "Intelligence" in HTML


def test_page_h1_is_english():
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", HTML, re.DOTALL)
    assert h1, "No h1 found"
    assert "Intelligence" in h1.group(1)


def test_page_subtitle_is_english():
    assert "admin" in HTML.lower() or "cross" in HTML.lower() or "researcher" in HTML.lower()


def test_export_button_is_english():
    assert "Export CSV" in HTML


def test_add_farm_button_is_english():
    assert "Add Farm" in HTML or "New Farm" in HTML


# ── HTML stat strip labels ────────────────────────────────────────────────────

def test_stat_label_farms_is_english():
    assert "Farms</div>" in HTML or ">Farms<" in HTML


def test_stat_label_fields_is_english():
    assert "Fields</div>" in HTML or ">Fields<" in HTML


def test_stat_label_avg_health_is_english():
    assert "Avg Health" in HTML or "Average Health" in HTML or "Health</div>" in HTML


def test_stat_label_critical_field_is_english():
    assert "Critical" in HTML or "Critical Field" in HTML


# ── HTML panel titles ─────────────────────────────────────────────────────────

def test_panel_anomalies_is_english():
    assert "Anomalies" in HTML


def test_panel_soil_trends_is_english():
    assert "Soil Trends" in HTML


def test_panel_treatment_is_english():
    assert "Treatment Effectiveness" in HTML


def test_panel_economic_is_english():
    assert "Economic Impact" in HTML


def test_panel_carbon_is_english():
    assert "Carbon" in HTML


def test_panel_sensor_validation_is_english():
    assert "Sensor" in HTML


def test_panel_farm_map_is_english():
    assert "Farm Map" in HTML or "Map" in HTML


def test_panel_farm_comparison_is_english():
    assert "Farm Comparison" in HTML or "Comparison" in HTML


def test_panel_field_health_is_english():
    assert "Field Health" in HTML or "Health by Field" in HTML


# ── HTML compare table headers ────────────────────────────────────────────────

def test_compare_table_farm_header_is_english():
    assert ">Farm<" in HTML or "Farm</span>" in HTML


def test_compare_table_fields_header_is_english():
    assert ">Fields<" in HTML or "Fields</span>" in HTML


def test_compare_table_yield_header_is_english():
    assert "Yield" in HTML


# ── HTML Spanish absence ──────────────────────────────────────────────────────

def test_no_spanish_panel_de_inteligencia_h1():
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", HTML, re.DOTALL)
    assert h1
    assert "Panel de Inteligencia" not in h1.group(1)


def test_no_spanish_salir_nav():
    assert ">Salir<" not in HTML


def test_no_spanish_footer_jalisco():
    assert "Agricultura de precision para Jalisco" not in HTML


def test_no_spanish_footer_transformando():
    assert "Transformando la agricultura" not in HTML


def test_no_spanish_seleccione_granjas():
    assert "Seleccione granjas para comparar" not in HTML


def test_no_spanish_actualizar_datos():
    assert ">Actualizar Datos<" not in HTML


def test_no_spanish_exportar_csv_button():
    assert ">Exportar CSV<" not in HTML


# ── JS English presence ───────────────────────────────────────────────────────

def test_js_no_anomalies_is_english():
    assert "No anomalies" in JS or "no anomalies" in JS


def test_js_no_treatment_data_is_english():
    assert "No treatment" in JS or "no treatment" in JS


def test_js_no_comparison_data_is_english():
    assert "No comparison" in JS or "comparison data" in JS.lower()


def test_js_csv_headers_are_english():
    # CSV export headers should use English column names
    assert "'Farm'" in JS or '"Farm"' in JS


def test_js_loading_message_is_english():
    assert "Loading" in JS or "loading" in JS


# ── JS Spanish absence ────────────────────────────────────────────────────────

def test_js_no_sin_anomalias():
    assert "Sin anomalias detectadas" not in JS


def test_js_no_sin_datos_tratamientos():
    assert "Sin datos de tratamientos" not in JS


def test_js_no_granja_csv_header():
    # Old Spanish CSV header
    assert "'Granja'" not in JS and '"Granja"' not in JS


def test_js_no_no_hay_datos():
    assert "No hay datos de comparacion" not in JS
