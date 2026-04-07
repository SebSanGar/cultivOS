"""Tests for FODECIJAL grant narrative PDF generation."""

import pytest
from datetime import datetime, timedelta

from cultivos.services.reports import generate_fodecijal_report_pdf


# ---------------------------------------------------------------------------
# Pure service tests
# ---------------------------------------------------------------------------

class TestGenerateFodecijalReportPdf:
    """Test the pure PDF generation function."""

    def _make_platform_stats(self):
        return {
            "api_endpoints": 100,
            "frontend_pages": 53,
            "passing_tests": 2221,
            "route_files": 40,
            "total_farms": 5,
            "total_fields": 12,
            "total_hectares": 180.0,
        }

    def _make_cerebro_summary(self):
        return {
            "health_scoring_sources": ["NDVI", "Thermal", "Soil", "Weather"],
            "treatment_methods": 21,
            "ancestral_methods": 8,
            "supported_crops": 11,
            "organic_only": True,
        }

    def _make_pipeline_status(self):
        return [
            {"name": "NDVI Multispectral", "status": "operational", "records": 45},
            {"name": "Thermal Stress", "status": "operational", "records": 30},
            {"name": "Microbiome Analysis", "status": "operational", "records": 15},
            {"name": "Soil CSV Import", "status": "operational", "records": 60},
            {"name": "Voice/WhatsApp", "status": "planned", "records": 0},
        ]

    def _make_carbon_summary(self):
        return {
            "total_co2e_tonnes": 245.5,
            "avg_soc_tonnes_per_ha": 1.36,
        }

    def _make_farm_details(self):
        return [
            {
                "name": "Rancho Los Agaves",
                "municipality": "Tequila",
                "state": "Jalisco",
                "hectares": 45.0,
                "field_count": 3,
                "avg_health": 72.5,
                "treatment_count": 8,
            },
            {
                "name": "Granja El Maizal",
                "municipality": "Zapopan",
                "state": "Jalisco",
                "hectares": 30.0,
                "field_count": 2,
                "avg_health": 65.0,
                "treatment_count": 5,
            },
        ]

    def test_returns_bytes(self):
        result = generate_fodecijal_report_pdf(
            platform_stats=self._make_platform_stats(),
            cerebro_summary=self._make_cerebro_summary(),
            pipeline_status=self._make_pipeline_status(),
            carbon_summary=self._make_carbon_summary(),
            farm_details=self._make_farm_details(),
        )
        assert isinstance(result, bytes)

    def test_starts_with_pdf_header(self):
        result = generate_fodecijal_report_pdf(
            platform_stats=self._make_platform_stats(),
            cerebro_summary=self._make_cerebro_summary(),
            pipeline_status=self._make_pipeline_status(),
            carbon_summary=self._make_carbon_summary(),
            farm_details=self._make_farm_details(),
        )
        assert result[:5] == b"%PDF-"

    def test_contains_fodecijal_title(self):
        result = generate_fodecijal_report_pdf(
            platform_stats=self._make_platform_stats(),
            cerebro_summary=self._make_cerebro_summary(),
            pipeline_status=self._make_pipeline_status(),
            carbon_summary=self._make_carbon_summary(),
            farm_details=self._make_farm_details(),
        )
        assert b"FODECIJAL" in result

    def test_contains_cultivOS_branding(self):
        result = generate_fodecijal_report_pdf(
            platform_stats=self._make_platform_stats(),
            cerebro_summary=self._make_cerebro_summary(),
            pipeline_status=self._make_pipeline_status(),
            carbon_summary=self._make_carbon_summary(),
            farm_details=self._make_farm_details(),
        )
        assert b"cultivOS" in result

    def test_contains_cerebro_section(self):
        result = generate_fodecijal_report_pdf(
            platform_stats=self._make_platform_stats(),
            cerebro_summary=self._make_cerebro_summary(),
            pipeline_status=self._make_pipeline_status(),
            carbon_summary=self._make_carbon_summary(),
            farm_details=self._make_farm_details(),
        )
        assert b"Cerebro" in result

    def test_contains_carbon_section(self):
        result = generate_fodecijal_report_pdf(
            platform_stats=self._make_platform_stats(),
            cerebro_summary=self._make_cerebro_summary(),
            pipeline_status=self._make_pipeline_status(),
            carbon_summary=self._make_carbon_summary(),
            farm_details=self._make_farm_details(),
        )
        assert b"Carbono" in result

    def test_contains_pipeline_section(self):
        result = generate_fodecijal_report_pdf(
            platform_stats=self._make_platform_stats(),
            cerebro_summary=self._make_cerebro_summary(),
            pipeline_status=self._make_pipeline_status(),
            carbon_summary=self._make_carbon_summary(),
            farm_details=self._make_farm_details(),
        )
        # Pipeline data section
        assert b"NDVI" in result

    def test_contains_farm_names(self):
        result = generate_fodecijal_report_pdf(
            platform_stats=self._make_platform_stats(),
            cerebro_summary=self._make_cerebro_summary(),
            pipeline_status=self._make_pipeline_status(),
            carbon_summary=self._make_carbon_summary(),
            farm_details=self._make_farm_details(),
        )
        assert b"Rancho Los Agaves" in result
        assert b"Granja El Maizal" in result

    def test_empty_farms_still_generates(self):
        result = generate_fodecijal_report_pdf(
            platform_stats=self._make_platform_stats(),
            cerebro_summary=self._make_cerebro_summary(),
            pipeline_status=self._make_pipeline_status(),
            carbon_summary=self._make_carbon_summary(),
            farm_details=[],
        )
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_spanish_text_present(self):
        result = generate_fodecijal_report_pdf(
            platform_stats=self._make_platform_stats(),
            cerebro_summary=self._make_cerebro_summary(),
            pipeline_status=self._make_pipeline_status(),
            carbon_summary=self._make_carbon_summary(),
            farm_details=self._make_farm_details(),
        )
        # Key Spanish sections
        assert b"Plataforma" in result
        assert b"Tratamiento" in result or b"tratamiento" in result


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestFodecijalReportEndpoint:
    """Test GET /api/reports/fodecijal."""

    def test_returns_pdf(self, client):
        resp = client.get("/api/reports/fodecijal")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    def test_pdf_header(self, client):
        resp = client.get("/api/reports/fodecijal")
        assert resp.content[:5] == b"%PDF-"

    def test_content_disposition(self, client):
        resp = client.get("/api/reports/fodecijal")
        cd = resp.headers.get("content-disposition", "")
        assert "fodecijal" in cd.lower()
        assert ".pdf" in cd

    def test_with_seeded_data(self, client, db):
        """With real data, PDF should contain farm info."""
        from cultivos.db.models import Farm, Field

        farm = Farm(
            name="Rancho Test FODECIJAL",
            municipality="Tequila",
            state="Jalisco",
            total_hectares=50.0,
        )
        db.add(farm)
        db.flush()

        field = Field(
            farm_id=farm.id,
            name="Parcela A",
            crop_type="agave",
            hectares=25.0,
        )
        db.add(field)
        db.commit()

        resp = client.get("/api/reports/fodecijal")
        assert resp.status_code == 200
        assert b"Rancho Test FODECIJAL" in resp.content

    def test_with_complete_data(self, client, db):
        """With full pipeline data, PDF generates without error."""
        from cultivos.db.models import Farm, Field, NDVIResult, SoilAnalysis, TreatmentRecord, HealthScore

        farm = Farm(
            name="Demo Farm Complete",
            municipality="Zapopan",
            state="Jalisco",
            total_hectares=40.0,
        )
        db.add(farm)
        db.flush()

        field = Field(
            farm_id=farm.id,
            name="Campo 1",
            crop_type="maiz",
            hectares=20.0,
        )
        db.add(field)
        db.flush()

        # Add pipeline data
        db.add(NDVIResult(
            field_id=field.id,
            ndvi_mean=0.72,
            ndvi_std=0.12,
            ndvi_min=0.45,
            ndvi_max=0.88,
            pixels_total=10000,
            stress_pct=8.5,
            zones=[{"zone": "healthy", "pct": 91.5}],
            analyzed_at=datetime.utcnow(),
        ))
        db.add(SoilAnalysis(
            field_id=field.id,
            ph=6.5,
            organic_matter_pct=3.2,
            nitrogen_ppm=45.0,
            phosphorus_ppm=30.0,
            potassium_ppm=200.0,
            sampled_at=datetime.utcnow(),
        ))
        db.add(TreatmentRecord(
            field_id=field.id,
            health_score_used=68.5,
            problema="Deficiencia de nitrogeno",
            causa_probable="Suelo agotado",
            tratamiento="Composta organica",
            prevencion="Rotacion de cultivos",
            urgencia="media",
            costo_estimado_mxn=2500,
        ))
        db.add(HealthScore(
            field_id=field.id,
            score=68.5,
            trend="improving",
            scored_at=datetime.utcnow(),
        ))
        db.commit()

        resp = client.get("/api/reports/fodecijal")
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"


