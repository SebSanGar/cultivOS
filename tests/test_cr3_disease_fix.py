"""
CR3 — /enfermedades 'Identificar' verification + fixes.

Bugs found by manual review (crawler finding was partially real):
1. disease-field-select missing onchange="loadDiseaseRisk()" — risk never auto-loads on field change
2. identifyDisease() silently returns on empty input — no DOM feedback shown to user
3. dis.emptySymptoms key missing from i18n.js

Tests assert the FIX state: if any test fails, the bug is still present.
"""
import os
import re

import pytest

_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")


def _html(name):
    with open(os.path.join(_FRONTEND, name), encoding="utf-8") as f:
        return f.read()


def _js(name):
    with open(os.path.join(_FRONTEND, name), encoding="utf-8") as f:
        return f.read()


# ── Seed diseases for endpoint tests ─────────────────────────────────────────

@pytest.fixture(autouse=True)
def seed_disease_data(db):
    from cultivos.db.seeds import seed_diseases
    seed_diseases(db)


# ── disease.html structural checks ────────────────────────────────────────────


def test_field_select_has_onchange_load_risk():
    """disease-field-select must fire loadDiseaseRisk() on change."""
    html = _html("disease.html")
    assert 'id="disease-field-select"' in html, "disease-field-select element missing"
    pattern = r'id="disease-field-select"[^>]*onchange="loadDiseaseRisk\(\)"'
    assert re.search(pattern, html), (
        "disease-field-select is missing onchange='loadDiseaseRisk()' — "
        "disease risk never auto-loads when user selects a field"
    )


def test_farm_select_has_onchange_load_fields():
    """disease-farm-select must fire loadFieldsForDisease() on change (regression guard)."""
    html = _html("disease.html")
    assert 'onchange="loadFieldsForDisease()"' in html, (
        "disease-farm-select is missing onchange='loadFieldsForDisease()'"
    )


def test_identify_form_has_onsubmit():
    """disease-identify-form must have onsubmit='identifyDisease(event)' (regression guard)."""
    html = _html("disease.html")
    assert 'onsubmit="identifyDisease(event)"' in html, (
        "disease-identify-form is missing onsubmit='identifyDisease(event)'"
    )


# ── disease.js UX checks ──────────────────────────────────────────────────────


def test_empty_symptoms_shows_feedback():
    """identifyDisease() must update resultsEl when input is empty, not silently return."""
    js = _js("disease.js")
    assert "_t('dis.emptySymptoms'" in js or '_t("dis.emptySymptoms"' in js, (
        "disease.js: empty symptoms must show feedback via t('dis.emptySymptoms') — "
        "currently silently returns with no DOM update"
    )


def test_empty_symptoms_key_in_i18n():
    """i18n.js must have dis.emptySymptoms EN key for empty-input feedback."""
    js = _js("i18n.js")
    assert "dis.emptySymptoms" in js or "'emptySymptoms'" in js, (
        "i18n.js: missing dis.emptySymptoms key"
    )


# ── Backend endpoint: identify returns results with seed data ─────────────────


def test_identify_endpoint_200_with_symptoms(client):
    """POST /api/knowledge/diseases/identify returns 200 for known symptoms."""
    resp = client.post(
        "/api/knowledge/diseases/identify",
        json={"symptoms": ["manchas amarillas", "hojas secas"]},
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


def test_identify_endpoint_returns_matches_for_jalisco_symptoms(client):
    """identify returns at least 1 match for common Jalisco crop symptoms."""
    resp = client.post(
        "/api/knowledge/diseases/identify",
        json={"symptoms": ["manchas", "hojas amarillas", "marchitamiento"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1, (
        "Expected at least 1 disease match for 'manchas, hojas amarillas, marchitamiento'."
    )


def test_identify_endpoint_empty_symptoms_returns_empty(client):
    """POST with empty symptoms list returns [] — not 500."""
    resp = client.post(
        "/api/knowledge/diseases/identify",
        json={"symptoms": []},
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_identify_endpoint_response_shape(client):
    """Each match has name, confidence, symptoms_matched, severity."""
    resp = client.post(
        "/api/knowledge/diseases/identify",
        json={"symptoms": ["manchas", "hojas amarillas"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    if data:
        first = data[0]
        for key in ("name", "confidence", "symptoms_matched", "severity"):
            assert key in first, f"Missing key '{key}' in DiseaseMatch response"
