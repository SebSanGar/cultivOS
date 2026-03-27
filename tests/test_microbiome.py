"""Tests for soil microbiome indicators — proxy metrics for microbial diversity."""

from datetime import datetime


class TestCreateMicrobiomeRecord:
    """POST /api/farms/{id}/fields/{id}/microbiome creates a microbiome record."""

    def test_create_microbiome_record(self, client, admin_headers, db):
        from cultivos.db.models import Farm, Field

        farm = Farm(name="Test Farm", location_lat=20.6, location_lon=-103.3)
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        resp = client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/microbiome",
            json={
                "respiration_rate": 55.0,
                "microbial_biomass_carbon": 320.0,
                "fungi_bacteria_ratio": 1.2,
                "sampled_at": "2026-03-27T10:00:00",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["respiration_rate"] == 55.0
        assert data["microbial_biomass_carbon"] == 320.0
        assert data["fungi_bacteria_ratio"] == 1.2
        assert data["field_id"] == field.id
        assert "id" in data
        assert "classification" in data

    def test_create_microbiome_invalid_field(self, client, admin_headers):
        resp = client.post(
            "/api/farms/999/fields/999/microbiome",
            json={
                "respiration_rate": 30.0,
                "microbial_biomass_carbon": 200.0,
                "fungi_bacteria_ratio": 0.8,
                "sampled_at": "2026-03-27T10:00:00",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_list_microbiome_records(self, client, admin_headers, db):
        from cultivos.db.models import Farm, Field

        farm = Farm(name="Test Farm", location_lat=20.6, location_lon=-103.3)
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        # Create two records
        for rate in [55.0, 15.0]:
            client.post(
                f"/api/farms/{farm.id}/fields/{field.id}/microbiome",
                json={
                    "respiration_rate": rate,
                    "microbial_biomass_carbon": 200.0,
                    "fungi_bacteria_ratio": 0.8,
                    "sampled_at": "2026-03-27T10:00:00",
                },
                headers=admin_headers,
            )

        resp = client.get(
            f"/api/farms/{farm.id}/fields/{field.id}/microbiome",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestMicrobiomeHealthClassification:
    """Classification: respiration_rate > 50 = healthy, 20-50 = moderate, <20 = degraded."""

    def _create_and_get(self, client, admin_headers, db, respiration_rate):
        from cultivos.db.models import Farm, Field

        farm = Farm(name="Test Farm", location_lat=20.6, location_lon=-103.3)
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        resp = client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/microbiome",
            json={
                "respiration_rate": respiration_rate,
                "microbial_biomass_carbon": 200.0,
                "fungi_bacteria_ratio": 0.8,
                "sampled_at": "2026-03-27T10:00:00",
            },
            headers=admin_headers,
        )
        return resp.json()

    def test_healthy_classification(self, client, admin_headers, db):
        data = self._create_and_get(client, admin_headers, db, 55.0)
        assert data["classification"] == "healthy"

    def test_moderate_classification(self, client, admin_headers, db):
        data = self._create_and_get(client, admin_headers, db, 35.0)
        assert data["classification"] == "moderate"

    def test_degraded_classification(self, client, admin_headers, db):
        data = self._create_and_get(client, admin_headers, db, 15.0)
        assert data["classification"] == "degraded"

    def test_boundary_at_50(self, client, admin_headers, db):
        data = self._create_and_get(client, admin_headers, db, 50.0)
        assert data["classification"] == "moderate"

    def test_boundary_at_20(self, client, admin_headers, db):
        data = self._create_and_get(client, admin_headers, db, 20.0)
        assert data["classification"] == "moderate"


class TestMicrobiomeIntegratesWithHealthScore:
    """Health score improves when microbiome data is healthy."""

    def test_health_score_with_healthy_microbiome(self, client, admin_headers, db):
        from cultivos.db.models import Farm, Field, NDVIResult
        from datetime import datetime

        farm = Farm(name="Test Farm", location_lat=20.6, location_lon=-103.3)
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        # Add NDVI data (mediocre)
        ndvi = NDVIResult(
            field_id=field.id, ndvi_mean=0.5, ndvi_std=0.1, ndvi_min=0.2,
            ndvi_max=0.8, pixels_total=1000, stress_pct=20.0,
            zones=[{"zone": "moderate", "pct": 100}],
            analyzed_at=datetime(2026, 3, 27),
        )
        db.add(ndvi)
        db.commit()

        # Compute health WITHOUT microbiome
        resp1 = client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/health",
            headers=admin_headers,
        )
        score_without = resp1.json()["score"]

        # Add healthy microbiome record
        client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/microbiome",
            json={
                "respiration_rate": 60.0,
                "microbial_biomass_carbon": 400.0,
                "fungi_bacteria_ratio": 1.5,
                "sampled_at": "2026-03-27T10:00:00",
            },
            headers=admin_headers,
        )

        # Compute health WITH healthy microbiome
        resp2 = client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/health",
            headers=admin_headers,
        )
        score_with = resp2.json()["score"]

        # Healthy microbiome should improve or maintain the score
        assert score_with >= score_without
        assert "microbiome" in resp2.json()["sources"]


class TestMicrobiomeRecommendations:
    """Degraded microbiome triggers specific regenerative recommendations."""

    def test_degraded_microbiome_triggers_recommendations(self, client, admin_headers, db):
        from cultivos.db.models import Farm, Field, NDVIResult
        from datetime import datetime

        farm = Farm(name="Test Farm", location_lat=20.6, location_lon=-103.3)
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Parcela A", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        # Add mediocre NDVI to get a health score
        ndvi = NDVIResult(
            field_id=field.id, ndvi_mean=0.4, ndvi_std=0.15, ndvi_min=0.1,
            ndvi_max=0.7, pixels_total=1000, stress_pct=35.0,
            zones=[{"zone": "stressed", "pct": 100}],
            analyzed_at=datetime(2026, 3, 27),
        )
        db.add(ndvi)
        db.commit()

        # Add degraded microbiome
        client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/microbiome",
            json={
                "respiration_rate": 10.0,
                "microbial_biomass_carbon": 80.0,
                "fungi_bacteria_ratio": 0.3,
                "sampled_at": "2026-03-27T10:00:00",
            },
            headers=admin_headers,
        )

        # Compute health score first
        client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/health",
            headers=admin_headers,
        )

        # Generate treatment recommendations
        resp = client.post(
            f"/api/farms/{farm.id}/fields/{field.id}/treatments",
            headers=admin_headers,
        )
        assert resp.status_code == 201
        treatments = resp.json()
        treatment_texts = [t["tratamiento"] for t in treatments]
        # Should contain microbiome-related recommendations
        found_microbiome = any(
            "composta" in t.lower() or "cobertura" in t.lower() or "micorriz" in t.lower()
            for t in treatment_texts
        )
        assert found_microbiome, f"Expected microbiome recommendations, got: {treatment_texts}"