# ---------------------------------------------------------------------------
# Frontend page tests
# ---------------------------------------------------------------------------

class TestFodecijalReportPage:
    """Test /reporte-fodecijal frontend page."""

    def test_page_loads(self, client):
        resp = client.get("/reporte-fodecijal")
        assert resp.status_code == 200

    def test_page_contains_title(self, client):
        resp = client.get("/reporte-fodecijal")
        text = resp.text
        assert "FODECIJAL" in text

    def test_page_contains_generate_button(self, client):
        resp = client.get("/reporte-fodecijal")
        text = resp.text
        assert "generate-btn" in text or "generar" in text.lower()

    def test_page_contains_description(self, client):
        resp = client.get("/reporte-fodecijal")
        text = resp.text
        assert "cultivOS" in text

    def test_page_has_spanish_content(self, client):
        resp = client.get("/reporte-fodecijal")
        text = resp.text
        assert "Generar" in text or "Reporte" in text

    def test_page_has_download_section(self, client):
        resp = client.get("/reporte-fodecijal")
        text = resp.text
        assert "download" in text.lower() or "descargar" in text.lower() or "pdf" in text.lower()

    def test_page_links_to_api(self, client):
        resp = client.get("/reporte-fodecijal")
        text = resp.text
        assert "/api/reports/fodecijal" in text

    def test_html_structure(self, client):
        resp = client.get("/reporte-fodecijal")
        text = resp.text
        assert "<html" in text
        assert "<body" in text
        assert "report-container" in text or "fodecijal" in text.lower()
