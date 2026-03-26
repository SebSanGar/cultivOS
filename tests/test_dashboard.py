"""Tests for Dashboard API — GET /api/farms/{id}/dashboard."""

from datetime import datetime

from cultivos.db.models import Farm, Field, HealthScore, NDVIResult, SoilAnalysis, WeatherRecord


class TestDashboardReturnsAllFieldsWithLatestScores:
    """GET /api/farms/{id}/dashboard returns fields with latest health_score, latest_ndvi, latest_soil."""

    def test_dashboard_returns_all_fields_with_latest_scores(self, client, db):
        farm = Farm(name="Finca Test", location_lat=20.5, location_lon=-103.3, total_hectares=50)
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field1 = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=20)
        field2 = Field(farm_id=farm.id, name="Parcela B", crop_type="agave", hectares=30)
        db.add_all([field1, field2])
        db.commit()
        db.refresh(field1)
        db.refresh(field2)

        # Add health scores for field1 (two scores — should return latest)
        hs_old = HealthScore(
            field_id=field1.id, score=60.0, trend="stable", sources=["ndvi"],
            breakdown={"ndvi": 60.0}, scored_at=datetime(2026, 1, 1),
        )
        hs_new = HealthScore(
            field_id=field1.id, score=75.0, trend="improving", sources=["ndvi", "soil"],
            breakdown={"ndvi": 70.0, "soil": 80.0}, scored_at=datetime(2026, 3, 1),
        )
        db.add_all([hs_old, hs_new])

        # Add NDVI for field1
        ndvi = NDVIResult(
            field_id=field1.id, ndvi_mean=0.65, ndvi_std=0.1, ndvi_min=0.3,
            ndvi_max=0.9, pixels_total=1000, stress_pct=15.0,
            zones=[{"classification": "healthy", "min_ndvi": 0.6, "max_ndvi": 0.9, "pixel_count": 850, "percentage": 85.0}],
            analyzed_at=datetime(2026, 3, 1),
        )
        db.add(ndvi)

        # Add soil for field2
        soil = SoilAnalysis(
            field_id=field2.id, ph=6.5, organic_matter_pct=3.2, nitrogen_ppm=40,
            phosphorus_ppm=25, potassium_ppm=180, texture="loam", moisture_pct=35,
            sampled_at=datetime(2026, 2, 15),
        )
        db.add(soil)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()

        assert data["farm"]["id"] == farm.id
        assert data["farm"]["name"] == "Finca Test"
        assert len(data["fields"]) == 2

        # Field1 should have latest health score and NDVI
        f1 = next(f for f in data["fields"] if f["name"] == "Parcela A")
        assert f1["latest_health_score"] is not None
        assert f1["latest_health_score"]["score"] == 75.0  # latest, not 60
        assert f1["latest_ndvi"] is not None
        assert f1["latest_ndvi"]["ndvi_mean"] == 0.65
        assert f1["latest_soil"] is None  # no soil for field1

        # Field2 should have soil but no health/ndvi
        f2 = next(f for f in data["fields"] if f["name"] == "Parcela B")
        assert f2["latest_health_score"] is None
        assert f2["latest_ndvi"] is None
        assert f2["latest_soil"] is not None
        assert f2["latest_soil"]["ph"] == 6.5


class TestDashboardEmptyFarm:
    """New farm with no data returns fields: [], overall_health: null."""

    def test_dashboard_empty_farm_returns_empty_fields(self, client, db):
        farm = Farm(name="Finca Vacia", location_lat=20.5, location_lon=-103.3)
        db.add(farm)
        db.commit()
        db.refresh(farm)

        resp = client.get(f"/api/farms/{farm.id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()

        assert data["farm"]["name"] == "Finca Vacia"
        assert data["fields"] == []
        assert data["overall_health"] is None
        assert data["weather"] is None


class TestDashboardRanksFieldsByUrgency:
    """Field with score 30 appears before field with score 80."""

    def test_dashboard_ranks_fields_by_urgency(self, client, db):
        farm = Farm(name="Finca Ranking", location_lat=20.5, location_lon=-103.3)
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field_healthy = Field(farm_id=farm.id, name="Sana", crop_type="maiz", hectares=10)
        field_sick = Field(farm_id=farm.id, name="Enferma", crop_type="agave", hectares=10)
        db.add_all([field_healthy, field_sick])
        db.commit()
        db.refresh(field_healthy)
        db.refresh(field_sick)

        hs_high = HealthScore(
            field_id=field_healthy.id, score=80.0, trend="stable",
            sources=["ndvi"], breakdown={"ndvi": 80.0}, scored_at=datetime(2026, 3, 1),
        )
        hs_low = HealthScore(
            field_id=field_sick.id, score=30.0, trend="declining",
            sources=["ndvi"], breakdown={"ndvi": 30.0}, scored_at=datetime(2026, 3, 1),
        )
        db.add_all([hs_high, hs_low])
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()

        fields = data["fields"]
        assert len(fields) == 2
        # Lowest score (most urgent) first
        assert fields[0]["name"] == "Enferma"
        assert fields[0]["latest_health_score"]["score"] == 30.0
        assert fields[1]["name"] == "Sana"
        assert fields[1]["latest_health_score"]["score"] == 80.0


class TestDashboardIncludesWeather:
    """If weather exists, dashboard has weather key."""

    def test_dashboard_includes_weather(self, client, db):
        farm = Farm(name="Finca Clima", location_lat=20.5, location_lon=-103.3)
        db.add(farm)
        db.commit()
        db.refresh(farm)

        weather = WeatherRecord(
            farm_id=farm.id, temp_c=28.5, humidity_pct=65.0, wind_kmh=12.0,
            description="Parcialmente nublado", forecast_3day=[],
            recorded_at=datetime(2026, 3, 26),
        )
        db.add(weather)
        db.commit()

        resp = client.get(f"/api/farms/{farm.id}/dashboard")
        assert resp.status_code == 200
        data = resp.json()

        assert data["weather"] is not None
        assert data["weather"]["temp_c"] == 28.5
        assert data["weather"]["description"] == "Parcialmente nublado"
