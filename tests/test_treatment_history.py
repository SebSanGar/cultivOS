"""Tests for treatment history tracking — TDD first.

Closes the recommendation → result loop:
- Log when a treatment was applied
- Measure effectiveness (health score delta before/after)
- View chronological treatment timeline with health scores
- Handle missing health data gracefully
"""

from datetime import datetime, timedelta


class TestTreatmentHistory:
    def _seed_farm_field(self, db):
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm", owner_name="Test Owner")
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)
        return farm.id, field.id

    def _seed_treatment(self, db, field_id, score=35.0):
        from cultivos.db.models import TreatmentRecord
        rec = TreatmentRecord(
            field_id=field_id,
            health_score_used=score,
            problema="Suelo acido",
            causa_probable="pH bajo por lluvias",
            tratamiento="Aplicar cal dolomita 2 ton/ha",
            costo_estimado_mxn=3000,
            urgencia="alta",
            prevencion="Encalado anual preventivo",
            organic=True,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec.id

    def _seed_health_score(self, db, field_id, score, scored_at):
        from cultivos.db.models import HealthScore
        hs = HealthScore(
            field_id=field_id,
            score=score,
            trend="stable",
            sources=["ndvi"],
            breakdown={"ndvi": score},
            scored_at=scored_at,
        )
        db.add(hs)
        db.commit()
        db.refresh(hs)
        return hs.id

    def test_log_treatment_applied(self, client, db):
        """POST /treatments/{id}/applied records date + notes."""
        fid, flid = self._seed_farm_field(db)
        tid = self._seed_treatment(db, flid)

        resp = client.post(
            f"/api/farms/{fid}/fields/{flid}/treatments/{tid}/applied",
            json={
                "applied_at": "2026-03-20T10:00:00",
                "notes": "Se aplico cal dolomita en la manana, suelo humedo",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == tid
        assert data["applied_at"] is not None
        assert "cal dolomita" in data["applied_notes"]

    def test_treatment_effectiveness(self, client, db):
        """GET /treatments/{id}/effectiveness returns health score delta before/after."""
        fid, flid = self._seed_farm_field(db)
        tid = self._seed_treatment(db, flid, score=35.0)

        # Health score BEFORE treatment application
        before_date = datetime(2026, 3, 15)
        self._seed_health_score(db, flid, score=35.0, scored_at=before_date)

        # Mark treatment as applied
        applied_date = datetime(2026, 3, 20)
        from cultivos.db.models import TreatmentRecord
        rec = db.query(TreatmentRecord).get(tid)
        rec.applied_at = applied_date
        rec.applied_notes = "Aplicado"
        db.commit()

        # Health score AFTER treatment application
        after_date = datetime(2026, 3, 28)
        self._seed_health_score(db, flid, score=58.0, scored_at=after_date)

        resp = client.get(
            f"/api/farms/{fid}/fields/{flid}/treatments/{tid}/effectiveness"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["treatment_id"] == tid
        assert data["score_before"] == 35.0
        assert data["score_after"] == 58.0
        assert data["delta"] == 23.0
        assert data["status"] == "effective"

    def test_treatment_timeline(self, client, db):
        """GET /fields/{id}/treatment-history returns chronological list with health scores."""
        fid, flid = self._seed_farm_field(db)

        # Create two treatments at different times
        tid1 = self._seed_treatment(db, flid, score=35.0)
        tid2 = self._seed_treatment(db, flid, score=50.0)

        # Mark first as applied
        from cultivos.db.models import TreatmentRecord
        rec1 = db.query(TreatmentRecord).get(tid1)
        rec1.applied_at = datetime(2026, 3, 10)
        rec1.applied_notes = "Aplicado"
        rec2 = db.query(TreatmentRecord).get(tid2)
        rec2.applied_at = datetime(2026, 3, 20)
        rec2.applied_notes = "Aplicado"
        db.commit()

        resp = client.get(
            f"/api/farms/{fid}/fields/{flid}/treatments/treatment-history"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # Should be chronological (oldest first)
        assert data[0]["treatment_id"] == tid1
        assert data[1]["treatment_id"] == tid2
        # Each entry should have the treatment info
        assert "problema" in data[0]
        assert "applied_at" in data[0]

    def test_no_health_data(self, client, db):
        """Effectiveness endpoint returns 'insufficient_data' when no scores around treatment date."""
        fid, flid = self._seed_farm_field(db)
        tid = self._seed_treatment(db, flid, score=35.0)

        # Mark as applied but no health scores exist
        from cultivos.db.models import TreatmentRecord
        rec = db.query(TreatmentRecord).get(tid)
        rec.applied_at = datetime(2026, 3, 20)
        rec.applied_notes = "Aplicado"
        db.commit()

        resp = client.get(
            f"/api/farms/{fid}/fields/{flid}/treatments/{tid}/effectiveness"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "insufficient_data"
        assert data["score_before"] is None
        assert data["score_after"] is None
        assert data["delta"] is None
