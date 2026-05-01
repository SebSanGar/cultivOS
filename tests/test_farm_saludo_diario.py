"""Tests for GET /api/farms/{farm_id}/saludo-diario — daily Spanish WhatsApp greeting."""

from datetime import datetime, timedelta


class TestFarmSaludoDiario:
    """Farm-level daily Spanish greeting endpoint."""

    def _seed_farm(self, db, name="Rancho Don Manuel", n_fields=0, field_names=None):
        from cultivos.db.models import Farm, Field

        farm = Farm(
            name=name, owner_name="Manuel",
            location_lat=20.6, location_lon=-103.3,
            total_hectares=30, municipality="Zapopan", state="Jalisco",
        )
        db.add(farm)
        db.flush()

        fields = []
        if field_names is None:
            field_names = [f"Parcela {i + 1}" for i in range(n_fields)]
        for fname in field_names:
            f = Field(
                farm_id=farm.id, name=fname, crop_type="maiz",
                hectares=8, planted_at=datetime.utcnow() - timedelta(days=30),
            )
            db.add(f)
            db.flush()
            fields.append(f)
        return farm, fields

    def test_key_schema(self, client, db):
        farm, _ = self._seed_farm(db, n_fields=1)
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/saludo-diario")
        assert r.status_code == 200
        body = r.json()
        assert "farm_name" in body
        assert "weather_es" in body
        assert "open_alerts" in body
        assert "urgent_field" in body
        assert "saludo_es" in body

    def test_happy_all_ok(self, client, db):
        farm, _ = self._seed_farm(db, n_fields=2)
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/saludo-diario")
        assert r.status_code == 200
        body = r.json()
        assert body["farm_name"] == "Rancho Don Manuel"
        assert body["open_alerts"] == 0
        assert body["urgent_field"] is None
        assert "tranquilo" in body["saludo_es"].lower()
        assert len(body["saludo_es"]) <= 200

    def test_unknown_farm_404(self, client, db):
        r = client.get("/api/farms/9999/saludo-diario")
        assert r.status_code == 404

    def test_with_weather_data(self, client, db):
        from cultivos.db.models import WeatherRecord

        farm, _ = self._seed_farm(db, n_fields=1)
        db.add(WeatherRecord(
            farm_id=farm.id, temp_c=32.0, humidity_pct=75.0,
            description="soleado", wind_kmh=10.0, rainfall_mm=0.0,
            recorded_at=datetime.utcnow(),
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/saludo-diario")
        body = r.json()
        assert "32" in body["weather_es"] or "caluroso" in body["weather_es"]
        assert len(body["saludo_es"]) <= 200

    def test_with_open_alerts(self, client, db):
        from cultivos.db.models import AlertLog

        farm, fields = self._seed_farm(db, n_fields=1, field_names=["Norte"])
        db.add(AlertLog(
            farm_id=farm.id, field_id=fields[0].id, alert_type="health",
            message="Estrés hídrico", severity="warning", acknowledged=False,
        ))
        db.add(AlertLog(
            farm_id=farm.id, field_id=fields[0].id, alert_type="pest",
            message="Mosca blanca", severity="info", acknowledged=False,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/saludo-diario")
        body = r.json()
        assert body["open_alerts"] == 2
        assert "alerta" in body["saludo_es"].lower()

    def test_urgent_field_shown(self, client, db):
        from cultivos.db.models import AlertLog

        farm, fields = self._seed_farm(db, n_fields=2, field_names=["Norte", "Sur"])
        db.add(AlertLog(
            farm_id=farm.id, field_id=fields[1].id, alert_type="health",
            message="Plaga crítica", severity="critical", acknowledged=False,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/saludo-diario")
        body = r.json()
        assert body["urgent_field"] == "Sur"
        assert "Sur" in body["saludo_es"]
        assert body["open_alerts"] == 1

    def test_saludo_max_200_chars(self, client, db):
        long_name = "Rancho de la Familia Hernández García del Valle de Zapopan"
        farm, _ = self._seed_farm(db, name=long_name, n_fields=3)
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/saludo-diario")
        body = r.json()
        assert len(body["saludo_es"]) <= 200
