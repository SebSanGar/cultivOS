"""Tests for GET /api/farms/{farm_id}/fields/{field_id}/alertas-criticas — voice-ready critical alerts."""

from datetime import datetime, timedelta


class TestFieldAlertasCriticas:
    """Field-level critical/high alert list in Spanish."""

    def _seed(self, db, farm_name="Rancho Don Manuel", field_name="Norte"):
        from cultivos.db.models import Farm, Field

        farm = Farm(
            name=farm_name, owner_name="Manuel",
            location_lat=20.6, location_lon=-103.3,
            total_hectares=30, municipality="Zapopan", state="Jalisco",
        )
        db.add(farm)
        db.flush()

        field = Field(
            farm_id=farm.id, name=field_name, crop_type="maiz",
            hectares=8, planted_at=datetime.utcnow() - timedelta(days=30),
        )
        db.add(field)
        db.flush()
        return farm, field

    def test_key_schema(self, client, db):
        farm, field = self._seed(db)
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/alertas-criticas")
        assert r.status_code == 200
        body = r.json()
        assert "field_name" in body
        assert "total" in body
        assert "alertas" in body

    def test_no_alerts_empty(self, client, db):
        farm, field = self._seed(db)
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/alertas-criticas")
        body = r.json()
        assert body["total"] == 0
        assert body["alertas"] == []

    def test_unknown_farm_404(self, client, db):
        r = client.get("/api/farms/9999/fields/1/alertas-criticas")
        assert r.status_code == 404

    def test_unknown_field_404(self, client, db):
        farm, _ = self._seed(db)
        db.commit()
        r = client.get(f"/api/farms/{farm.id}/fields/9999/alertas-criticas")
        assert r.status_code == 404

    def test_critical_and_high_included(self, client, db):
        from cultivos.db.models import AlertLog

        farm, field = self._seed(db)
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Plaga severa", severity="critical", acknowledged=False,
        ))
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="pest",
            message="Mosca blanca", severity="high", acknowledged=False,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/alertas-criticas")
        body = r.json()
        assert body["total"] == 2
        assert len(body["alertas"]) == 2
        severities = {a["severity"] for a in body["alertas"]}
        assert severities == {"critical", "high"}
        for a in body["alertas"]:
            assert "alert_id" in a
            assert "mensaje_es" in a

    def test_low_severity_excluded(self, client, db):
        from cultivos.db.models import AlertLog

        farm, field = self._seed(db)
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Nota informativa", severity="info", acknowledged=False,
        ))
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Atención menor", severity="warning", acknowledged=False,
        ))
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Plaga severa", severity="critical", acknowledged=False,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/alertas-criticas")
        body = r.json()
        assert body["total"] == 1
        assert body["alertas"][0]["severity"] == "critical"

    def test_acknowledged_excluded(self, client, db):
        from cultivos.db.models import AlertLog

        farm, field = self._seed(db)
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Ya atendida", severity="critical", acknowledged=True,
        ))
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="pest",
            message="Pendiente", severity="critical", acknowledged=False,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/alertas-criticas")
        body = r.json()
        assert body["total"] == 1
        assert "Pendiente" in body["alertas"][0]["mensaje_es"]

    def test_mensaje_es_spanish_sentence(self, client, db):
        from cultivos.db.models import AlertLog

        farm, field = self._seed(db)
        db.add(AlertLog(
            farm_id=farm.id, field_id=field.id, alert_type="health",
            message="Estrés hídrico detectado", severity="critical",
            acknowledged=False,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/fields/{field.id}/alertas-criticas")
        body = r.json()
        msg = body["alertas"][0]["mensaje_es"]
        assert "salud" in msg.lower() or "alerta" in msg.lower()
        assert len(msg) > 10
