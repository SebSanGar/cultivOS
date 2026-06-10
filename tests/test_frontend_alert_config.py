"""Tests for alert configuration UI on the farm dashboard."""


def test_dashboard_has_alert_config_gear_icon(client):
    """Dashboard HTML includes a gear icon button next to Notificaciones header."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="alert-config-btn"' in resp.text


def test_dashboard_has_alert_config_form(client):
    """Dashboard HTML includes a hidden alert config form with threshold inputs."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="alert-config-form"' in html
    assert 'id="cfg-health-floor"' in html
    assert 'id="cfg-ndvi-min"' in html
    assert 'id="cfg-temp-max"' in html


def test_dashboard_js_has_alert_config_functions(client):
    """Dashboard JS includes load, open, and save functions for alert config."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "loadAlertConfig" in js
    assert "toggleAlertConfig" in js
    assert "saveAlertConfig" in js


def test_dashboard_css_has_alert_config_styles(client):
    """Dashboard CSS includes alert config form styling."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    css = resp.text
    assert "alert-config" in css


def test_alert_config_form_has_labels_in_english(client):
    """Alert config form labels are in English (English-first farmer UI)."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "health" in html.lower()
    assert "NDVI" in html
    assert "temperature" in html.lower()


def test_alert_config_form_has_save_button(client):
    """Alert config form has a save button."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="alert-config-save"' in resp.text


def test_js_calls_alert_config_api(client):
    """JS loadAlertConfig fetches from /alert-config endpoint."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "/alert-config" in js


def test_js_saves_via_put(client):
    """JS saveAlertConfig sends PUT to update thresholds."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "PUT" in js
