"""Tests for treatment application form on field detail page.

Task #52 — TDD tests first.
Verifies:
- Treatment list endpoint returns applied_at status
- Marking a treatment as applied via POST updates the record
- Already-applied treatments are distinguishable from pending ones
- Application without notes still works
"""

from datetime import datetime


class TestTreatmentApplicationForm:
    """Frontend-facing tests: the treatment card needs to show application status."""

    def _seed_farm_field(self, db):
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm", owner_name="Owner")
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=3)
        db.add(field)
        db.commit()
        db.refresh(field)
        return farm.id, field.id

    def _seed_treatment(self, db, field_id, applied_at=None, applied_notes=None):
        from cultivos.db.models import TreatmentRecord
        rec = TreatmentRecord(
            field_id=field_id,
            health_score_used=40.0,
            problema="Deficiencia de nitrogeno",
            causa_probable="Suelo agotado",
            tratamiento="Aplicar composta 3 ton/ha",
            costo_estimado_mxn=2500,
            urgencia="media",
            prevencion="Rotacion con leguminosas",
            organic=True,
            applied_at=applied_at,
            applied_notes=applied_notes,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec.id

    def test_list_treatments_shows_applied_status(self, client, db):
        """GET /treatments returns applied_at field so UI can distinguish pending vs applied."""
        fid, flid = self._seed_farm_field(db)
        # One pending, one applied
        self._seed_treatment(db, flid)
        self._seed_treatment(db, flid, applied_at=datetime(2026, 3, 25, 10, 0), applied_notes="Aplicado por la manana")

        resp = client.get(f"/api/farms/{fid}/fields/{flid}/treatments")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        applied = [t for t in data if t["applied_at"] is not None]
        pending = [t for t in data if t["applied_at"] is None]
        assert len(applied) == 1
        assert len(pending) == 1
        assert applied[0]["applied_notes"] == "Aplicado por la manana"

    def test_mark_treatment_applied_with_notes(self, client, db):
        """POST /treatments/{id}/applied with date and notes updates the record."""
        fid, flid = self._seed_farm_field(db)
        tid = self._seed_treatment(db, flid)

        resp = client.post(
            f"/api/farms/{fid}/fields/{flid}/treatments/{tid}/applied",
            json={
                "applied_at": "2026-03-26T08:30:00",
                "notes": "Suelo humedo, condiciones ideales",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["applied_at"] is not None
        assert data["applied_notes"] == "Suelo humedo, condiciones ideales"

    def test_mark_treatment_applied_without_notes(self, client, db):
        """POST /treatments/{id}/applied works without notes (notes is optional)."""
        fid, flid = self._seed_farm_field(db)
        tid = self._seed_treatment(db, flid)

        resp = client.post(
            f"/api/farms/{fid}/fields/{flid}/treatments/{tid}/applied",
            json={
                "applied_at": "2026-03-26T09:00:00",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["applied_at"] is not None
        assert data["applied_notes"] is None

    def test_mark_nonexistent_treatment_returns_404(self, client, db):
        """POST /treatments/9999/applied returns 404 for unknown treatment."""
        fid, flid = self._seed_farm_field(db)
        resp = client.post(
            f"/api/farms/{fid}/fields/{flid}/treatments/9999/applied",
            json={"applied_at": "2026-03-26T10:00:00"},
        )
        assert resp.status_code == 404

    def test_treatment_list_includes_id_for_apply_button(self, client, db):
        """Each treatment in list must have 'id' so the UI can target the apply endpoint."""
        fid, flid = self._seed_farm_field(db)
        self._seed_treatment(db, flid)

        resp = client.get(f"/api/farms/{fid}/fields/{flid}/treatments")
        data = resp.json()
        assert len(data) > 0
        for t in data:
            assert "id" in t
            assert isinstance(t["id"], int)
