"""Tests for treatment application flow — marking treatments as applied via API."""

from datetime import datetime


class TestTreatmentApplied:
    """POST /api/farms/{fid}/fields/{flid}/treatments/{tid}/applied marks treatment as applied."""

    def _seed(self, db):
        from cultivos.db.models import Farm, Field, HealthScore, SoilAnalysis
        farm = Farm(name="Rancho Test", owner_name="Owner")
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Campo A", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)
        hs = HealthScore(
            field_id=field.id, score=30, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 30.0},
        )
        db.add(hs)
        soil = SoilAnalysis(
            field_id=field.id, ph=8.5, organic_matter_pct=1.0,
            nitrogen_ppm=10, phosphorus_ppm=8, potassium_ppm=50,
            moisture_pct=15, sampled_at=datetime.utcnow(),
        )
        db.add(soil)
        db.commit()
        return farm.id, field.id

    def test_mark_treatment_applied(self, client, db):
        """POST applied_at + notes marks treatment, GET returns updated record."""
        fid, flid = self._seed(db)
        # Generate treatments
        resp = client.post(f"/api/farms/{fid}/fields/{flid}/treatments")
        assert resp.status_code == 201
        tid = resp.json()[0]["id"]

        # Mark as applied
        now = datetime.utcnow().isoformat()
        resp = client.post(
            f"/api/farms/{fid}/fields/{flid}/treatments/{tid}/applied",
            json={"applied_at": now, "notes": "Aplicado con exito"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["applied_at"] is not None
        assert data["applied_notes"] == "Aplicado con exito"

    def test_mark_applied_not_found(self, client, db):
        """POST to non-existent treatment returns 404."""
        fid, flid = self._seed(db)
        resp = client.post(
            f"/api/farms/{fid}/fields/{flid}/treatments/9999/applied",
            json={"applied_at": datetime.utcnow().isoformat()},
        )
        assert resp.status_code == 404

    def test_applied_shows_in_history(self, client, db):
        """After marking applied, treatment-history returns the applied treatment."""
        fid, flid = self._seed(db)
        resp = client.post(f"/api/farms/{fid}/fields/{flid}/treatments")
        tid = resp.json()[0]["id"]

        now = datetime.utcnow().isoformat()
        client.post(
            f"/api/farms/{fid}/fields/{flid}/treatments/{tid}/applied",
            json={"applied_at": now, "notes": "Nota de campo"},
        )

        resp = client.get(f"/api/farms/{fid}/fields/{flid}/treatments/treatment-history")
        assert resp.status_code == 200
        history = resp.json()
        assert len(history) >= 1
        assert history[0]["applied_notes"] == "Nota de campo"

    def test_list_treatments_shows_applied_status(self, client, db):
        """GET treatments list includes applied_at field for applied treatments."""
        fid, flid = self._seed(db)
        resp = client.post(f"/api/farms/{fid}/fields/{flid}/treatments")
        treatments = resp.json()
        tid = treatments[0]["id"]

        # Before applying — applied_at is null
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/treatments")
        assert resp.json()[0]["applied_at"] is None

        # After applying
        now = datetime.utcnow().isoformat()
        client.post(
            f"/api/farms/{fid}/fields/{flid}/treatments/{tid}/applied",
            json={"applied_at": now},
        )
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/treatments")
        applied = [t for t in resp.json() if t["id"] == tid]
        assert applied[0]["applied_at"] is not None
