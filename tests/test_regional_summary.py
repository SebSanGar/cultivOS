"""Tests for GET /api/intel/regional-summary — regional intelligence aggregation."""

from datetime import datetime

import pytest

from cultivos.db.models import (
    Farm,
    FarmerFeedback,
    Field,
    HealthScore,
    TreatmentRecord,
)


def _seed_region(db, state="Jalisco", farm_count=2, fields_per_farm=2):
    """Seed farms, fields, health scores, and treatments for a region."""
    farms = []
    for i in range(farm_count):
        farm = Farm(
            name=f"Finca {state} {i+1}",
            owner_name=f"Propietario {i+1}",
            location_lat=20.6 + i * 0.1,
            location_lon=-103.3 + i * 0.1,
            total_hectares=50.0 + i * 10,
            municipality=f"Municipio {i+1}",
            state=state,
            country="MX",
        )
        db.add(farm)
        db.flush()
        farms.append(farm)

        for j in range(fields_per_farm):
            crop = "maiz" if j % 2 == 0 else "frijol"
            field = Field(
                farm_id=farm.id,
                name=f"Parcela {j+1}",
                crop_type=crop,
                hectares=10.0 + j * 5,
            )
            db.add(field)
            db.flush()

            # Add health score
            hs = HealthScore(
                field_id=field.id,
                score=70 + i * 5 + j * 3,
                trend="improving" if i % 2 == 0 else "stable",
                scored_at=datetime(2026, 3, 15),
            )
            db.add(hs)

            # Add treatments
            tr = TreatmentRecord(
                field_id=field.id,
                health_score_used=65.0,
                problema="Baja fertilidad",
                causa_probable="Suelo agotado",
                tratamiento="Composta" if j % 2 == 0 else "Bocashi",
                costo_estimado_mxn=500,
                urgencia="media",
                prevencion="Rotar cultivos cada temporada",
                organic=True,
                ancestral_method_name="Milpa" if j == 0 else None,
            )
            db.add(tr)
            db.flush()

            # Add farmer feedback for first treatment
            if j == 0:
                fb = FarmerFeedback(
                    field_id=field.id,
                    treatment_id=tr.id,
                    worked=True,
                    rating=4,
                    farmer_notes="Funciono bien",
                )
                db.add(fb)

    db.commit()
    return farms


# ── Service tests ────────────────────────────────────────────────────


class TestComputeRegionalSummary:
    """Tests for compute_regional_summary service function."""

    def test_returns_region_with_farms(self, db):
        """Farms in the same state are grouped into one region."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        _seed_region(db, state="Jalisco", farm_count=2, fields_per_farm=2)
        result = compute_regional_summary(db)

        assert "regions" in result
        assert len(result["regions"]) == 1
        region = result["regions"][0]
        assert region["state"] == "Jalisco"
        assert region["farm_count"] == 2
        assert region["field_count"] == 4

    def test_multiple_regions(self, db):
        """Farms in different states produce separate region entries."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=1)
        _seed_region(db, state="Ontario", farm_count=1, fields_per_farm=1)
        result = compute_regional_summary(db)

        assert len(result["regions"]) == 2
        states = {r["state"] for r in result["regions"]}
        assert states == {"Jalisco", "Ontario"}

    def test_total_hectares(self, db):
        """Region aggregates total hectares from all fields."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=2)
        result = compute_regional_summary(db)

        region = result["regions"][0]
        # field 0 = 10 ha, field 1 = 15 ha
        assert region["total_hectares"] == 25.0

    def test_avg_health(self, db):
        """Region computes average health from latest scores per field."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=2)
        result = compute_regional_summary(db)

        region = result["regions"][0]
        assert region["avg_health"] is not None
        assert 0 <= region["avg_health"] <= 100

    def test_crop_distribution(self, db):
        """Region shows crop type distribution with counts."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=2)
        result = compute_regional_summary(db)

        region = result["regions"][0]
        assert "crop_distribution" in region
        crops = {c["crop_type"] for c in region["crop_distribution"]}
        assert "maiz" in crops

    def test_treatment_success_rate(self, db):
        """Region includes treatment success rate from farmer feedback."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=2)
        result = compute_regional_summary(db)

        region = result["regions"][0]
        assert "treatment_count" in region
        assert region["treatment_count"] >= 1

    def test_top_treatments(self, db):
        """Region lists most-used treatments."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=2)
        result = compute_regional_summary(db)

        region = result["regions"][0]
        assert "top_treatments" in region
        assert len(region["top_treatments"]) >= 1

    def test_seasonal_alerts_included(self, db):
        """Region includes current seasonal alerts."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=1)
        result = compute_regional_summary(db)

        region = result["regions"][0]
        assert "seasonal_alerts" in region
        assert isinstance(region["seasonal_alerts"], list)

    def test_empty_database(self, db):
        """Empty DB returns empty regions list."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        result = compute_regional_summary(db)
        assert result["regions"] == []

    def test_state_filter(self, db):
        """Optional state filter returns only matching region."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=1)
        _seed_region(db, state="Ontario", farm_count=1, fields_per_farm=1)
        result = compute_regional_summary(db, state="Jalisco")

        assert len(result["regions"]) == 1
        assert result["regions"][0]["state"] == "Jalisco"

    def test_ancestral_methods_count(self, db):
        """Region counts treatments linked to ancestral methods."""
        from cultivos.services.intelligence.analytics import compute_regional_summary

        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=2)
        result = compute_regional_summary(db)

        region = result["regions"][0]
        assert "ancestral_methods_count" in region
        assert region["ancestral_methods_count"] >= 1


