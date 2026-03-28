"""Tests for the farm dashboard summary panel — aggregate data shown when a farm is selected."""


def test_dashboard_summary_html_present(client):
    """Dashboard HTML contains the summary panel container."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="dashboard-summary"' in html
    assert "Resumen de Granja" in html


def test_dashboard_api_returns_aggregate_data(client, db):
    """GET /api/farms/{id}/dashboard returns overall_health and field count for summary panel."""
    from cultivos.db.models import Farm, Field, HealthScore
    from datetime import datetime

    farm = Farm(name="Finca Resumen", location_lat=20.5, location_lon=-103.3, total_hectares=100)
    db.add(farm)
    db.commit()
    db.refresh(farm)

    f1 = Field(farm_id=farm.id, name="Campo A", crop_type="maiz", hectares=40)
    f2 = Field(farm_id=farm.id, name="Campo B", crop_type="agave", hectares=60)
    db.add_all([f1, f2])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)

    hs1 = HealthScore(
        field_id=f1.id, score=80.0, trend="improving", sources=["ndvi"],
        breakdown={"ndvi": 80.0}, scored_at=datetime(2026, 3, 1),
    )
    hs2 = HealthScore(
        field_id=f2.id, score=60.0, trend="stable", sources=["ndvi"],
        breakdown={"ndvi": 60.0}, scored_at=datetime(2026, 3, 1),
    )
    db.add_all([hs1, hs2])
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_health"] == 70.0
    assert len(data["fields"]) == 2
    assert data["farm"]["total_hectares"] == 100


def test_dashboard_api_empty_farm_returns_nulls(client, db):
    """Empty farm returns null overall_health and empty fields — summary panel should handle gracefully."""
    from cultivos.db.models import Farm

    farm = Farm(name="Finca Vacia", location_lat=20.5, location_lon=-103.3)
    db.add(farm)
    db.commit()
    db.refresh(farm)

    resp = client.get(f"/api/farms/{farm.id}/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_health"] is None
    assert data["fields"] == []


def test_dashboard_summary_shows_correct_aggregates(client, db):
    """Dashboard summary should compute: total fields, avg health, total hectares, crop count."""
    from cultivos.db.models import Farm, Field, HealthScore
    from datetime import datetime

    farm = Farm(name="Finca Completa", location_lat=20.5, location_lon=-103.3, total_hectares=150)
    db.add(farm)
    db.commit()
    db.refresh(farm)

    f1 = Field(farm_id=farm.id, name="Norte", crop_type="maiz", hectares=50)
    f2 = Field(farm_id=farm.id, name="Sur", crop_type="agave", hectares=50)
    f3 = Field(farm_id=farm.id, name="Este", crop_type="maiz", hectares=50)
    db.add_all([f1, f2, f3])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)
    db.refresh(f3)

    for f, score in [(f1, 90.0), (f2, 60.0), (f3, 75.0)]:
        db.add(HealthScore(
            field_id=f.id, score=score, trend="stable", sources=["ndvi"],
            breakdown={"ndvi": score}, scored_at=datetime(2026, 3, 1),
        ))
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["fields"]) == 3
    assert data["overall_health"] == 75.0  # (90+60+75)/3
    # Fields sorted by urgency: lowest score first
    assert data["fields"][0]["latest_health_score"]["score"] == 60.0
    # Unique crops: maiz, agave
    crops = {f["crop_type"] for f in data["fields"]}
    assert crops == {"maiz", "agave"}


def test_dashboard_includes_treatment_count(client, db):
    """Dashboard summary includes total treatment count across all fields."""
    from cultivos.db.models import Farm, Field, TreatmentRecord
    from datetime import datetime

    farm = Farm(name="Finca Tratamientos", location_lat=20.5, location_lon=-103.3)
    db.add(farm)
    db.commit()
    db.refresh(farm)

    f1 = Field(farm_id=farm.id, name="Campo T1", crop_type="maiz", hectares=30)
    f2 = Field(farm_id=farm.id, name="Campo T2", crop_type="agave", hectares=40)
    db.add_all([f1, f2])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)

    # 3 treatments across 2 fields
    for field in [f1, f1, f2]:
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=65.0, problema="Plagas",
            causa_probable="Humedad alta", tratamiento="Neem",
            costo_estimado_mxn=500, urgencia="media", prevencion="Monitoreo",
            organic=True,
        ))
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert data["treatment_count"] == 3


def test_dashboard_includes_top_risk(client, db):
    """Dashboard summary includes the top risk field (lowest health score)."""
    from cultivos.db.models import Farm, Field, HealthScore
    from datetime import datetime

    farm = Farm(name="Finca Riesgo", location_lat=20.5, location_lon=-103.3)
    db.add(farm)
    db.commit()
    db.refresh(farm)

    f1 = Field(farm_id=farm.id, name="Campo Sano", crop_type="maiz", hectares=30)
    f2 = Field(farm_id=farm.id, name="Campo Enfermo", crop_type="agave", hectares=40)
    db.add_all([f1, f2])
    db.commit()
    db.refresh(f1)
    db.refresh(f2)

    db.add(HealthScore(
        field_id=f1.id, score=85.0, trend="stable", sources=["ndvi"],
        breakdown={"ndvi": 85.0}, scored_at=datetime(2026, 3, 1),
    ))
    db.add(HealthScore(
        field_id=f2.id, score=35.0, trend="declining", sources=["ndvi"],
        breakdown={"ndvi": 35.0}, scored_at=datetime(2026, 3, 1),
    ))
    db.commit()

    resp = client.get(f"/api/farms/{farm.id}/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert data["top_risk"] is not None
    assert data["top_risk"]["field_name"] == "Campo Enfermo"
    assert data["top_risk"]["score"] == 35.0
    assert data["top_risk"]["trend"] == "declining"


def test_dashboard_no_treatments_returns_zero(client, db):
    """Dashboard with no treatments returns treatment_count=0."""
    from cultivos.db.models import Farm

    farm = Farm(name="Finca Sin Tratamientos", location_lat=20.5, location_lon=-103.3)
    db.add(farm)
    db.commit()
    db.refresh(farm)

    resp = client.get(f"/api/farms/{farm.id}/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert data["treatment_count"] == 0
    assert data["top_risk"] is None


def test_dashboard_html_has_treatment_and_risk_elements(client):
    """Dashboard HTML contains treatment count and top risk elements."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="summary-treatments"' in html
    assert 'id="summary-top-risk"' in html
    assert "Tratamientos" in html
