"""Tests for per-crop treatment effectiveness comparison.

GET /api/intel/treatment-effectiveness-by-crop?crop=maiz

Simpler than /treatment-effectiveness-report:
- REQUIRES crop filter
- Ranks treatments by mean health delta desc
- Flags low-confidence entries (sample_count < 2)
- Cerebro's answer to "which treatment worked best for MY crop"
"""

from datetime import datetime

from cultivos.db.models import (
    Farm,
    Field,
    HealthScore,
    TreatmentRecord,
)


def _seed(db, farm_name, fields):
    farm = Farm(name=farm_name, owner_name="Test", total_hectares=100)
    db.add(farm)
    db.flush()
    for fd in fields:
        field = Field(
            farm_id=farm.id,
            name=fd["name"],
            crop_type=fd.get("crop_type", "maiz"),
            hectares=10.0,
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
            if tr_data.get("health_after") is not None:
                db.add(HealthScore(
                    field_id=field.id,
                    score=tr_data["health_after"],
                    trend="improving",
                    sources=["ndvi"],
                    breakdown={"ndvi": tr_data["health_after"]},
                    scored_at=datetime(2026, 2, 1 + i),
                ))
    db.commit()
    return farm


# ── Test 1: Filters to selected crop only ───────────────────────────

def test_filters_by_crop(client, db, admin_headers):
    """Only treatments on fields of the requested crop are counted."""
    _seed(db, "Rancho", [
        {"name": "Maizal", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Composta", "health_before": 50, "health_after": 70},
            {"tratamiento": "Composta", "health_before": 40, "health_after": 60},
        ]},
        {"name": "Agave lot", "crop_type": "agave", "treatments": [
            {"tratamiento": "Ceniza", "health_before": 55, "health_after": 80},
        ]},
    ])

    resp = client.get(
        "/api/intel/treatment-effectiveness-by-crop?crop=maiz",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["crop"] == "maiz"
    names = [t["tratamiento"] for t in data["treatments"]]
    assert "Composta" in names
    assert "Ceniza" not in names


# ── Test 2: Ranks treatments by mean health delta desc ──────────────

def test_ranks_by_mean_delta_desc(client, db, admin_headers):
    """Treatments sorted by mean health delta, best first."""
    # Each treatment on its own field so "next HealthScore after treatment"
    # doesn't pick up scores from a sibling treatment on the same field.
    _seed(db, "Rancho", [
        {"name": "F1", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Composta", "health_before": 50, "health_after": 70},
        ]},
        {"name": "F2", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Composta", "health_before": 40, "health_after": 60},
        ]},
        {"name": "F3", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Te de platano", "health_before": 60, "health_after": 65},
        ]},
        {"name": "F4", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Te de platano", "health_before": 50, "health_after": 55},
        ]},
    ])

    resp = client.get(
        "/api/intel/treatment-effectiveness-by-crop?crop=maiz",
        headers=admin_headers,
    )
    data = resp.json()["treatments"]
    assert len(data) == 2
    assert data[0]["tratamiento"] == "Composta"
    assert data[0]["mean_health_delta"] == 20.0
    assert data[0]["sample_count"] == 2
    assert data[0]["low_confidence"] is False
    assert data[1]["tratamiento"] == "Te de platano"
    assert data[1]["mean_health_delta"] == 5.0


# ── Test 3: Low-confidence flag when samples < 2 ────────────────────

def test_low_confidence_flag_for_single_sample(client, db, admin_headers):
    """Treatments with only one sample are flagged low_confidence."""
    _seed(db, "Rancho", [
        {"name": "F1", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Composta", "health_before": 50, "health_after": 70},
        ]},
        {"name": "F2", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Composta", "health_before": 40, "health_after": 55},
        ]},
        {"name": "F3", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Ajo", "health_before": 50, "health_after": 90},
        ]},
    ])

    resp = client.get(
        "/api/intel/treatment-effectiveness-by-crop?crop=maiz",
        headers=admin_headers,
    )
    data = {t["tratamiento"]: t for t in resp.json()["treatments"]}
    assert data["Composta"]["low_confidence"] is False
    assert data["Composta"]["sample_count"] == 2
    assert data["Ajo"]["low_confidence"] is True
    assert data["Ajo"]["sample_count"] == 1


# ── Test 4: Unknown crop returns empty list ─────────────────────────

def test_unknown_crop_returns_empty(client, db, admin_headers):
    _seed(db, "Rancho", [
        {"name": "F1", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Composta", "health_before": 50, "health_after": 70},
        ]},
    ])

    resp = client.get(
        "/api/intel/treatment-effectiveness-by-crop?crop=durian",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["crop"] == "durian"
    assert data["treatments"] == []


# ── Test 5: Missing crop param returns 422 ──────────────────────────

def test_missing_crop_param_is_required(client, db, admin_headers):
    resp = client.get(
        "/api/intel/treatment-effectiveness-by-crop",
        headers=admin_headers,
    )
    assert resp.status_code == 422


# ── Test 6: Treatments without a subsequent health score are excluded ──

def test_excludes_treatments_without_health_delta(client, db, admin_headers):
    """Treatments with no post-treatment HealthScore produce no delta and are excluded."""
    _seed(db, "Rancho", [
        {"name": "F1", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Composta", "health_before": 50, "health_after": 65},
        ]},
        {"name": "F2", "crop_type": "maiz", "treatments": [
            {"tratamiento": "Mulch", "health_before": 60, "health_after": None},
        ]},
    ])

    resp = client.get(
        "/api/intel/treatment-effectiveness-by-crop?crop=maiz",
        headers=admin_headers,
    )
    names = [t["tratamiento"] for t in resp.json()["treatments"]]
    assert "Composta" in names
    assert "Mulch" not in names
