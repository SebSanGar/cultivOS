"""Tests for multi-farm portfolio PDF report."""

import pytest
from datetime import datetime
from cultivos.db.models import (
    Farm, Field, HealthScore, NDVIResult, SoilAnalysis, TreatmentRecord,
)
from cultivos.db.seeds import seed_fertilizers


@pytest.fixture(autouse=True)
def seed_data(db):
    seed_fertilizers(db)


def _create_farms(db, count=2):
    """Create multiple farms with fields, health scores, and treatments."""
    farms = []
    for i in range(count):
        farm = Farm(
            name=f"Rancho {i + 1}", owner_name=f"Productor {i + 1}",
            location_lat=20.6 + i * 0.1, location_lon=-103.3,
            total_hectares=30.0 + i * 10, municipality="Zapopan",
            state="Jalisco", country="MX",
        )
        db.add(farm)
        db.flush()

        field = Field(
            farm_id=farm.id, name=f"Parcela {i + 1}A",
            crop_type="maiz", hectares=15.0 + i * 5,
        )
        db.add(field)
        db.flush()

        hs = HealthScore(
            field_id=field.id, score=65.0 + i * 10, trend="improving",
            sources=["ndvi", "soil"], breakdown={"ndvi": 0.7, "soil": 0.6},
        )
        db.add(hs)

        tr = TreatmentRecord(
            field_id=field.id, health_score_used=65.0 + i * 10,
            problema="Nitrogeno bajo", causa_probable="Desgaste",
            tratamiento="Composta 5 ton/ha", costo_estimado_mxn=4000,
            urgencia="media", prevencion="Rotar cultivos", organic=True,
        )
        db.add(tr)

        soil = SoilAnalysis(
            field_id=field.id, ph=6.2 + i * 0.3,
            organic_matter_pct=3.0 + i * 0.5, depth_cm=30.0,
            sampled_at=datetime(2026, 3, 1),
        )
        db.add(soil)
        db.flush()

        farms.append(farm)

    return farms


class TestPortfolioReportPDF:
    """POST /api/reports/portfolio returns a multi-farm PDF."""

    def test_portfolio_report_returns_pdf(self, client, db, admin_headers):
        """Returns valid PDF with correct content-type."""
        _create_farms(db, count=2)
        resp = client.post("/api/reports/portfolio", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"

    def test_portfolio_contains_farm_names(self, client, db, admin_headers):
        """PDF contains each farm's name."""
        _create_farms(db, count=3)
        resp = client.post("/api/reports/portfolio", headers=admin_headers)
        assert resp.status_code == 200
        assert b"Rancho 1" in resp.content
        assert b"Rancho 2" in resp.content
        assert b"Rancho 3" in resp.content

    def test_portfolio_contains_executive_summary(self, client, db, admin_headers):
        """PDF contains executive summary section header."""
        _create_farms(db, count=2)
        resp = client.post("/api/reports/portfolio", headers=admin_headers)
        assert resp.status_code == 200
        assert b"Resumen Ejecutivo" in resp.content

    def test_portfolio_contains_health_scores(self, client, db, admin_headers):
        """PDF includes health score values for farms."""
        _create_farms(db, count=2)
        resp = client.post("/api/reports/portfolio", headers=admin_headers)
        assert resp.status_code == 200
        # Health scores 65.0 and 75.0 formatted as "65.0" and "75.0"
        assert b"65.0" in resp.content
        assert b"75.0" in resp.content

    def test_portfolio_single_farm(self, client, db, admin_headers):
        """Works with a single farm."""
        _create_farms(db, count=1)
        resp = client.post("/api/reports/portfolio", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"
        assert b"Rancho 1" in resp.content

    def test_portfolio_no_farms(self, client, db, admin_headers):
        """Returns PDF even with no farms (empty portfolio)."""
        resp = client.post("/api/reports/portfolio", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"
        assert b"Sin granjas registradas" in resp.content

    def test_portfolio_contains_treatment_info(self, client, db, admin_headers):
        """PDF includes treatment effectiveness section."""
        _create_farms(db, count=2)
        resp = client.post("/api/reports/portfolio", headers=admin_headers)
        assert resp.status_code == 200
        assert b"Tratamientos" in resp.content

    def test_portfolio_contains_carbon_section(self, client, db, admin_headers):
        """PDF includes carbon sequestration aggregate."""
        _create_farms(db, count=2)
        resp = client.post("/api/reports/portfolio", headers=admin_headers)
        assert resp.status_code == 200
        assert b"Carbono" in resp.content


class TestPortfolioReportPure:
    """Test the pure generation function directly."""

    def test_generate_portfolio_report_pdf_returns_bytes(self):
        """Pure function returns PDF bytes from data dicts."""
        from cultivos.services.reports import generate_portfolio_report_pdf

        result = generate_portfolio_report_pdf(
            farms_summary={
                "total_farms": 2,
                "total_hectares": 70.0,
                "avg_health_score": 70.0,
                "total_fields": 4,
            },
            farm_details=[
                {
                    "name": "Rancho Prueba",
                    "municipality": "Zapopan",
                    "state": "Jalisco",
                    "hectares": 30.0,
                    "avg_health": 72.5,
                    "health_trend": "improving",
                    "field_count": 2,
                    "treatment_count": 3,
                },
            ],
            carbon_summary={
                "total_co2e_tonnes": 150.0,
                "avg_soc_tonnes_per_ha": 45.0,
            },
            economic_summary={
                "total_savings_mxn": 414000,
                "water_savings_mxn": 160000,
                "fertilizer_savings_mxn": 100000,
                "yield_improvement_mxn": 154000,
            },
        )
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"
        assert b"Rancho Prueba" in result

    def test_generate_portfolio_empty(self):
        """Pure function handles empty portfolio."""
        from cultivos.services.reports import generate_portfolio_report_pdf

        result = generate_portfolio_report_pdf(
            farms_summary={
                "total_farms": 0,
                "total_hectares": 0,
                "avg_health_score": 0,
                "total_fields": 0,
            },
            farm_details=[],
            carbon_summary={"total_co2e_tonnes": 0, "avg_soc_tonnes_per_ha": 0},
            economic_summary={
                "total_savings_mxn": 0,
                "water_savings_mxn": 0,
                "fertilizer_savings_mxn": 0,
                "yield_improvement_mxn": 0,
            },
        )
        assert isinstance(result, bytes)
        assert b"Sin granjas registradas" in result
