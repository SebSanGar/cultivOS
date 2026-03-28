"""Tests for treatment effectiveness report — GET /api/intel/treatment-effectiveness-report.

Aggregate stats: group treatments by name, compute success rate from farmer feedback
+ health score delta, rank by composite score. Researcher-facing.
"""

from datetime import datetime

from cultivos.db.models import (
    Farm,
    FarmerFeedback,
    Field,
    HealthScore,
    TreatmentRecord,
)


def _seed_treatment_data(db, farm_name, fields):
    """Seed farm + fields + treatments + feedback + health scores.

    fields: list of dicts:
        name, crop_type, hectares,
        treatments: list of dicts:
            tratamiento, health_before, health_after (optional), feedback (optional dict: worked, rating)
    """
    farm = Farm(name=farm_name, owner_name="Test", total_hectares=100)
    db.add(farm)
    db.flush()

    for fd in fields:
        field = Field(
            farm_id=farm.id,
            name=fd["name"],
            crop_type=fd.get("crop_type", "maiz"),
            hectares=fd.get("hectares", 10.0),
        )
        db.add(field)
        db.flush()

        for i, tr_data in enumerate(fd.get("treatments", [])):
            tr = TreatmentRecord(
                field_id=field.id,
                health_score_used=tr_data["health_before"],
                problema="Deficiencia",
                causa_probable="Test",
                tratamiento=tr_data["tratamiento"],
                costo_estimado_mxn=500,
                urgencia="media",
                prevencion="Rotacion",
                organic=True,
                created_at=datetime(2026, 1, 1 + i),
            )
            db.add(tr)
            db.flush()

            # Health score BEFORE treatment
            db.add(HealthScore(
                field_id=field.id,
                score=tr_data["health_before"],
                trend="stable",
                sources=["ndvi"],
                breakdown={"ndvi": tr_data["health_before"]},
                scored_at=datetime(2026, 1, 1 + i),
            ))

            # Health score AFTER treatment (if provided)
            if tr_data.get("health_after") is not None:
                db.add(HealthScore(
                    field_id=field.id,
                    score=tr_data["health_after"],
                    trend="improving",
                    sources=["ndvi"],
                    breakdown={"ndvi": tr_data["health_after"]},
                    scored_at=datetime(2026, 2, 1 + i),
                ))

            # Farmer feedback (if provided)
            if "feedback" in tr_data:
                fb = FarmerFeedback(
                    field_id=field.id,
                    treatment_id=tr.id,
                    worked=tr_data["feedback"]["worked"],
                    rating=tr_data["feedback"]["rating"],
                )
                db.add(fb)

    db.commit()
    return farm


# ── Test 1: Aggregates across multiple farms ────────────────────────


def test_aggregates_across_multiple_farms(client, db, admin_headers):
    """Same treatment name used on different farms — aggregated into one entry."""
    _seed_treatment_data(db, "Rancho A", [
        {"name": "P1", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Composta", "health_before": 50, "health_after": 70,
             "feedback": {"worked": True, "rating": 5}},
        ]},
    ])
    _seed_treatment_data(db, "Rancho B", [
        {"name": "P2", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Composta", "health_before": 40, "health_after": 55,
             "feedback": {"worked": True, "rating": 4}},
        ]},
    ])

    resp = client.get("/api/intel/treatment-effectiveness-report", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()

    # "Composta" should appear exactly once (aggregated)
    composta = [e for e in data["treatments"] if e["tratamiento"] == "Composta"]
    assert len(composta) == 1
    entry = composta[0]
    assert entry["total_applications"] == 2
    assert entry["feedback_count"] == 2
    # Both worked → success rate = 100%
    assert entry["feedback_success_rate"] == 100.0
    # avg delta: (20 + 15) / 2 = 17.5
    assert entry["avg_health_delta"] == 17.5


# ── Test 2: Ranked by composite score ───────────────────────────────


def test_ranked_by_composite_score(client, db, admin_headers):
    """Results are ranked by composite score (feedback success + health delta), best first."""
    _seed_treatment_data(db, "Rancho", [
        {"name": "P1", "crop_type": "maiz", "treatments": [
            # Good treatment: high delta, positive feedback
            {"tratamiento": "Composta", "health_before": 40, "health_after": 80,
             "feedback": {"worked": True, "rating": 5}},
            # Bad treatment: no improvement, negative feedback
            {"tratamiento": "Te de platano", "health_before": 60, "health_after": 62,
             "feedback": {"worked": False, "rating": 2}},
        ]},
    ])

    resp = client.get("/api/intel/treatment-effectiveness-report", headers=admin_headers)
    data = resp.json()["treatments"]

    assert len(data) == 2
    # Best treatment should be first
    assert data[0]["tratamiento"] == "Composta"
    assert data[1]["tratamiento"] == "Te de platano"
    # Composite scores should be descending
    assert data[0]["composite_score"] > data[1]["composite_score"]


# ── Test 3: Treatments with no feedback ─────────────────────────────


def test_handles_treatments_with_no_feedback(client, db, admin_headers):
    """Treatments with no farmer feedback still appear with null feedback fields."""
    _seed_treatment_data(db, "Rancho", [
        {"name": "P1", "treatments": [
            {"tratamiento": "Composta", "health_before": 50, "health_after": 65},
            # no "feedback" key — no FarmerFeedback record
        ]},
    ])

    resp = client.get("/api/intel/treatment-effectiveness-report", headers=admin_headers)
    data = resp.json()

    assert len(data["treatments"]) == 1
    entry = data["treatments"][0]
    assert entry["tratamiento"] == "Composta"
    assert entry["total_applications"] == 1
    assert entry["feedback_count"] == 0
    assert entry["feedback_success_rate"] is None
    # Health delta still available even without feedback
    assert entry["avg_health_delta"] == 15.0


# ── Test 4: Filters by crop_type ────────────────────────────────────


def test_filters_by_crop_type(client, db, admin_headers):
    """Optional crop_type param filters to only treatments on matching fields."""
    _seed_treatment_data(db, "Rancho", [
        {"name": "Maiz field", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Composta", "health_before": 50, "health_after": 70,
             "feedback": {"worked": True, "rating": 5}},
        ]},
        {"name": "Agave field", "crop_type": "agave", "treatments": [
            {"tratamiento": "Composta", "health_before": 60, "health_after": 65,
             "feedback": {"worked": False, "rating": 2}},
        ]},
    ])

    # Filter to maiz only
    resp = client.get(
        "/api/intel/treatment-effectiveness-report?crop_type=maiz",
        headers=admin_headers,
    )
    data = resp.json()

    assert len(data["treatments"]) == 1
    entry = data["treatments"][0]
    assert entry["total_applications"] == 1
    assert entry["feedback_success_rate"] == 100.0
    assert entry["avg_health_delta"] == 20.0


# ── Test 5: Empty data returns empty list ───────────────────────────


def test_empty_data_returns_empty_list(client, db, admin_headers):
    """No treatments in DB returns empty treatments list."""
    resp = client.get("/api/intel/treatment-effectiveness-report", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["treatments"] == []
