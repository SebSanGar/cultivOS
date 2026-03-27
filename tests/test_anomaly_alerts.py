"""Tests for anomaly detection alerts — automated field health monitoring."""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult


# ---- Pure function tests ----


def test_anomaly_alert_created():
    """Health score drops >15 points between consecutive readings → anomaly detected."""
    from cultivos.services.intelligence.anomaly import detect_health_anomalies

    scores = [
        {"score": 75, "scored_at": datetime(2026, 3, 1)},
        {"score": 55, "scored_at": datetime(2026, 3, 15)},  # drop of 20
    ]
    anomalies = detect_health_anomalies(scores, field_name="Lote Norte")
    assert len(anomalies) == 1
    assert anomalies[0]["type"] == "health_drop"
    assert anomalies[0]["drop"] == 20
    assert anomalies[0]["field_name"] == "Lote Norte"


def test_ndvi_anomaly():
    """NDVI mean drops below field's historical average by >20% → anomaly detected."""
    from cultivos.services.intelligence.anomaly import detect_ndvi_anomalies

    ndvi_records = [
        {"ndvi_mean": 0.70, "analyzed_at": datetime(2026, 1, 1)},
        {"ndvi_mean": 0.72, "analyzed_at": datetime(2026, 2, 1)},
        {"ndvi_mean": 0.68, "analyzed_at": datetime(2026, 3, 1)},
        {"ndvi_mean": 0.50, "analyzed_at": datetime(2026, 3, 15)},  # 0.50 vs avg ~0.70 = ~29% drop
    ]
    anomalies = detect_ndvi_anomalies(ndvi_records, field_name="Lote Sur")
    assert len(anomalies) == 1
    assert anomalies[0]["type"] == "ndvi_drop"
    assert anomalies[0]["field_name"] == "Lote Sur"
    assert anomalies[0]["current_ndvi"] == 0.50
    assert anomalies[0]["historical_avg"] > 0.65


def test_alert_recommendations():
    """Anomaly alert includes suggested next action in Spanish."""
    from cultivos.services.intelligence.anomaly import detect_health_anomalies

    scores = [
        {"score": 80, "scored_at": datetime(2026, 3, 1)},
        {"score": 60, "scored_at": datetime(2026, 3, 15)},  # drop of 20
    ]
    anomalies = detect_health_anomalies(scores, field_name="Lote Norte")
    assert len(anomalies) == 1
    msg = anomalies[0]["recommendation"]
    # Must be in Spanish and action-oriented
    assert isinstance(msg, str)
    assert len(msg) > 10
    # Check it mentions the field name
    assert "Lote Norte" in msg


def test_no_false_positive():
    """Normal variation (<10 points health score change) → no anomaly."""
    from cultivos.services.intelligence.anomaly import detect_health_anomalies

    scores = [
        {"score": 75, "scored_at": datetime(2026, 3, 1)},
        {"score": 68, "scored_at": datetime(2026, 3, 15)},  # drop of 7 — normal
    ]
    anomalies = detect_health_anomalies(scores, field_name="Lote Norte")
    assert len(anomalies) == 0


# ---- API endpoint tests ----


def test_check_anomalies_endpoint(client, db, admin_headers):
    """POST /check-anomalies scans fields and creates alerts for detected anomalies."""
    # Create farm + field
    resp = client.post("/api/farms", json={
        "name": "Rancho Test", "owner_name": "Don Manuel",
        "location_lat": 20.5, "location_lon": -103.3,
        "total_hectares": 50, "municipality": "Zapopan",
    }, headers=admin_headers)
    farm_id = resp.json()["id"]

    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Lote Anomalia", "crop_type": "maiz", "hectares": 10,
    }, headers=admin_headers)
    field_id = resp.json()["id"]

    # Add two health scores — big drop
    now = datetime.utcnow()
    hs1 = HealthScore(
        field_id=field_id, score=80, trend="stable",
        sources=["ndvi"], breakdown={"ndvi": 80},
        scored_at=now - timedelta(days=14),
    )
    hs2 = HealthScore(
        field_id=field_id, score=55, trend="declining",
        sources=["ndvi"], breakdown={"ndvi": 55},
        scored_at=now,
    )
    db.add_all([hs1, hs2])
    db.commit()

    resp = client.post(f"/api/farms/{farm_id}/alerts/check-anomalies", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["fields_checked"] >= 1
    assert len(data["alerts_created"]) >= 1
    assert data["alerts_created"][0]["alert_type"] == "anomaly_health_drop"


def test_check_anomalies_no_alert_normal_variation(client, db, admin_headers):
    """POST /check-anomalies creates no alert for normal score variation."""
    resp = client.post("/api/farms", json={
        "name": "Rancho Estable", "owner_name": "Dona Maria",
        "location_lat": 20.5, "location_lon": -103.3,
        "total_hectares": 30, "municipality": "Tlajomulco",
    }, headers=admin_headers)
    farm_id = resp.json()["id"]

    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Lote Normal", "crop_type": "frijol", "hectares": 5,
    }, headers=admin_headers)
    field_id = resp.json()["id"]

    now = datetime.utcnow()
    hs1 = HealthScore(
        field_id=field_id, score=75, trend="stable",
        sources=["ndvi"], breakdown={"ndvi": 75},
        scored_at=now - timedelta(days=14),
    )
    hs2 = HealthScore(
        field_id=field_id, score=70, trend="stable",
        sources=["ndvi"], breakdown={"ndvi": 70},
        scored_at=now,
    )
    db.add_all([hs1, hs2])
    db.commit()

    resp = client.post(f"/api/farms/{farm_id}/alerts/check-anomalies", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["alerts_created"]) == 0


def test_check_anomalies_ndvi_drop(client, db, admin_headers):
    """POST /check-anomalies detects NDVI drop below historical average."""
    resp = client.post("/api/farms", json={
        "name": "Rancho NDVI", "owner_name": "Don Pedro",
        "location_lat": 20.5, "location_lon": -103.3,
        "total_hectares": 40, "municipality": "Tonala",
    }, headers=admin_headers)
    farm_id = resp.json()["id"]

    resp = client.post(f"/api/farms/{farm_id}/fields", json={
        "name": "Lote NDVI", "crop_type": "agave", "hectares": 8,
    }, headers=admin_headers)
    field_id = resp.json()["id"]

    now = datetime.utcnow()
    # Historical NDVI records — good values
    for i in range(3):
        ndvi = NDVIResult(
            field_id=field_id, ndvi_mean=0.70, ndvi_std=0.05,
            ndvi_min=0.50, ndvi_max=0.85, pixels_total=1000,
            stress_pct=10.0, zones=[],
            analyzed_at=now - timedelta(days=60 - i * 20),
        )
        db.add(ndvi)

    # Latest NDVI — big drop
    ndvi_bad = NDVIResult(
        field_id=field_id, ndvi_mean=0.45, ndvi_std=0.10,
        ndvi_min=0.20, ndvi_max=0.60, pixels_total=1000,
        stress_pct=40.0, zones=[],
        analyzed_at=now,
    )
    db.add(ndvi_bad)
    db.commit()

    resp = client.post(f"/api/farms/{farm_id}/alerts/check-anomalies", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Should have at least one NDVI anomaly alert
    ndvi_alerts = [a for a in data["alerts_created"] if a["alert_type"] == "anomaly_ndvi_drop"]
    assert len(ndvi_alerts) >= 1
