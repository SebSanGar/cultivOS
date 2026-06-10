"""NB-EN: cerebro-analytics.html + cerebro-analytics.js — English coverage tests."""


# ── cerebro-analytics.html ────────────────────────────────────────────────

def test_html_lang_is_english(client):
    resp = client.get("/cerebro-analytics")
    assert resp.status_code == 200
    assert 'lang="en"' in resp.text


def test_page_title_is_english(client):
    resp = client.get("/cerebro-analytics")
    assert "Cerebro" in resp.text  # brand stays
    assert "Analytics" in resp.text


def test_meta_description_is_english(client):
    resp = client.get("/cerebro-analytics")
    assert "Panel de analitica" not in resp.text
    assert "decisiones, precision" not in resp.text


def test_subtitle_is_english(client):
    """'Decisiones de IA, precision...' → English."""
    resp = client.get("/cerebro-analytics")
    assert "Decisiones de IA" not in resp.text
    assert "motor inteligente" not in resp.text


def test_stat_labels_english(client):
    """Stat strip labels in English."""
    resp = client.get("/cerebro-analytics")
    assert "Total Decisiones" not in resp.text
    assert "Recomendaciones" not in resp.text
    assert "Granjas Cubiertas" not in resp.text
    assert "Tasa de Exito" not in resp.text
    assert "Decisions" in resp.text or "Total" in resp.text


def test_empty_state_english(client):
    resp = client.get("/cerebro-analytics")
    assert "No hay datos" not in resp.text
    assert "todavia" not in resp.text


def test_nav_links_english(client):
    resp = client.get("/cerebro-analytics")
    assert ">Granjas<" not in resp.text
    assert ">Inteligencia<" not in resp.text
    assert ">Recomendaciones<" not in resp.text
    assert ">Notificaciones<" not in resp.text
    assert ">Estado<" not in resp.text


def test_logout_english(client):
    resp = client.get("/cerebro-analytics")
    assert ">Salir<" not in resp.text


def test_chart_section_english(client):
    """Chart card title in English."""
    resp = client.get("/cerebro-analytics")
    assert "Decisiones por Dia" not in resp.text


def test_decisions_by_type_section_english(client):
    resp = client.get("/cerebro-analytics")
    assert "Decisiones por Tipo" not in resp.text


def test_accuracy_section_english(client):
    resp = client.get("/cerebro-analytics")
    assert "Precision y Retroalimentacion" not in resp.text


def test_footer_is_english(client):
    resp = client.get("/cerebro-analytics")
    assert "Agricultura de precision" not in resp.text
    assert "Transformando la agricultura" not in resp.text


# ── cerebro-analytics.js ─────────────────────────────────────────────────

def test_js_chart_label_english(client):
    """Daily chart dataset label 'Decisiones' → 'Decisions'."""
    resp = client.get("/cerebro-analytics.js")
    assert resp.status_code == 200
    assert "'Decisiones'" not in resp.text
    assert '"Decisiones"' not in resp.text
    assert "Decisions" in resp.text


def test_js_decision_type_rows_english(client):
    """renderDecisionsByType row labels in English."""
    resp = client.get("/cerebro-analytics.js")
    assert "Evaluaciones de Salud" not in resp.text
    assert "Recomendaciones de Tratamiento" not in resp.text
    assert "Analisis NDVI" not in resp.text
    assert "Analisis Termal" not in resp.text
    assert "Alertas Generadas" not in resp.text
    assert "Health" in resp.text
    assert "Treatment" in resp.text
    assert "Alerts" in resp.text


def test_js_accuracy_labels_english(client):
    """renderAccuracy stat labels in English."""
    resp = client.get("/cerebro-analytics.js")
    assert "Tasa de Retroalimentacion" not in resp.text
    assert "Total Retroalimentaciones" not in resp.text
    assert "Retroalimentaciones Recibidas" not in resp.text
    assert "Feedback" in resp.text or "Positive" in resp.text


def test_js_no_spanish_stat_labels(client):
    """No remaining Spanish labels in JS."""
    resp = client.get("/cerebro-analytics.js")
    spanish = ["Granjas Cubiertas", "Tasa de Exito", "Analisis"]
    for s in spanish:
        assert s not in resp.text, f"Spanish still present: {s}"
