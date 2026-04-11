"""Tests for per-field treatment cost effectiveness endpoint.

GET /api/farms/{farm_id}/fields/{field_id}/treatment-cost-effectiveness
Returns per-treatment cost_mxn and health_delta (next HealthScore - health_score_used).
"""

from datetime import datetime, timedelta

from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord


def _make_farm_field(db):
    farm = Farm(name="Rancho Prueba", state="Jalisco", total_hectares=20.0)
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela Norte", hectares=5.0, crop_type="maiz")
    db.add(field)
    db.flush()
    return farm, field


def _make_treatment(field_id, tratamiento="Composta", cost=1500, health_score_used=55.0):
    return TreatmentRecord(
        field_id=field_id,
        health_score_used=health_score_used,
        problema="Salud baja",
        causa_probable="Falta de nutrientes",
        tratamiento=tratamiento,
        urgencia="media",
        prevencion="rotacion de cultivos",
        organic=True,
        costo_estimado_mxn=cost,
    )


class TestFieldTreatmentCostEffectiveness:

    def test_no_treatments_returns_empty_list(self, client, db):
        """Field with no treatments returns empty list."""
        farm, field = _make_farm_field(db)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/treatment-cost-effectiveness")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_treatment_with_health_delta(self, client, db):
        """Treatment with a subsequent HealthScore returns cost and computed delta."""
        farm, field = _make_farm_field(db)

        now = datetime.utcnow()
        tr = _make_treatment(field.id, cost=2000, health_score_used=50.0)
        tr.created_at = now - timedelta(days=10)
        db.add(tr)
        db.flush()

        # HealthScore AFTER treatment creation
        hs = HealthScore(field_id=field.id, score=68.0, scored_at=now - timedelta(days=3))
        db.add(hs)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/treatment-cost-effectiveness")

        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["tratamiento"] == "Composta"
        assert results[0]["cost_mxn"] == 2000
        assert abs(results[0]["health_delta"] - 18.0) < 0.1  # 68 - 50

    def test_treatment_no_subsequent_health_score_returns_none_delta(self, client, db):
        """Treatment with no subsequent HealthScore returns health_delta=None."""
        farm, field = _make_farm_field(db)

        tr = _make_treatment(field.id, cost=800)
        db.add(tr)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/treatment-cost-effectiveness")

        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["health_delta"] is None
        assert results[0]["cost_mxn"] == 800

    def test_multiple_treatments_each_with_own_delta(self, client, db):
        """Multiple treatments each compute their own health delta independently."""
        farm, field = _make_farm_field(db)

        now = datetime.utcnow()

        tr1 = _make_treatment(field.id, tratamiento="Composta", cost=1000, health_score_used=40.0)
        tr1.created_at = now - timedelta(days=20)
        db.add(tr1)

        tr2 = _make_treatment(field.id, tratamiento="Te de lombriz", cost=500, health_score_used=60.0)
        tr2.created_at = now - timedelta(days=5)
        db.add(tr2)

        db.flush()

        # Health score after tr1 (should be picked up for tr1's delta)
        db.add(HealthScore(field_id=field.id, score=55.0, scored_at=now - timedelta(days=15)))
        # Health score after tr2
        db.add(HealthScore(field_id=field.id, score=72.0, scored_at=now - timedelta(days=2)))
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/treatment-cost-effectiveness")

        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 2

        by_name = {r["tratamiento"]: r for r in results}
        assert abs(by_name["Composta"]["health_delta"] - 15.0) < 0.1      # 55 - 40
        assert abs(by_name["Te de lombriz"]["health_delta"] - 12.0) < 0.1  # 72 - 60

    def test_unknown_field_returns_404(self, client, db):
        """GET for non-existent field returns 404."""
        farm = Farm(name="Rancho X", state="Jalisco", total_hectares=10.0)
        db.add(farm)
        db.commit()
        db.refresh(farm)

        resp = client.get(f"/api/farms/{farm.id}/fields/9999/treatment-cost-effectiveness")
        assert resp.status_code == 404

    def test_unknown_farm_returns_404(self, client, db):
        """GET for non-existent farm returns 404."""
        resp = client.get("/api/farms/9999/fields/1/treatment-cost-effectiveness")
        assert resp.status_code == 404

    def test_health_score_before_treatment_not_counted(self, client, db):
        """HealthScore created BEFORE the treatment is ignored — delta must be post-treatment."""
        farm, field = _make_farm_field(db)

        now = datetime.utcnow()
        tr = _make_treatment(field.id, cost=1200, health_score_used=45.0)
        tr.created_at = now - timedelta(days=5)
        db.add(tr)
        db.flush()

        # Health score BEFORE treatment — should NOT be used for delta
        db.add(HealthScore(field_id=field.id, score=90.0, scored_at=now - timedelta(days=10)))
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/treatment-cost-effectiveness")

        assert resp.status_code == 200
        results = resp.json()
        assert results[0]["health_delta"] is None
