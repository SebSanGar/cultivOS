"""Tests for C8 cooperative resumen-mensual endpoint.

GET /api/cooperatives/{coop_id}/resumen-mensual

Last 30-day Spanish narrative: farms count, avg health change, total treatments,
total alerts. One paragraph (<=300 chars) WhatsApp-ready.
Tests monkeypatch datetime for deterministic 30-day window.
"""

import pytest
from datetime import datetime, timedelta

from cultivos.db.models import (
    AlertLog, Cooperative, Farm, Field, HealthScore, TreatmentRecord,
)
from cultivos.services.intelligence import coop_resumen_mensual as svc


NOW = datetime(2026, 5, 1, 12, 0, 0)


@pytest.fixture
def coop(db):
    c = Cooperative(name="Cooperativa Mensual", state="Jalisco")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _farm(db, coop, name="Rancho"):
    f = Farm(
        name=name, owner_name="Test", state="Jalisco",
        total_hectares=50.0, cooperative_id=coop.id,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _field(db, farm, name="Parcela"):
    fld = Field(name=name, farm_id=farm.id, crop_type="maiz", hectares=10.0)
    db.add(fld)
    db.commit()
    db.refresh(fld)
    return fld


def _health(db, field, score, days_ago):
    hs = HealthScore(
        field_id=field.id, score=score,
        sources=["ndvi"], breakdown={},
        scored_at=NOW - timedelta(days=days_ago),
    )
    db.add(hs)
    db.commit()
    return hs


def _treatment(db, field, days_ago):
    tr = TreatmentRecord(
        field_id=field.id, health_score_used=50.0,
        problema="Estrés", causa_probable="Sequía",
        tratamiento="Riego", costo_estimado_mxn=500,
        urgencia="media", prevencion="Mulch",
        created_at=NOW - timedelta(days=days_ago),
    )
    db.add(tr)
    db.commit()
    return tr


def _alert(db, farm, field, days_ago, severity="warning"):
    al = AlertLog(
        farm_id=farm.id, field_id=field.id,
        alert_type="health", message="Test alert",
        severity=severity,
        created_at=NOW - timedelta(days=days_ago),
    )
    db.add(al)
    db.commit()
    return al


# --- Test cases ---


def test_schema_keys(db, coop):
    """Response has all required keys."""
    result = svc.compute_coop_resumen_mensual(coop, db, _now=NOW)
    assert "coop_name" in result
    assert "total_farms" in result
    assert "total_fields" in result
    assert "period_days" in result
    assert "avg_health_change" in result
    assert "total_treatments" in result
    assert "total_alerts" in result
    assert "resumen_es" in result


def test_no_farms(db, coop):
    """Cooperative with no farms returns zeros and descriptive message."""
    result = svc.compute_coop_resumen_mensual(coop, db, _now=NOW)
    assert result["total_farms"] == 0
    assert result["total_fields"] == 0
    assert result["total_treatments"] == 0
    assert result["total_alerts"] == 0
    assert result["avg_health_change"] is None
    assert "sin fincas" in result["resumen_es"].lower()


def test_no_activity(db, coop):
    """Farms with fields but no 30-day activity."""
    farm = _farm(db, coop, "Finca Vacía")
    _field(db, farm, "Campo 1")
    result = svc.compute_coop_resumen_mensual(coop, db, _now=NOW)
    assert result["total_farms"] == 1
    assert result["total_fields"] == 1
    assert result["total_treatments"] == 0
    assert result["total_alerts"] == 0
    assert result["avg_health_change"] is None


def test_happy_with_activity(db, coop):
    """Full activity: health scores, treatments, alerts within 30 days."""
    farm = _farm(db, coop, "Rancho Sol")
    fld = _field(db, farm, "Parcela Norte")

    _health(db, fld, 45.0, 25)
    _health(db, fld, 65.0, 5)
    _treatment(db, fld, 10)
    _treatment(db, fld, 3)
    _alert(db, farm, fld, 7)

    result = svc.compute_coop_resumen_mensual(coop, db, _now=NOW)
    assert result["total_farms"] == 1
    assert result["total_fields"] == 1
    assert result["total_treatments"] == 2
    assert result["total_alerts"] == 1
    assert result["avg_health_change"] == pytest.approx(20.0, abs=0.1)


def test_excludes_old_data(db, coop):
    """Data older than 30 days excluded from counts."""
    farm = _farm(db, coop, "Rancho Viejo")
    fld = _field(db, farm, "Parcela Antigua")

    _health(db, fld, 50.0, 40)
    _treatment(db, fld, 35)
    _alert(db, farm, fld, 45)
    _health(db, fld, 70.0, 5)

    result = svc.compute_coop_resumen_mensual(coop, db, _now=NOW)
    assert result["total_treatments"] == 0
    assert result["total_alerts"] == 0
    assert result["avg_health_change"] is None


def test_multi_farm_aggregation(db, coop):
    """Aggregates across multiple farms and fields."""
    farm_a = _farm(db, coop, "Finca A")
    farm_b = _farm(db, coop, "Finca B")
    fld_a1 = _field(db, farm_a, "A1")
    fld_b1 = _field(db, farm_b, "B1")

    _health(db, fld_a1, 40.0, 20)
    _health(db, fld_a1, 60.0, 2)
    _health(db, fld_b1, 70.0, 18)
    _health(db, fld_b1, 80.0, 1)
    _treatment(db, fld_a1, 5)
    _alert(db, farm_a, fld_a1, 3)
    _alert(db, farm_b, fld_b1, 8)

    result = svc.compute_coop_resumen_mensual(coop, db, _now=NOW)
    assert result["total_farms"] == 2
    assert result["total_fields"] == 2
    assert result["total_treatments"] == 1
    assert result["total_alerts"] == 2
    assert result["avg_health_change"] == pytest.approx(15.0, abs=0.1)


def test_resumen_max_300_chars(db, coop):
    """resumen_es never exceeds 300 characters."""
    farm = _farm(db, coop, "Cooperativa con nombre extremadamente largo para probar límite")
    fld = _field(db, farm, "Campo con nombre muy largo también")
    _health(db, fld, 30.0, 28)
    _health(db, fld, 80.0, 1)
    _treatment(db, fld, 5)
    _alert(db, farm, fld, 3)
    result = svc.compute_coop_resumen_mensual(coop, db, _now=NOW)
    assert len(result["resumen_es"]) <= 300


def test_unknown_coop_404(client, db):
    """GET with unknown coop_id returns 404."""
    resp = client.get("/api/cooperatives/9999/resumen-mensual")
    assert resp.status_code == 404
