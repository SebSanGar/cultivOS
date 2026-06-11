"""AB2 — intel.html + intelligence.html i18n (B3 AUDIT_PLAN_2026-06-10).

intelligence.html was hardcoded lang=es with all Spanish content.
intel.html was English but had zero data-i18n attributes.
These tests assert the fixes: English default + data-i18n on both pages.
"""
from pathlib import Path

HTML_INT = Path("frontend/intelligence.html").read_text()
HTML_INTEL = Path("frontend/intel.html").read_text()
JS_PAGE = Path("frontend/intelligence-page.js").read_text()
I18N = Path("frontend/i18n.js").read_text()


# ── intelligence.html: lang attr ─────────────────────────────────────────────

def test_intelligence_lang_attr_is_en():
    assert 'lang="en"' in HTML_INT


def test_intelligence_no_lang_es():
    assert 'lang="es"' not in HTML_INT


# ── intelligence.html: title / h1 ────────────────────────────────────────────

def test_intelligence_title_english():
    assert "Intelligence" in HTML_INT or "Field Intelligence" in HTML_INT


def test_intelligence_h1_english():
    import re
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", HTML_INT, re.DOTALL)
    assert h1, "No h1 found"
    assert "Intelligence" in h1.group(1) or "Field" in h1.group(1)


def test_intelligence_no_inteligencia_de_campo():
    """Spanish title must be gone."""
    assert "Inteligencia de Campo Completa" not in HTML_INT


# ── intelligence.html: nav ────────────────────────────────────────────────────

def test_intelligence_nav_farms_english():
    assert ">Farms<" in HTML_INT or 'data-i18n' in HTML_INT


def test_intelligence_no_granjas_nav():
    assert ">Granjas<" not in HTML_INT


def test_intelligence_no_salir_nav():
    assert ">Salir<" not in HTML_INT


# ── intelligence.html: stat labels ────────────────────────────────────────────

def test_intelligence_stat_health_english():
    assert ">Health<" in HTML_INT or "Health</div>" in HTML_INT or 'data-i18n="intelligence.statHealth"' in HTML_INT


def test_intelligence_stat_risk_english():
    assert ">Risk<" in HTML_INT or "Risk</div>" in HTML_INT or 'data-i18n="intelligence.statRisk"' in HTML_INT


def test_intelligence_stat_treatments_english():
    assert ">Treatments<" in HTML_INT or 'data-i18n="intelligence.statTreatments"' in HTML_INT


def test_intelligence_no_salud_stat():
    assert ">Salud<" not in HTML_INT


def test_intelligence_no_riesgo_stat():
    assert ">Riesgo<" not in HTML_INT


# ── intelligence.html: button + selects ───────────────────────────────────────

def test_intelligence_button_english():
    assert "Load Intelligence" in HTML_INT or "Consult" in HTML_INT or 'data-i18n="intelligence.loadBtn"' in HTML_INT


def test_intelligence_no_consultar_inteligencia():
    assert "Consultar Inteligencia" not in HTML_INT


def test_intelligence_select_farm_english():
    assert "Select a farm" in HTML_INT or "Select farm" in HTML_INT or 'data-i18n="intelligence.selectFarm"' in HTML_INT


def test_intelligence_no_seleccione_una_granja():
    assert "Seleccione una granja..." not in HTML_INT


def test_intelligence_no_seleccione_un_campo():
    assert "Seleccione un campo..." not in HTML_INT


# ── intelligence.html: section headers ────────────────────────────────────────

def test_intelligence_section_thermal_english():
    assert "Thermal" in HTML_INT


def test_intelligence_no_section_termico():
    assert ">Termico<" not in HTML_INT


def test_intelligence_section_microbiome_english():
    assert "Microbiome" in HTML_INT


def test_intelligence_no_section_microbioma():
    assert ">Microbioma<" not in HTML_INT


def test_intelligence_section_weather_english():
    assert "Weather" in HTML_INT


def test_intelligence_no_section_clima():
    # "Clima" as a section header (not in meta description)
    assert "<h3" not in HTML_INT or "Clima<" not in HTML_INT or ">Clima<" not in HTML_INT


def test_intelligence_section_yield_english():
    assert "Yield" in HTML_INT


def test_intelligence_section_disease_english():
    assert "Disease" in HTML_INT


def test_intelligence_section_growth_english():
    assert "Growth" in HTML_INT


# ── intelligence.html: empty state ───────────────────────────────────────────

def test_intelligence_empty_state_english():
    assert "Select a farm" in HTML_INT or "Select farm" in HTML_INT or "farm and a field" in HTML_INT


def test_intelligence_no_spanish_empty_state():
    assert "Seleccione una granja y un campo" not in HTML_INT


# ── intelligence.html: footer ─────────────────────────────────────────────────

def test_intelligence_footer_no_jalisco():
    assert "Agricultura de precision para Jalisco" not in HTML_INT


def test_intelligence_footer_no_transformando():
    assert "Transformando la agricultura" not in HTML_INT


# ── intelligence.html: data-i18n ─────────────────────────────────────────────

def test_intelligence_has_data_i18n():
    count = HTML_INT.count("data-i18n")
    assert count >= 8, f"intelligence.html has only {count} data-i18n attrs, expected >= 8"


# ── intelligence-page.js: no Spanish empty states ────────────────────────────

def test_js_no_sin_datos_salud():
    assert "Sin datos de salud" not in JS_PAGE


def test_js_no_sin_datos_ndvi():
    assert "Sin datos NDVI" not in JS_PAGE


def test_js_no_sin_datos_termicos():
    assert "Sin datos termicos" not in JS_PAGE


def test_js_no_sin_datos_suelo():
    assert "Sin datos de suelo" not in JS_PAGE


def test_js_no_sin_datos_microbioma():
    assert "Sin datos de microbioma" not in JS_PAGE


def test_js_no_sin_datos_clima():
    assert "Sin datos de clima" not in JS_PAGE


def test_js_no_prediccion():
    assert "Sin prediccion de rendimiento" not in JS_PAGE


def test_js_no_sin_tratamientos():
    assert "Sin tratamientos registrados" not in JS_PAGE


# ── intelligence-page.js: English empty states ───────────────────────────────

def test_js_english_no_health_data():
    assert "No health data" in JS_PAGE


def test_js_english_no_ndvi_data():
    assert "No NDVI data" in JS_PAGE


def test_js_english_trend_labels():
    assert "Improving" in JS_PAGE and "Stable" in JS_PAGE and "Declining" in JS_PAGE


def test_js_english_risk_labels():
    assert "High" in JS_PAGE and "Low" in JS_PAGE


def test_js_no_mejorando():
    assert '"Mejorando"' not in JS_PAGE


def test_js_no_declinando():
    assert '"Declinando"' not in JS_PAGE


# ── intel.html: data-i18n ─────────────────────────────────────────────────────

def test_intel_has_data_i18n():
    count = HTML_INTEL.count("data-i18n")
    assert count >= 5, f"intel.html has only {count} data-i18n attrs, expected >= 5"


# ── i18n.js: intelligence keys ────────────────────────────────────────────────

def test_i18n_has_intelligence_keys():
    assert '"intelligence.' in I18N or "intelligence." in I18N
