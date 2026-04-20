"""Tests for GET /api/farms/{farm_id}/digest-whatsapp — farm-level Spanish daily digest."""

from datetime import datetime, timedelta


class TestFarmDigestWhatsapp:
    """Farm-level WhatsApp-ready Spanish digest endpoint."""

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

        r = client.get(f"/api/farms/{farm.id}/digest-whatsapp")
        assert r.status_code == 200
        body = r.json()
        assert "farm_name" in body
        assert "field_count" in body
        assert "top_priority" in body
        assert "digest_es" in body

    def test_happy_all_ok(self, client, db):
        farm, fields = self._seed_farm(db, n_fields=3)
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/digest-whatsapp")
        assert r.status_code == 200
        body = r.json()
        assert body["farm_name"] == "Rancho Don Manuel"
        assert body["field_count"] == 3
        assert body["top_priority"] == "ninguna"
        assert "todo en orden" in body["digest_es"].lower()
        assert len(body["digest_es"]) <= 200

    def test_unknown_farm_404(self, client, db):
        r = client.get("/api/farms/9999/digest-whatsapp")
        assert r.status_code == 404

    def test_no_fields(self, client, db):
        farm, _ = self._seed_farm(db, n_fields=0)
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/digest-whatsapp")
        assert r.status_code == 200
        body = r.json()
        assert body["field_count"] == 0
        assert "sin campos" in body["digest_es"].lower()

    def test_critical_alert_top_priority(self, client, db):
        from cultivos.db.models import AlertLog, HealthScore

        farm, fields = self._seed_farm(db, n_fields=2, field_names=["Norte", "Sur"])
        db.add(HealthScore(
            field_id=fields[0].id, score=85.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 85},
            scored_at=datetime.utcnow(),
        ))
        db.add(AlertLog(
            farm_id=farm.id, field_id=fields[1].id, alert_type="health",
            message="Plaga detectada", severity="critical",
            acknowledged=False,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/digest-whatsapp")
        body = r.json()
        assert body["top_priority"] == "alta"
        assert "Sur" in body["digest_es"]
        assert len(body["digest_es"]) <= 200

    def test_mixed_priorities_picks_highest(self, client, db):
        from cultivos.db.models import HealthScore, TreatmentRecord

        farm, fields = self._seed_farm(db, n_fields=2, field_names=["Alfa", "Beta"])
        db.add(HealthScore(
            field_id=fields[0].id, score=42.0, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 42},
            scored_at=datetime.utcnow(),
        ))
        db.add(TreatmentRecord(
            field_id=fields[1].id, health_score_used=55.0,
            problema="Deficiencia", causa_probable="Suelo",
            tratamiento="Compost", costo_estimado_mxn=300,
            urgencia="alta", prevencion="Monitorear", organic=True,
            applied_at=None,
        ))
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/digest-whatsapp")
        body = r.json()
        assert body["top_priority"] == "alta"
        assert body["field_count"] == 2
        assert len(body["digest_es"]) <= 200

    def test_single_field_farm(self, client, db):
        farm, fields = self._seed_farm(db, n_fields=1, field_names=["Unico"])
        db.commit()

        r = client.get(f"/api/farms/{farm.id}/digest-whatsapp")
        body = r.json()
        assert body["field_count"] == 1
        assert body["farm_name"] == "Rancho Don Manuel"
        assert "Unico" in body["digest_es"] or "1 campo" in body["digest_es"]
        assert len(body["digest_es"]) <= 200
