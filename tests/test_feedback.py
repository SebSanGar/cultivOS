"""Tests for farmer feedback loop — treatment ratings + TEK validation."""

from datetime import datetime, timedelta

import pytest


@pytest.fixture
def farm_field(client, admin_headers, db):
    """Create a farm and field for feedback tests."""
    resp = client.post("/api/farms", json={
        "name": "Finca Retroalimentacion", "owner_name": "Luis"
    }, headers=admin_headers)
    farm_id = resp.json()["id"]
    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Maiz", "crop_type": "maiz", "hectares": 5.0
    }, headers=admin_headers)
    field_id = resp.json()["id"]
    return farm_id, field_id


@pytest.fixture
def treatment_with_feedback(client, admin_headers, farm_field, db):
    """Create a health score + treatment for the field so we can submit feedback."""
    from cultivos.db.models import HealthScore, TreatmentRecord
    farm_id, field_id = farm_field
    # Create a health score directly in DB
    hs = HealthScore(field_id=field_id, score=45.0, trend="declining",
                     sources=["ndvi"], breakdown={"ndvi": 45.0}, scored_at=datetime.utcnow())
    db.add(hs)
    db.flush()
    # Create a treatment record
    tr = TreatmentRecord(
        field_id=field_id, health_score_used=45.0,
        problema="Bajo NDVI", causa_probable="Deficiencia de nitrogeno",
        tratamiento="Aplicar composta", costo_estimado_mxn=500,
        urgencia="alta", prevencion="Rotacion con leguminosas", organic=True,
        ancestral_method_name="Milpa",
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return farm_id, field_id, tr.id


def test_post_feedback_success(client, admin_headers, treatment_with_feedback):
    """POST feedback on a treatment returns 201 with saved data."""
    farm_id, field_id, treatment_id = treatment_with_feedback
    url = f"/api/farms/{farm_id}/fields/{field_id}/feedback"
    resp = client.post(url, json={
        "treatment_id": treatment_id,
        "rating": 4,
        "worked": True,
        "farmer_notes": "Funciono muy bien con la composta",
        "alternative_method": "Mi abuelo usaba ceniza de madera",
    }, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 4
    assert data["worked"] is True
    assert data["farmer_notes"] == "Funciono muy bien con la composta"
    assert data["alternative_method"] == "Mi abuelo usaba ceniza de madera"
    assert data["treatment_id"] == treatment_id
    assert "id" in data


def test_post_feedback_minimal(client, admin_headers, treatment_with_feedback):
    """POST feedback with only required fields (rating + worked)."""
    farm_id, field_id, treatment_id = treatment_with_feedback
    url = f"/api/farms/{farm_id}/fields/{field_id}/feedback"
    resp = client.post(url, json={
        "treatment_id": treatment_id,
        "rating": 2,
        "worked": False,
    }, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 2
    assert data["worked"] is False
    assert data["farmer_notes"] is None
    assert data["alternative_method"] is None


def test_post_feedback_invalid_rating(client, admin_headers, treatment_with_feedback):
    """Rating must be 1-5."""
    farm_id, field_id, treatment_id = treatment_with_feedback
    url = f"/api/farms/{farm_id}/fields/{field_id}/feedback"
    resp = client.post(url, json={
        "treatment_id": treatment_id,
        "rating": 6,
        "worked": True,
    }, headers=admin_headers)
    assert resp.status_code == 422


def test_post_feedback_treatment_not_found(client, admin_headers, farm_field):
    """Feedback on nonexistent treatment returns 404."""
    farm_id, field_id = farm_field
    url = f"/api/farms/{farm_id}/fields/{field_id}/feedback"
    resp = client.post(url, json={
        "treatment_id": 99999,
        "rating": 3,
        "worked": True,
    }, headers=admin_headers)
    assert resp.status_code == 404


def test_get_feedback_for_field(client, admin_headers, treatment_with_feedback):
    """GET returns all feedback for a field, most recent first."""
    farm_id, field_id, treatment_id = treatment_with_feedback
    url = f"/api/farms/{farm_id}/fields/{field_id}/feedback"
    # Submit two feedbacks
    client.post(url, json={
        "treatment_id": treatment_id, "rating": 5, "worked": True,
        "farmer_notes": "Excelente",
    }, headers=admin_headers)
    client.post(url, json={
        "treatment_id": treatment_id, "rating": 2, "worked": False,
        "farmer_notes": "No funciono",
    }, headers=admin_headers)
    resp = client.get(url, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_tek_validation_aggregation(client, admin_headers, treatment_with_feedback, db):
    """GET /api/intel/tek-validation aggregates feedback by ancestral method."""
    from cultivos.db.models import TreatmentRecord
    farm_id, field_id, treatment_id = treatment_with_feedback
    url = f"/api/farms/{farm_id}/fields/{field_id}/feedback"
    # Submit positive feedback for Milpa-linked treatment
    client.post(url, json={
        "treatment_id": treatment_id, "rating": 5, "worked": True,
    }, headers=admin_headers)
    client.post(url, json={
        "treatment_id": treatment_id, "rating": 4, "worked": True,
    }, headers=admin_headers)
    client.post(url, json={
        "treatment_id": treatment_id, "rating": 2, "worked": False,
    }, headers=admin_headers)

    resp = client.get("/api/intel/tek-validation", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "methods" in data
    assert len(data["methods"]) >= 1
    milpa = [m for m in data["methods"] if m["method_name"] == "Milpa"]
    assert len(milpa) == 1
    m = milpa[0]
    assert m["total_feedback"] == 3
    assert m["positive_count"] == 2
    assert m["average_rating"] == pytest.approx(3.67, abs=0.01)
    assert 0 <= m["trust_score"] <= 100


def test_tek_validation_empty(client, admin_headers):
    """TEK validation with no feedback returns empty methods list."""
    resp = client.get("/api/intel/tek-validation", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["methods"] == []
