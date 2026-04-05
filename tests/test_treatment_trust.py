"""Tests for treatment trust scores — aggregated farmer feedback per treatment."""

from datetime import datetime

import pytest


@pytest.fixture
def trust_data(client, admin_headers, db):
    """Create farms, fields, treatments, and feedback for trust score tests."""
    from cultivos.db.models import FarmerFeedback, HealthScore, TreatmentRecord

    # Farm + 2 fields (maiz, agave)
    resp = client.post("/api/farms", json={
        "name": "Finca Confianza", "owner_name": "Pedro",
    }, headers=admin_headers)
    farm_id = resp.json()["id"]

    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Maiz", "crop_type": "maiz", "hectares": 5.0,
    }, headers=admin_headers)
    maiz_field_id = resp.json()["id"]

    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Parcela Agave", "crop_type": "agave", "hectares": 3.0,
    }, headers=admin_headers)
    agave_field_id = resp.json()["id"]

    # Health scores for both fields
    for fid in [maiz_field_id, agave_field_id]:
        db.add(HealthScore(
            field_id=fid, score=50.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 50.0},
            scored_at=datetime.utcnow(),
        ))
    db.flush()

    # Treatment 1: "Aplicar composta" on maiz field
    tr1 = TreatmentRecord(
        field_id=maiz_field_id, health_score_used=50.0,
        problema="Bajo NDVI", causa_probable="Deficiencia de nitrogeno",
        tratamiento="Aplicar composta", costo_estimado_mxn=500,
        urgencia="alta", prevencion="Rotacion con leguminosas", organic=True,
    )
    # Treatment 2: "Aplicar composta" on agave field (same treatment name)
    tr2 = TreatmentRecord(
        field_id=agave_field_id, health_score_used=50.0,
        problema="Bajo NDVI", causa_probable="Deficiencia de nitrogeno",
        tratamiento="Aplicar composta", costo_estimado_mxn=500,
        urgencia="alta", prevencion="Rotacion con leguminosas", organic=True,
    )
    # Treatment 3: "Riego por goteo" on maiz field
    tr3 = TreatmentRecord(
        field_id=maiz_field_id, health_score_used=50.0,
        problema="Estres hidrico", causa_probable="Falta de agua",
        tratamiento="Riego por goteo", costo_estimado_mxn=2000,
        urgencia="media", prevencion="Monitoreo de humedad", organic=True,
    )
    db.add_all([tr1, tr2, tr3])
    db.flush()

    # Feedback for "Aplicar composta" on maiz — 2 positive, 1 negative
    db.add(FarmerFeedback(field_id=maiz_field_id, treatment_id=tr1.id, rating=5, worked=True, farmer_notes="Excelente"))
    db.add(FarmerFeedback(field_id=maiz_field_id, treatment_id=tr1.id, rating=4, worked=True))
    db.add(FarmerFeedback(field_id=maiz_field_id, treatment_id=tr1.id, rating=2, worked=False))

    # Feedback for "Aplicar composta" on agave — 1 positive
    db.add(FarmerFeedback(field_id=agave_field_id, treatment_id=tr2.id, rating=4, worked=True))

    # Feedback for "Riego por goteo" — all negative
    db.add(FarmerFeedback(field_id=maiz_field_id, treatment_id=tr3.id, rating=1, worked=False))
    db.add(FarmerFeedback(field_id=maiz_field_id, treatment_id=tr3.id, rating=2, worked=False))

    db.commit()
    return {
        "farm_id": farm_id,
        "maiz_field_id": maiz_field_id,
        "agave_field_id": agave_field_id,
        "tr1_id": tr1.id,
        "tr2_id": tr2.id,
        "tr3_id": tr3.id,
    }


# --- Pure function tests ---


def test_aggregate_treatment_trust_mixed_feedback(db, trust_data):
    """Aggregation returns trust scores grouped by treatment name."""
    from cultivos.services.intelligence.feedback_aggregation import aggregate_treatment_trust

    result = aggregate_treatment_trust(db)
    assert len(result) == 2  # two distinct treatments

    # "Aplicar composta" has 4 feedbacks (3 maiz + 1 agave), 3 positive
    composta = [t for t in result if t["treatment_name"] == "Aplicar composta"]
    assert len(composta) == 1
    c = composta[0]
    assert c["total_feedback"] == 4
    assert c["positive_count"] == 3
    assert c["negative_count"] == 1
    assert c["average_rating"] == pytest.approx(3.75, abs=0.01)
    assert 0 <= c["trust_score"] <= 100
    # Trust: (3/4 * 0.6 + (3.75-1)/4 * 0.4) * 100 = (0.75*0.6 + 0.6875*0.4)*100 = (0.45+0.275)*100 = 72.5
    assert c["trust_score"] == pytest.approx(72.5, abs=0.1)

    # "Riego por goteo" has 2 feedbacks, 0 positive
    riego = [t for t in result if t["treatment_name"] == "Riego por goteo"]
    assert len(riego) == 1
    r = riego[0]
    assert r["total_feedback"] == 2
    assert r["positive_count"] == 0
    assert r["negative_count"] == 2
    assert r["trust_score"] < 20  # low trust


