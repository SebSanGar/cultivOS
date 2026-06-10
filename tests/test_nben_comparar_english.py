"""NB-EN: comparar.html + comparar.js — English coverage tests."""
import pytest


# ── comparar.html — page-level ─────────────────────────────────────────────

def test_page_title_is_english(client):
    resp = client.get("/comparar")
    assert resp.status_code == 200
    assert "Compare Farms" in resp.text or "Farm Comparison" in resp.text


def test_html_lang_is_english(client):
    resp = client.get("/comparar")
    assert 'lang="en"' in resp.text


def test_meta_description_is_english(client):
    resp = client.get("/comparar")
    # No Spanish in meta description
    assert "lado a lado" not in resp.text
    assert "granjas" not in resp.text.lower().split("<title>")[0]


def test_no_comparar_granjas_heading(client):
    """H1 should say 'Compare Farms' not 'Comparar Granjas'."""
    resp = client.get("/comparar")
    assert "Comparar Granjas" not in resp.text


def test_compare_button_is_english(client):
    resp = client.get("/comparar")
    assert ">Compare<" in resp.text or 'value="Compare"' in resp.text or ">Compare</button>" in resp.text


def test_farm_selectors_labels_english(client):
    """'Granja 1', 'Granja 2', 'Granja 3' → 'Farm 1', 'Farm 2', 'Farm 3'."""
    resp = client.get("/comparar")
    assert "Farm 1" in resp.text
    assert "Farm 2" in resp.text
    assert "Farm 3" in resp.text
    assert "Granja 1" not in resp.text
    assert "Granja 2" not in resp.text
    assert "Granja 3" not in resp.text


def test_select_placeholder_is_english(client):
    """'Seleccione...' → 'Select...'"""
    resp = client.get("/comparar")
    assert "Seleccione" not in resp.text
    assert "Select" in resp.text or "-- None --" in resp.text or "None" in resp.text


def test_comparison_summary_panel_english(client):
    """'Resumen Comparativo' → 'Comparison Summary'."""
    resp = client.get("/comparar")
    assert "Resumen Comparativo" not in resp.text
    assert "Comparison" in resp.text


def test_chart_titles_english(client):
    """Chart panel titles should be English."""
    resp = client.get("/comparar")
    assert "Salud Promedio" not in resp.text
    assert "Historial de Salud" not in resp.text
    assert "Rendimiento Total" not in resp.text


def test_empty_state_english(client):
    """Empty state instructions in English."""
    resp = client.get("/comparar")
    assert "Seleccione al menos" not in resp.text


def test_nav_links_english(client):
    """Nav tabs should use English labels."""
    resp = client.get("/comparar")
    assert ">Granjas<" not in resp.text
    assert ">Inteligencia<" not in resp.text
    assert ">Clima<" not in resp.text
    assert ">Resumen<" not in resp.text
    assert ">Estado<" not in resp.text


def test_logout_link_english(client):
    """'Salir' → 'Log out' or 'Logout'."""
    resp = client.get("/comparar")
    assert ">Salir<" not in resp.text


def test_footer_is_english(client):
    resp = client.get("/comparar")
    assert "Agricultura de precision" not in resp.text
    assert "Transformando la agricultura" not in resp.text
    assert "Recorrido" not in resp.text


# ── comparar.js — JS strings ─────────────────────────────────────────────

def test_js_trend_map_english(client):
    """TREND_MAP values should be English."""
    resp = client.get("/comparar.js")
    assert resp.status_code == 200
    assert "Mejorando" not in resp.text
    assert "Estable" not in resp.text
    assert "Declinando" not in resp.text
    assert "Improving" in resp.text
    assert "Stable" in resp.text
    assert "Declining" in resp.text


def test_js_loading_state_english(client):
    """'Cargando...' → 'Loading...'"""
    resp = client.get("/comparar.js")
    assert "Cargando" not in resp.text
    assert "Loading" in resp.text


def test_js_compare_button_text_english(client):
    """Button reset text 'Comparar' → 'Compare'."""
    resp = client.get("/comparar.js")
    assert "'Compare'" in resp.text or '"Compare"' in resp.text


def test_js_alert_message_english(client):
    """Alert message in English."""
    resp = client.get("/comparar.js")
    assert "Seleccione al menos 2 granjas" not in resp.text
    assert "Select at least 2 farms" in resp.text or "least 2 farms" in resp.text


def test_js_table_metrics_english(client):
    """Table metric labels in English."""
    resp = client.get("/comparar.js")
    assert "Campos" not in resp.text
    assert "Hectareas" not in resp.text
    assert "Tratamientos" not in resp.text
    assert "Alertas" not in resp.text
    assert "Fields" in resp.text
    assert "Hectares" in resp.text
    assert "Treatments" in resp.text
    assert "Alerts" in resp.text


def test_js_chart_labels_english(client):
    """Chart axis labels in English."""
    resp = client.get("/comparar.js")
    assert "Medicion" not in resp.text
    assert "Measurement" in resp.text or "Reading" in resp.text or "Record" in resp.text


def test_js_no_spanish_metric_labels(client):
    """None of the Spanish metric labels remain in JS."""
    resp = client.get("/comparar.js")
    spanish_labels = ["Salud Promedio", "Rendimiento", "Materia Organica", "Carbono", "Completitud Datos"]
    for label in spanish_labels:
        assert label not in resp.text, f"Spanish label still present: {label}"


def test_js_yield_chart_label_english(client):
    resp = client.get("/comparar.js")
    assert "Rendimiento Total" not in resp.text
    assert "Total Yield" in resp.text or "Yield" in resp.text
