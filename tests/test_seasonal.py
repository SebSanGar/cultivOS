"""Tests for seasonal performance comparison — temporal vs secas analysis."""

import pytest
from datetime import datetime


@pytest.fixture
def farm_field(db):
    """Create a farm and field for seasonal tests."""
    from cultivos.db.models import Farm, Field

    farm = Farm(
        name="Rancho Estacional",
        owner_name="Maria",
        location_lat=20.6,
        location_lon=-103.3,
        total_hectares=40,
        municipality="Zapopan",
        state="Jalisco",
        country="MX",
    )
    db.add(farm)
    db.flush()

    field = Field(farm_id=farm.id, name="Parcela Maiz", crop_type="maiz", hectares=20)
    db.add(field)
    db.flush()

    return farm, field


@pytest.fixture
def seed_scores(db, farm_field):
    """Seed health scores across temporal and secas seasons over 2 years."""
    from cultivos.db.models import HealthScore

    _, field = farm_field
    scores = [
        # 2025 temporal (Jun-Oct)
        (datetime(2025, 7, 15), 75.0),
        (datetime(2025, 8, 20), 80.0),
        (datetime(2025, 9, 10), 78.0),
        # 2025 secas (Nov-May) — crosses into 2026
        (datetime(2025, 12, 5), 55.0),
        (datetime(2026, 2, 10), 50.0),
        # 2026 temporal (Jun-Oct)
        (datetime(2026, 7, 1), 82.0),
        (datetime(2026, 8, 15), 85.0),
    ]
    for scored_at, score in scores:
        hs = HealthScore(
            field_id=field.id,
            score=score,
            trend="stable",
            sources=["ndvi"],
            breakdown={"ndvi": score},
            scored_at=scored_at,
        )
        db.add(hs)
    db.commit()
    return scores


class TestSeasonalSummary:
    def test_seasonal_summary(self, client, db, admin_headers, farm_field, seed_scores):
        """GET /api/farms/{id}/fields/{id}/seasonal returns per-season averages."""
        farm, field = farm_field
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/seasonal",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "seasons" in data
        assert len(data["seasons"]) > 0
        # Each season entry has season name, year, avg score, count
        entry = data["seasons"][0]
        assert "season" in entry
        assert "year" in entry
        assert "avg_score" in entry
        assert "count" in entry


class TestTemporalVsSecas:
    def test_temporal_vs_secas(self, client, db, admin_headers, farm_field, seed_scores):
        """Groups health scores by Jalisco season (Jun-Oct temporal, Nov-May secas)."""
        farm, field = farm_field
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/seasonal",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        seasons = data["seasons"]
        season_names = [s["season"] for s in seasons]
        assert "temporal" in season_names
        assert "secas" in season_names

        # 2025 temporal: avg of 75, 80, 78 = 77.67
        temporal_2025 = next(
            s for s in seasons if s["season"] == "temporal" and s["year"] == 2025
        )
        assert abs(temporal_2025["avg_score"] - 77.67) < 0.5
        assert temporal_2025["count"] == 3

        # 2025-2026 secas: avg of 55, 50 = 52.5
        # Secas spans Nov-May, so the "year" key refers to the start year (2025)
        secas_2025 = next(
            s for s in seasons if s["season"] == "secas" and s["year"] == 2025
        )
        assert abs(secas_2025["avg_score"] - 52.5) < 0.5
        assert secas_2025["count"] == 2


class TestYearOverYear:
    def test_year_over_year(self, client, db, admin_headers, farm_field, seed_scores):
        """Supports ?year= param to filter to a specific year."""
        farm, field = farm_field
        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/seasonal?year=2025",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should only have 2025 seasons
        years = {s["year"] for s in data["seasons"]}
        assert years == {2025}

        resp2 = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/seasonal?year=2026",
            headers=admin_headers,
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        years2 = {s["year"] for s in data2["seasons"]}
        assert years2 == {2026}


class TestInsufficientData:
    def test_insufficient_data(self, client, db, admin_headers, farm_field):
        """Returns 'insufficient_data' for seasons with <2 data points."""
        from cultivos.db.models import HealthScore

        farm, field = farm_field
        # Add just 1 score in temporal 2025
        hs = HealthScore(
            field_id=field.id,
            score=70.0,
            trend="stable",
            sources=["ndvi"],
            breakdown={"ndvi": 70.0},
            scored_at=datetime(2025, 7, 15),
        )
        db.add(hs)
        db.commit()

        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/seasonal",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Season with only 1 data point should be marked insufficient
        temporal = next(
            s for s in data["seasons"] if s["season"] == "temporal" and s["year"] == 2025
        )
        assert temporal["status"] == "insufficient_data"
        assert temporal["count"] == 1
