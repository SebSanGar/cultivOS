"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/accion-siguiente — single Spanish action."""

from datetime import datetime, timedelta


class TestFieldAccionSiguiente:
    """Field one-sentence Spanish next-action endpoint."""

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

    def test_happy_no_data_returns_monitoring(self, client, db):
        farm, field = self._seed_farm_field(db)
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/accion-siguiente")
        assert r.status_code == 200
        body = r.json()
        assert body["field_name"] == "Parcela Norte"
        assert body["priority"] == "ninguna"
        assert body["source"] == "monitoring"
        assert "No hay acciones urgentes" in body["accion_es"]
        assert body["accion_es"].endswith(".")

    def test_healthy_field_returns_ninguna(self, client, db):
        from cultivos.db.models import HealthScore

        farm, field = self._seed_farm_field(db)
        db.add(HealthScore(
            field_id=field.id, score=82.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 82},
            scored_at=datetime.utcnow(),
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/accion-siguiente")
        body = r.json()
        assert body["priority"] == "ninguna"
        assert body["source"] == "monitoring"

    def test_unknown_farm_404(self, client, db):
        r = client.get("/api/farms/9999/fields/1/accion-siguiente")
        assert r.status_code == 404

    def test_unknown_field_404(self, client, db):
        farm, _ = self._seed_farm_field(db)
        db.commit()
        r = client.get(f"/api/farms/{farm.id}/fields/9999/accion-siguiente")
        assert r.status_code == 404

    def test_critical_alert_wins_over_treatment(self, client, db):
        from cultivos.db.models import AlertLog, HealthScore, TreatmentRecord

        farm, field = self._seed_farm_field(db)
        db.add(HealthScore(
            field_id=field.id, score=40.0, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 40},
            scored_at=datetime.utcnow(),
        ))
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=40.0,
            problema="Estres", causa_probable="Riego",
            tratamiento="Aplicar riego", costo_estimado_mxn=500,
            urgencia="media", prevencion="Monitorear", organic=True,
            applied_at=None,
        ))
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Salud critica detectada", severity="critical",
            acknowledged=False,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/accion-siguiente")
        body = r.json()
        assert body["priority"] == "alta"
        assert body["source"] == "alert"
        assert "Atender alerta critica" in body["accion_es"]
        assert "Salud critica detectada" in body["accion_es"]
        assert body["accion_es"].endswith(".")

    def test_pending_treatment_without_alert(self, client, db):
        from cultivos.db.models import TreatmentRecord

        farm, field = self._seed_farm_field(db)
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=55.0,
            problema="Estres hidrico", causa_probable="Falta riego",
            tratamiento="Aplicar riego por goteo", costo_estimado_mxn=500,
            urgencia="alta", prevencion="Monitorear", organic=True,
            applied_at=None,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/accion-siguiente")
        body = r.json()
        assert body["priority"] == "alta"
        assert body["source"] == "treatment"
        assert "Aplicar tratamiento" in body["accion_es"]
        assert "riego por goteo" in body["accion_es"].lower()

    def test_low_health_no_alert_no_treatment(self, client, db):
        from cultivos.db.models import HealthScore

        farm, field = self._seed_farm_field(db)
        db.add(HealthScore(
            field_id=field.id, score=42.0, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 42},
            scored_at=datetime.utcnow(),
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/accion-siguiente")
        body = r.json()
        assert body["priority"] == "media"
        assert body["source"] == "health"
        assert "Revisar el campo" in body["accion_es"]
        assert "42" in body["accion_es"]

    def test_acknowledged_alert_ignored(self, client, db):
        from cultivos.db.models import AlertLog, HealthScore

        farm, field = self._seed_farm_field(db)
        db.add(HealthScore(
            field_id=field.id, score=60.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 60},
            scored_at=datetime.utcnow(),
        ))
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Atendido", severity="critical", acknowledged=True,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/accion-siguiente")
        body = r.json()
        assert body["source"] != "alert"
        assert body["priority"] == "baja"
        assert body["source"] == "monitoring"
        assert "Monitorear" in body["accion_es"]