# ── API endpoint tests ───────────────────────────────────────────────


class TestRegionalSummaryAPI:
    """Tests for GET /api/intel/regional-summary endpoint."""

    def test_returns_200(self, client, db, admin_headers):
        """Endpoint returns 200 with valid auth."""
        resp = client.get("/api/intel/regional-summary", headers=admin_headers)
        assert resp.status_code == 200

    def test_returns_regions_list(self, client, db, admin_headers):
        """Response contains regions key with a list."""
        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=1)
        resp = client.get("/api/intel/regional-summary", headers=admin_headers)
        data = resp.json()
        assert "regions" in data
        assert isinstance(data["regions"], list)

    def test_region_fields_present(self, client, db, admin_headers):
        """Each region has required fields."""
        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=1)
        resp = client.get("/api/intel/regional-summary", headers=admin_headers)
        region = resp.json()["regions"][0]

        required = [
            "state", "country", "farm_count", "field_count",
            "total_hectares", "avg_health", "crop_distribution",
            "treatment_count", "top_treatments", "seasonal_alerts",
            "ancestral_methods_count",
        ]
        for field in required:
            assert field in region, f"Missing field: {field}"

    def test_state_filter_query_param(self, client, db, admin_headers):
        """State query parameter filters results."""
        _seed_region(db, state="Jalisco", farm_count=1, fields_per_farm=1)
        _seed_region(db, state="Ontario", farm_count=1, fields_per_farm=1)

        resp = client.get(
            "/api/intel/regional-summary?state=Ontario",
            headers=admin_headers,
        )
        data = resp.json()
        assert len(data["regions"]) == 1
        assert data["regions"][0]["state"] == "Ontario"

    def test_empty_returns_empty_list(self, client, db, admin_headers):
        """Empty DB returns empty regions list."""
        resp = client.get("/api/intel/regional-summary", headers=admin_headers)
        assert resp.json()["regions"] == []

    def test_requires_auth(self, db):
        """Endpoint requires admin or researcher role."""
        from cultivos.config import get_settings
        get_settings.cache_clear()
        import os
        os.environ["AUTH_ENABLED"] = "true"
        get_settings.cache_clear()
        from cultivos.app import create_app
        from cultivos.db.session import get_db
        from fastapi.testclient import TestClient

        app = create_app()
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/api/intel/regional-summary")
            assert resp.status_code in (401, 403)
        app.dependency_overrides.clear()
        os.environ.pop("AUTH_ENABLED", None)
        get_settings.cache_clear()
