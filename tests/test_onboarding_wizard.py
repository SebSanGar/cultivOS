"""Tests for onboarding wizard page — multi-step farm creation flow."""

import pytest


# ── Page loads ───────────────────────────────────────────────────────


def test_onboarding_page_loads(client):
    """GET /onboarding returns 200."""
    resp = client.get("/onboarding")
    assert resp.status_code == 200


def test_onboarding_has_title(client):
    """Page has the wizard title in Spanish."""
    resp = client.get("/onboarding")
    assert "Nueva Granja" in resp.text


def test_onboarding_has_step_indicators(client):
    """Page has step indicator elements."""
    resp = client.get("/onboarding")
    assert "wizard-progress-step" in resp.text


def test_onboarding_has_three_steps(client):
    """Page has exactly 3 step indicators."""
    resp = client.get("/onboarding")
    assert "wizard-prog-1" in resp.text
    assert "wizard-prog-2" in resp.text
    assert "wizard-prog-3" in resp.text


# ── Step navigation ──────────────────────────────────────────────────


def test_onboarding_js_loads(client):
    """JS file for onboarding loads."""
    resp = client.get("/onboarding.js")
    assert resp.status_code == 200


def test_onboarding_js_has_step_navigation(client):
    """JS contains step navigation functions."""
    resp = client.get("/onboarding.js")
    js = resp.text
    assert "nextStep" in js
    assert "prevStep" in js


def test_onboarding_js_has_submit(client):
    """JS contains farm creation submission."""
    resp = client.get("/onboarding.js")
    assert "finishWizard" in resp.text


def test_onboarding_js_has_add_field(client):
    """JS contains add field function."""
    resp = client.get("/onboarding.js")
    assert "addField" in resp.text


# ── Form elements ────────────────────────────────────────────────────


def test_onboarding_has_farm_name_input(client):
    """Step 1 has farm name input."""
    resp = client.get("/onboarding")
    assert 'id="wizard-farm-name"' in resp.text


def test_onboarding_has_field_section(client):
    """Step 2 has field addition section."""
    resp = client.get("/onboarding")
    assert 'id="wizard-fields"' in resp.text


def test_onboarding_has_crop_type_in_js(client):
    """Wizard JS includes crop type handling for fields."""
    resp = client.get("/onboarding.js")
    assert "crop" in resp.text.lower()


def test_onboarding_has_finish_button(client):
    """Wizard has a finish/complete button."""
    resp = client.get("/onboarding")
    assert "Finalizar" in resp.text


# ── CSS ──────────────────────────────────────────────────────────────


def test_styles_has_wizard_classes(client):
    """styles.css has wizard-specific styles."""
    resp = client.get("/styles.css")
    assert resp.status_code == 200
    assert "wizard" in resp.text


# ── API integration ──────────────────────────────────────────────────


def test_onboarding_js_calls_farms_api(client):
    """JS calls POST /api/farms."""
    resp = client.get("/onboarding.js")
    assert "/api/farms" in resp.text


def test_onboarding_js_calls_fields_api(client):
    """JS calls fields endpoint."""
    resp = client.get("/onboarding.js")
    assert "/fields" in resp.text


def test_onboarding_js_has_crop_loading(client):
    """JS loads crop types from API."""
    resp = client.get("/onboarding.js")
    assert "/api/knowledge/crops" in resp.text


def test_onboarding_js_has_summary_rendering(client):
    """JS has summary rendering for confirmation step."""
    resp = client.get("/onboarding.js")
    assert "wizard-summary" in resp.text


def test_onboarding_js_has_remove_field(client):
    """JS has ability to remove a field entry."""
    resp = client.get("/onboarding.js")
    assert "removeField" in resp.text
