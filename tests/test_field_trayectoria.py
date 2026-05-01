"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/trayectoria-semana — 7-day Spanish trajectory."""

import pytest
from datetime import datetime, timedelta


class TestFieldTrayectoriaSemana:
    """Field 7-day Spanish trajectory endpoint."""

    def _seed_farm_field(self, db):
        from cultivos.db.models import Farm, Field

        farm = Farm(
            name="Rancho Don Manuel", owner_name="Manuel",
            location_lat=20.6, location_lon=-103.3,
            total_hectares=30, municipality="Zapopan", state="Jalisco",
        )
        db.add(farm)
        db.flush()

        field = Field(
            farm_id=farm.id, name="Parcela Norte", crop_type="maiz",
            hectares=8, planted_at=datetime.utcnow() - timedelta(days=30),
        )
        db.add(field)
        db.flush()
        return farm, field

    def test_happy_improving(self, client, db):
        from cultivos.db.models import HealthScore

        farm, field = self._seed_farm_field(db)
        now = datetime.utcnow()
        db.add(HealthScore(
            field_id=field.id, score=60.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 60},
            scored_at=now - timedelta(days=6),
        ))
        db.add(HealthScore(
            field_id=field.id, score=72.0, trend="improving",
            sources=["ndvi"], breakdown={"ndvi": 72},
            scored_at=now - timedelta(hours=2),
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/trayectoria-semana")
        assert r.status_code == 200
        body = r.json()
        assert body["field_name"] == "Parcela Norte"
        assert body["days_window"] == 7
        assert body["health_delta"] == pytest.approx(12.0)
        assert body["trend"] == "mejorando"
        assert "Tendencia positiva" in body["narrativa_es"]
        assert "+12" in body["narrativa_es"]

    def test_healthy_stable(self, client, db):
        from cultivos.db.models import HealthScore

        farm, field = self._seed_farm_field(db)
        now = datetime.utcnow()
        db.add(HealthScore(
            field_id=field.id, score=80.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 80},
            scored_at=now - timedelta(days=5),
        ))
        db.add(HealthScore(
            field_id=field.id, score=81.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 81},
            scored_at=now - timedelta(hours=1),
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/trayectoria-semana")
        body = r.json()
        assert body["trend"] == "estable"
        assert body["health_delta"] == pytest.approx(1.0)
        assert "Estado estable" in body["narrativa_es"]

    def test_no_data_sin_datos(self, client, db):
        farm, field = self._seed_farm_field(db)
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/trayectoria-semana")
        body = r.json()
        assert body["trend"] == "sin_datos"
        assert body["health_delta"] is None
        assert body["alerts_count"] == 0
        assert body["treatments_count"] == 0
        assert "No hay datos suficientes" in body["narrativa_es"]

    def test_unknown_farm_404(self, client, db):
        r = client.get("/api/farms/9999/fields/1/trayectoria-semana")
        assert r.status_code == 404

    def test_unknown_field_404(self, client, db):
        farm, _ = self._seed_farm_field(db)
        db.commit()
        r = client.get(f"/api/farms/{farm.id}/fields/9999/trayectoria-semana")
        assert r.status_code == 404

    def test_alerts_counted_7d_window(self, client, db):
        from cultivos.db.models import AlertLog, HealthScore

        farm, field = self._seed_farm_field(db)
        now = datetime.utcnow()
        db.add(HealthScore(
            field_id=field.id, score=65.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 65},
            scored_at=now - timedelta(days=3),
        ))
        # Alert within 7 days — should be counted
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Estres detectado", severity="warning",
            acknowledged=False, created_at=now - timedelta(days=2),
        ))
        # Alert outside 7 days — should NOT be counted
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Vieja alerta", severity="critical",
            acknowledged=False, created_at=now - timedelta(days=10),
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/trayectoria-semana")
        body = r.json()
        assert body["alerts_count"] == 1

    def test_treatments_counted_7d_window(self, client, db):
        from cultivos.db.models import HealthScore, TreatmentRecord

        farm, field = self._seed_farm_field(db)
        now = datetime.utcnow()
        db.add(HealthScore(
            field_id=field.id, score=50.0, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 50},
            scored_at=now - timedelta(days=5),
        ))
        db.add(HealthScore(
            field_id=field.id, score=44.0, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 44},
            scored_at=now - timedelta(hours=3),
        ))
        # Treatment applied within 7 days — counted
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=50.0,
            problema="Estres", causa_probable="Riego",
            tratamiento="Riego goteo", costo_estimado_mxn=500,
            urgencia="media", prevencion="Monitorear", organic=True,
            applied_at=now - timedelta(days=1),
        ))
        # Treatment applied outside 7 days — NOT counted
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=45.0,
            problema="Plagas", causa_probable="Temporal",
            tratamiento="Neem", costo_estimado_mxn=300,
            urgencia="baja", prevencion="Monitorear", organic=True,
            applied_at=now - timedelta(days=15),
        ))
        # Pending treatment (applied_at=None) — NOT counted
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=44.0,
            problema="Estres", causa_probable="Calor",
            tratamiento="Sombra", costo_estimado_mxn=200,
            urgencia="alta", prevencion="Monitorear", organic=True,
            applied_at=None,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/trayectoria-semana")
        body = r.json()
        assert body["treatments_count"] == 1
        assert body["trend"] == "empeorando"
        assert "Atencion" in body["narrativa_es"] or "Atención" in body["narrativa_es"]
