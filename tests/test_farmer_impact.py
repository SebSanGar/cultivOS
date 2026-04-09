"""Tests for farmer impact summary at /impacto-agricultor."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import (
    Farm,
    FarmerFeedback,
    Field,
    HealthScore,
    TreatmentRecord,
)


def _seed_farm_with_impact(db):
    """Seed a farm with fields, health scores, treatments, and feedback."""
    farm = Farm(
        name="Rancho Impacto",
        state="Jalisco",
        total_hectares=100.0,
        created_at=datetime.utcnow() - timedelta(days=90),
    )
    db.add(farm)
    db.flush()

    field1 = Field(farm_id=farm.id, name="Parcela Maiz", hectares=40.0, crop_type="maiz")
    field2 = Field(farm_id=farm.id, name="Parcela Agave", hectares=60.0, crop_type="agave")
    db.add_all([field1, field2])
    db.flush()

    now = datetime.utcnow()

    # Health scores for field1: improving from 45 -> 68
    for i, score in enumerate([45.0, 50.0, 55.0, 62.0, 68.0]):
        db.add(HealthScore(
            field_id=field1.id,
            score=score,
            scored_at=now - timedelta(days=80 - i * 15),
        ))

    # Health scores for field2: slight decline 72 -> 70
    for i, score in enumerate([72.0, 71.0, 70.0]):
        db.add(HealthScore(
            field_id=field2.id,
            score=score,
            scored_at=now - timedelta(days=60 - i * 20),
        ))

    # Treatments for field1 — 3 recommendations, 2 applied
    t1 = TreatmentRecord(
        field_id=field1.id, health_score_used=45.0,
        problema="Bajo vigor", causa_probable="Deficiencia de nitrogeno",
        tratamiento="Composta organica 5t/ha", costo_estimado_mxn=2000,
        urgencia="alta", prevencion="Rotar con leguminosas",
        applied_at=now - timedelta(days=60),
    )
    t2 = TreatmentRecord(
        field_id=field1.id, health_score_used=55.0,
        problema="Estres hidrico", causa_probable="Riego insuficiente",
        tratamiento="Mulch organico 3cm", costo_estimado_mxn=1500,
        urgencia="media", prevencion="Acolchado permanente",
        applied_at=now - timedelta(days=30),
    )
    t3 = TreatmentRecord(
        field_id=field1.id, health_score_used=62.0,
        problema="Plagas menores", causa_probable="Aumento de temperatura",
        tratamiento="Neem foliar", costo_estimado_mxn=800,
        urgencia="baja", prevencion="Control biologico",
        applied_at=None,  # not applied yet
    )
    db.add_all([t1, t2, t3])
    db.flush()

    # Feedback on applied treatments
    db.add(FarmerFeedback(
        field_id=field1.id, treatment_id=t1.id,
        rating=4, worked=True, farmer_notes="Funciono bien",
    ))
    db.add(FarmerFeedback(
        field_id=field1.id, treatment_id=t2.id,
        rating=5, worked=True, farmer_notes="Excelente resultado",
    ))

    db.commit()
    return farm


def _seed_empty_farm(db):
    """Seed a farm with no fields, treatments, or health data."""
    farm = Farm(
        name="Rancho Vacio",
        state="Jalisco",
        total_hectares=20.0,
        created_at=datetime.utcnow() - timedelta(days=10),
    )
    db.add(farm)
    db.commit()
    return farm


# ── Service function tests ────────────────────────────────────────────


class TestComputeFarmerImpact:
    def test_computes_impact_with_data(self, db):
        farm = _seed_farm_with_impact(db)
        from cultivos.services.intelligence.analytics import compute_farmer_impact

        result = compute_farmer_impact(db, farm.id)
        assert result is not None
        assert result["farm_id"] == farm.id
        assert result["farm_name"] == "Rancho Impacto"
        assert result["days_since_onboard"] >= 89  # ~90 days
        assert result["total_fields"] == 2
        assert result["total_hectares"] == 100.0
        assert result["recommendations_received"] == 3
        assert result["treatments_applied"] == 2
        assert result["feedback_given"] == 2
        # Field1: 68-45=+23, Field2: 70-72=-2 -> avg = (23 + -2)/2 = 10.5
        assert result["avg_health_improvement_pct"] == 10.5
        # 2 applied treatments * 1500 = 3000
        assert result["estimated_savings_mxn"] == 3000
        assert len(result["fields"]) == 2

    def test_field_entries_contain_health_data(self, db):
        farm = _seed_farm_with_impact(db)
        from cultivos.services.intelligence.analytics import compute_farmer_impact

        result = compute_farmer_impact(db, farm.id)
        fields = {f["field_name"]: f for f in result["fields"]}

        maiz = fields["Parcela Maiz"]
        assert maiz["first_score"] == 45.0
        assert maiz["latest_score"] == 68.0
        assert maiz["health_delta"] == 23.0
        assert maiz["treatments_applied"] == 2
        assert maiz["crop_type"] == "maiz"

        agave = fields["Parcela Agave"]
        assert agave["first_score"] == 72.0
        assert agave["latest_score"] == 70.0
        assert agave["health_delta"] == -2.0
        assert agave["treatments_applied"] == 0

    def test_empty_farm_returns_zeros(self, db):
        farm = _seed_empty_farm(db)
        from cultivos.services.intelligence.analytics import compute_farmer_impact

        result = compute_farmer_impact(db, farm.id)
        assert result is not None
        assert result["farm_name"] == "Rancho Vacio"
        assert result["total_fields"] == 0
        assert result["recommendations_received"] == 0
        assert result["treatments_applied"] == 0
        assert result["feedback_given"] == 0
        assert result["avg_health_improvement_pct"] is None
        assert result["estimated_savings_mxn"] == 0
        assert result["fields"] == []

    def test_nonexistent_farm_returns_none(self, db):
        from cultivos.services.intelligence.analytics import compute_farmer_impact

        result = compute_farmer_impact(db, 99999)
        assert result is None


# ── API endpoint tests ────────────────────────────────────────────────


class TestFarmerImpactEndpoint:
    def test_get_farmer_impact_returns_200(self, client, db):
        farm = _seed_farm_with_impact(db)
        resp = client.get(f"/api/farms/{farm.id}/farmer-impact")
        assert resp.status_code == 200
        data = resp.json()
        assert data["farm_id"] == farm.id
        assert data["farm_name"] == "Rancho Impacto"
        assert data["recommendations_received"] == 3
        assert data["treatments_applied"] == 2
        assert len(data["fields"]) == 2

    def test_get_farmer_impact_404_missing_farm(self, client):
        resp = client.get("/api/farms/99999/farmer-impact")
        assert resp.status_code == 404

    def test_get_farmer_impact_empty_farm(self, client, db):
        farm = _seed_empty_farm(db)
        resp = client.get(f"/api/farms/{farm.id}/farmer-impact")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_fields"] == 0
        assert data["estimated_savings_mxn"] == 0

    def test_response_matches_pydantic_schema(self, client, db):
        farm = _seed_farm_with_impact(db)
        resp = client.get(f"/api/farms/{farm.id}/farmer-impact")
        data = resp.json()
        required_keys = {
            "farm_id", "farm_name", "days_since_onboard", "total_fields",
            "total_hectares", "recommendations_received", "treatments_applied",
            "feedback_given", "avg_health_improvement_pct", "estimated_savings_mxn",
            "fields",
        }
        assert required_keys.issubset(data.keys())

    def test_multiple_farms_independent(self, client, db):
        farm1 = _seed_farm_with_impact(db)
        farm2 = _seed_empty_farm(db)
        resp1 = client.get(f"/api/farms/{farm1.id}/farmer-impact")
        resp2 = client.get(f"/api/farms/{farm2.id}/farmer-impact")
        assert resp1.json()["recommendations_received"] == 3
        assert resp2.json()["recommendations_received"] == 0


# ── Frontend page tests ──────────────────────────────────────────────


class TestFarmerImpactPage:
    def test_page_loads_200(self, client):
        resp = client.get("/impacto-agricultor")
        assert resp.status_code == 200

    def test_page_has_spanish_title(self, client):
        resp = client.get("/impacto-agricultor")
        text = resp.text
        assert "Impacto" in text

    def test_page_has_farm_selector(self, client):
        resp = client.get("/impacto-agricultor")
        assert "farmSelect" in resp.text or "farm-select" in resp.text

    def test_page_has_impact_containers(self, client):
        resp = client.get("/impacto-agricultor")
        text = resp.text
        assert "days-onboard" in text or "daysOnboard" in text or "dias" in text.lower()

    def test_page_has_field_cards_container(self, client):
        resp = client.get("/impacto-agricultor")
        assert "field-cards" in resp.text or "fieldCards" in resp.text

    def test_page_references_js(self, client):
        resp = client.get("/impacto-agricultor")
        assert "impacto-agricultor.js" in resp.text

    def test_page_has_stats_strip(self, client):
        resp = client.get("/impacto-agricultor")
        assert "stats-strip" in resp.text or "stats" in resp.text.lower()

    def test_js_file_loads(self, client):
        resp = client.get("/impacto-agricultor.js")
        assert resp.status_code == 200
