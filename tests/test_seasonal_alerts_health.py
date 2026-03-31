"""Tests for seasonal alerts enriched with field health context."""

from datetime import date, datetime

import pytest

from cultivos.db.models import Farm, Field, HealthScore


class TestSeasonalAlertsWithHealth:
    """Seasonal alerts include field health summaries when data exists."""

    def _seed_farm_with_health(self, db):
        """Create farm with 2 fields, each with a health score."""
        farm = Farm(name="Granja Salud", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        f1 = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=5.0)
        f2 = Field(farm_id=farm.id, name="Parcela Sur", crop_type="frijol", hectares=3.0)
        db.add_all([f1, f2])
        db.commit()
        db.refresh(f1)
        db.refresh(f2)

        hs1 = HealthScore(
            field_id=f1.id, score=78.5, trend="improving",
            sources=["ndvi", "soil"], breakdown={"ndvi": 80.0, "soil": 75.0},
            scored_at=datetime(2026, 3, 15),
        )
        hs2 = HealthScore(
            field_id=f2.id, score=45.2, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 45.2},
            scored_at=datetime(2026, 3, 14),
        )
        db.add_all([hs1, hs2])
        db.commit()

        return farm

    def test_response_includes_field_health(self, client, db, admin_headers):
        """Response includes field_health list with health data per field."""
        farm = self._seed_farm_with_health(db)
        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-03-15",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "field_health" in data
        assert len(data["field_health"]) == 2

    def test_field_health_has_required_fields(self, client, db, admin_headers):
        """Each field_health entry has field_id, field_name, crop_type, score, trend."""
        farm = self._seed_farm_with_health(db)
        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-03-15",
            headers=admin_headers,
        )
        data = resp.json()
        for fh in data["field_health"]:
            assert "field_id" in fh
            assert "field_name" in fh
            assert "crop_type" in fh
            assert "score" in fh
            assert "trend" in fh

    def test_field_health_score_values(self, client, db, admin_headers):
        """Health scores match seeded data."""
        farm = self._seed_farm_with_health(db)
        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-03-15",
            headers=admin_headers,
        )
        data = resp.json()
        by_name = {fh["field_name"]: fh for fh in data["field_health"]}
        assert by_name["Parcela Norte"]["score"] == 78.5
        assert by_name["Parcela Norte"]["trend"] == "improving"
        assert by_name["Parcela Sur"]["score"] == 45.2
        assert by_name["Parcela Sur"]["trend"] == "declining"

    def test_field_health_includes_crop_type(self, client, db, admin_headers):
        """Field health entries include the crop type."""
        farm = self._seed_farm_with_health(db)
        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-03-15",
            headers=admin_headers,
        )
        data = resp.json()
        crops = {fh["crop_type"] for fh in data["field_health"]}
        assert "maiz" in crops
        assert "frijol" in crops

    def test_avg_health_included(self, client, db, admin_headers):
        """Response includes avg_health computed from field scores."""
        farm = self._seed_farm_with_health(db)
        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-03-15",
            headers=admin_headers,
        )
        data = resp.json()
        assert "avg_health" in data
        expected_avg = round((78.5 + 45.2) / 2, 1)
        assert data["avg_health"] == expected_avg


class TestSeasonalAlertsWithoutHealth:
    """Graceful degradation when no health data exists."""

    def test_no_health_data_returns_empty_list(self, client, db, admin_headers):
        """When farm has fields but no health scores, field_health is empty."""
        farm = Farm(name="Granja Sin Datos", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        f1 = Field(farm_id=farm.id, name="Parcela Vacia", crop_type="maiz", hectares=2.0)
        db.add(f1)
        db.commit()

        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-03-15",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["field_health"] == []
        assert data["avg_health"] is None

    def test_no_fields_returns_empty_list(self, client, db, admin_headers):
        """When farm has no fields at all, field_health is empty."""
        farm = Farm(name="Granja Vacia", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-03-15",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["field_health"] == []
        assert data["avg_health"] is None

    def test_alerts_still_present_without_health(self, client, db, admin_headers):
        """Seasonal alerts are unaffected by absence of health data."""
        farm = Farm(name="Granja Solo Alertas", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-03-15",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts"]) > 0
        assert data["season"] == "secas"


class TestFieldHealthLatestOnly:
    """Only the most recent health score per field is returned."""

    def test_returns_latest_score(self, client, db, admin_headers):
        """When multiple scores exist, only the latest is used."""
        farm = Farm(name="Granja Historica", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        f1 = Field(farm_id=farm.id, name="Campo Historial", crop_type="agave", hectares=10.0)
        db.add(f1)
        db.commit()
        db.refresh(f1)

        old = HealthScore(
            field_id=f1.id, score=30.0, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 30.0},
            scored_at=datetime(2026, 2, 1),
        )
        new = HealthScore(
            field_id=f1.id, score=72.0, trend="improving",
            sources=["ndvi", "soil"], breakdown={"ndvi": 75.0, "soil": 68.0},
            scored_at=datetime(2026, 3, 10),
        )
        db.add_all([old, new])
        db.commit()

        resp = client.get(
            f"/api/farms/{farm.id}/seasonal-alerts?reference_date=2026-03-15",
            headers=admin_headers,
        )
        data = resp.json()
        assert len(data["field_health"]) == 1
        assert data["field_health"][0]["score"] == 72.0
        assert data["field_health"][0]["trend"] == "improving"
