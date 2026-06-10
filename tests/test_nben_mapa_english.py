"""NB-EN — Field Map page (mapa.html / mapa.js) English coverage."""

import re
from pathlib import Path

HTML = Path("frontend/mapa.html").read_text()
JS = Path("frontend/mapa.js").read_text()


# ── HTML title / header ──────────────────────────────────────────────────────

def test_page_title_is_english():
    assert "Field Map" in HTML or "Map" in HTML


def test_page_h1_is_english():
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", HTML, re.DOTALL)
    assert h1, "No h1 found"
    assert "Map" in h1.group(1)


def test_subtitle_is_english():
    assert "Farm" in HTML or "farm" in HTML


def test_farm_filter_all_farms_is_english():
    assert "All farms" in HTML


# ── HTML stat strip ───────────────────────────────────────────────────────────

def test_stat_farms_label_is_english():
    assert "Farms</div>" in HTML or ">Farms<" in HTML


def test_stat_fields_label_is_english():
    assert "Fields</div>" in HTML or ">Fields<" in HTML


def test_stat_hectares_label_is_english():
    assert "Hectares</div>" in HTML or ">Hectares<" in HTML


def test_stat_avg_health_label_is_english():
    assert "Avg Health" in HTML or "Average Health" in HTML


# ── HTML legend ───────────────────────────────────────────────────────────────

def test_legend_healthy_is_english():
    assert "Healthy" in HTML


def test_legend_alert_is_english():
    assert "Alert" in HTML


def test_legend_critical_is_english():
    assert "Critical" in HTML


def test_legend_no_data_is_english():
    assert "No data" in HTML


def test_legend_high_risk_is_english():
    assert "High Risk" in HTML or "High risk" in HTML


def test_legend_low_risk_is_english():
    assert "Low Risk" in HTML or "Low risk" in HTML


# ── HTML empty/info states ────────────────────────────────────────────────────

def test_empty_state_is_english():
    assert "No farms" in HTML or "no farms" in HTML or "registered" in HTML


def test_info_panel_is_english():
    assert "Click" in HTML or "click" in HTML


# ── HTML Spanish absence ──────────────────────────────────────────────────────

def test_no_spanish_mapa_de_campos_h1():
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", HTML, re.DOTALL)
    assert h1
    assert "Mapa de Campos" not in h1.group(1)


def test_no_spanish_granjas_nav():
    assert ">Granjas<" not in HTML


def test_no_spanish_salir():
    assert ">Salir<" not in HTML


def test_no_spanish_salud_promedio_label():
    assert "Salud Promedio</div>" not in HTML


def test_no_spanish_parcelas_label():
    assert "Parcelas</div>" not in HTML


def test_no_spanish_saludable_legend():
    assert "Saludable" not in HTML


def test_no_spanish_sin_datos_legend():
    assert "Sin datos" not in HTML


def test_no_spanish_no_hay_granjas():
    assert "No hay granjas" not in HTML


def test_no_spanish_haz_clic():
    assert "Haz clic" not in HTML


# ── JS English presence ───────────────────────────────────────────────────────

def test_js_no_data_label_is_english():
    assert "No data" in JS or "no data" in JS


def test_js_healthy_label_is_english():
    assert "Healthy" in JS or "healthy" in JS


def test_js_view_farm_link_is_english():
    assert "View farm" in JS or "view farm" in JS


def test_js_view_field_link_is_english():
    assert "View field" in JS or "view field" in JS


# ── JS Spanish absence ────────────────────────────────────────────────────────

def test_js_no_sin_datos():
    assert "'Sin datos'" not in JS and '"Sin datos"' not in JS


def test_js_no_saludable():
    assert "'Saludable'" not in JS and '"Saludable"' not in JS


def test_js_no_ver_granja():
    assert "'Ver granja'" not in JS and '"Ver granja"' not in JS
