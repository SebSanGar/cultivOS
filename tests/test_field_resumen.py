"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/resumen — Spanish plain-language field summary."""

from datetime import datetime, timedelta


class TestFieldResumen:
    """Field Spanish plain-language summary endpoint."""

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

    def test_happy_path_healthy_field_no_alerts(self, client, db):
        from cultivos.db.models import HealthScore

        farm, field = self._seed_farm_field(db)
        db.add(HealthScore(
            field_id=field.id, score=78.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 78},
            scored_at=datetime.utcnow(),
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resumen")
        assert r.status_code == 200
        body = r.json()
        assert body["field_name"] == "Parcela Norte"
        assert body["health_status"] == "bueno"
        assert body["urgency"] == "ninguna"
        # three sentences, first names the field, third starts with "Siguiente paso"
        summary = body["summary_es"]
        assert "Parcela Norte" in summary
        assert "bueno" in summary
        assert "No hay problemas urgentes" in summary
        assert "Siguiente paso" in summary
        assert summary.count(".") >= 3

    def test_no_health_data_returns_sin_datos(self, client, db):
        farm, field = self._seed_farm_field(db)
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resumen")
        assert r.status_code == 200
        body = r.json()
        assert body["health_status"] == "sin_datos"
        assert body["urgency"] == "ninguna"
        assert "sin evaluar" in body["summary_es"]
        assert "continuar monitoreo" in body["summary_es"]

    def test_unknown_farm_404(self, client, db):
        r = client.get("/api/farms/9999/fields/1/resumen")
        assert r.status_code == 404

    def test_unknown_field_404(self, client, db):
        farm, _ = self._seed_farm_field(db)
        db.commit()
        r = client.get(f"/api/farms/{farm.id}/fields/9999/resumen")
        assert r.status_code == 404

    def test_critical_alert_raises_urgency_alta(self, client, db):
        from cultivos.db.models import HealthScore, AlertLog

        farm, field = self._seed_farm_field(db)
        db.add(HealthScore(
            field_id=field.id, score=45.0, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 45},
            scored_at=datetime.utcnow(),
        ))
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Salud critica", severity="critical", acknowledged=False,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resumen")
        assert r.status_code == 200
        body = r.json()
        assert body["health_status"] == "malo"
        assert body["urgency"] == "alta"
        assert "delicado" in body["summary_es"]
        assert "alerta" in body["summary_es"].lower()

    def test_acknowledged_alerts_ignored(self, client, db):
        from cultivos.db.models import HealthScore, AlertLog

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

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resumen")
        body = r.json()
        assert body["urgency"] == "ninguna"
        assert body["health_status"] == "regular"

    def test_pending_treatment_drives_next_step(self, client, db):
        from cultivos.db.models import HealthScore, TreatmentRecord

        farm, field = self._seed_farm_field(db)
        db.add(HealthScore(
            field_id=field.id, score=55.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 55},
            scored_at=datetime.utcnow(),
        ))
        db.add(TreatmentRecord(
            field_id=field.id, health_score_used=55.0,
            problema="Estres hidrico", causa_probable="Falta de riego",
            tratamiento="Aplicar riego por goteo en zona norte",
            costo_estimado_mxn=500, urgencia="alta",
            prevencion="Monitorear humedad", organic=True,
            applied_at=None,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/resumen")
        body = r.json()
        assert "Siguiente paso:" in body["summary_es"]
        assert "riego por goteo" in body["summary_es"].lower()