def test_aggregate_treatment_trust_filter_by_crop(db, trust_data):
    """Filter by crop_type only includes feedback from fields with that crop."""
    from cultivos.services.intelligence.feedback_aggregation import aggregate_treatment_trust

    result = aggregate_treatment_trust(db, crop_type="agave")
    assert len(result) == 1
    assert result[0]["treatment_name"] == "Aplicar composta"
    assert result[0]["total_feedback"] == 1  # only agave field feedback


def test_aggregate_treatment_trust_filter_by_field(db, trust_data):
    """Filter by field_id only includes feedback from that specific field."""
    from cultivos.services.intelligence.feedback_aggregation import aggregate_treatment_trust

    maiz_id = trust_data["maiz_field_id"]
    result = aggregate_treatment_trust(db, field_id=maiz_id)
    assert len(result) == 2  # composta + riego on maiz field
    composta = [t for t in result if t["treatment_name"] == "Aplicar composta"]
    assert composta[0]["total_feedback"] == 3  # only maiz feedback


def test_aggregate_treatment_trust_empty(db):
    """No feedback returns empty list."""
    from cultivos.services.intelligence.feedback_aggregation import aggregate_treatment_trust

    result = aggregate_treatment_trust(db)
    assert result == []


def test_aggregate_treatment_trust_single_treatment(db, client, admin_headers):
    """Single treatment with single feedback."""
    from cultivos.db.models import FarmerFeedback, HealthScore, TreatmentRecord
    from cultivos.services.intelligence.feedback_aggregation import aggregate_treatment_trust

    resp = client.post("/api/farms", json={"name": "Solo", "owner_name": "Ana"}, headers=admin_headers)
    farm_id = resp.json()["id"]
    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Campo", "crop_type": "frijol", "hectares": 2.0,
    }, headers=admin_headers)
    field_id = resp.json()["id"]
    db.add(HealthScore(field_id=field_id, score=60.0, trend="stable",
                       sources=["ndvi"], breakdown={"ndvi": 60.0}, scored_at=datetime.utcnow()))
    db.flush()
    tr = TreatmentRecord(
        field_id=field_id, health_score_used=60.0,
        problema="Plaga", causa_probable="Mosca blanca",
        tratamiento="Neem", costo_estimado_mxn=300,
        urgencia="alta", prevencion="Monitoreo", organic=True,
    )
    db.add(tr)
    db.flush()
    db.add(FarmerFeedback(field_id=field_id, treatment_id=tr.id, rating=5, worked=True))
    db.commit()

    result = aggregate_treatment_trust(db)
    assert len(result) == 1
    assert result[0]["trust_score"] == pytest.approx(100.0, abs=0.1)


# --- API endpoint tests ---


def test_treatment_trust_endpoint(client, admin_headers, trust_data):
    """GET /api/intel/treatment-trust returns ranked treatments."""
    resp = client.get("/api/intel/treatment-trust", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "treatments" in data
    assert len(data["treatments"]) == 2
    # Sorted by trust_score descending
    assert data["treatments"][0]["trust_score"] >= data["treatments"][1]["trust_score"]
    # First should be "Aplicar composta" (higher trust)
    assert data["treatments"][0]["treatment_name"] == "Aplicar composta"


def test_treatment_trust_endpoint_crop_filter(client, admin_headers, trust_data):
    """GET /api/intel/treatment-trust?crop_type=agave filters by crop."""
    resp = client.get("/api/intel/treatment-trust?crop_type=agave", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["treatments"]) == 1
    assert data["treatments"][0]["treatment_name"] == "Aplicar composta"


def test_treatment_trust_endpoint_field_filter(client, admin_headers, trust_data):
    """GET /api/intel/treatment-trust?field_id=X filters by field."""
    maiz_id = trust_data["maiz_field_id"]
    resp = client.get(f"/api/intel/treatment-trust?field_id={maiz_id}", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["treatments"]) == 2


def test_treatment_trust_endpoint_empty(client, admin_headers):
    """No feedback returns empty treatments list."""
    resp = client.get("/api/intel/treatment-trust", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["treatments"] == []


def test_treatment_trust_response_fields(client, admin_headers, trust_data):
    """Each treatment has all expected fields."""
    resp = client.get("/api/intel/treatment-trust", headers=admin_headers)
    data = resp.json()
    t = data["treatments"][0]
    assert "treatment_name" in t
    assert "total_feedback" in t
    assert "positive_count" in t
    assert "negative_count" in t
    assert "average_rating" in t
    assert "trust_score" in t
    assert "top_farmer_note" in t
