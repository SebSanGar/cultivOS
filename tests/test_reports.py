"""Tests for farm report PDF export."""

import pytest
from cultivos.db.models import Farm, Field, HealthScore, TreatmentRecord
from cultivos.db.seeds import seed_fertilizers


@pytest.fixture(autouse=True)
def seed_data(db):
    seed_fertilizers(db)


def _create_farm_with_fields(db, with_fields=True):
    """Helper: create a farm and optionally add fields with health + treatment data."""
    farm = Farm(name="Rancho El Sol", owner_name="Juan Perez",
                location_lat=20.6, location_lon=-103.3,
                total_hectares=50.0, municipality="Zapopan",
                state="Jalisco", country="MX")
    db.add(farm)
    db.flush()

    if with_fields:
        field = Field(farm_id=farm.id, name="Parcela Norte", crop_type="maiz", hectares=25.0)
        db.add(field)
        db.flush()

        hs = HealthScore(field_id=field.id, score=72.5, trend="improving",
                         sources=["ndvi", "soil"], breakdown={"ndvi": 0.75, "soil": 0.70})
        db.add(hs)

        tr = TreatmentRecord(field_id=field.id, health_score_used=72.5,
                             problema="pH bajo", causa_probable="Suelo acido",
                             tratamiento="Aplicar cal agricola 2 ton/ha",
                             costo_estimado_mxn=3000, urgencia="media",
                             prevencion="Monitorear pH cada 3 meses", organic=True)
        db.add(tr)
        db.flush()

    return farm


class TestGenerateReportPDF:
    def test_generate_report_pdf(self, client, db, admin_headers):
        """POST /api/farms/{id}/report returns PDF with farm name, fields, latest health scores."""
        farm = _create_farm_with_fields(db)
        resp = client.post(f"/api/farms/{farm.id}/report", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        # PDF magic bytes
        assert resp.content[:5] == b"%PDF-"
        # Farm name should appear somewhere in the PDF content
        assert b"Rancho El Sol" in resp.content

    def test_report_includes_recommendations(self, client, db, admin_headers):
        """PDF includes active treatment recommendations."""
        farm = _create_farm_with_fields(db)
        resp = client.post(f"/api/farms/{farm.id}/report", headers=admin_headers)
        assert resp.status_code == 200
        # Treatment text should appear in PDF
        assert b"cal agricola" in resp.content

    def test_report_spanish(self, client, db, admin_headers):
        """All text in the PDF is in Spanish."""
        farm = _create_farm_with_fields(db)
        resp = client.post(f"/api/farms/{farm.id}/report", headers=admin_headers)
        assert resp.status_code == 200
        content = resp.content
        # Spanish section headers should be present
        assert b"Reporte de Salud" in content
        assert b"Parcelas" in content
        # English should NOT appear
        assert b"Health Report" not in content
        assert b"Fields" not in content

    def test_report_no_fields(self, client, db, admin_headers):
        """Farm with no fields generates report with 'Sin parcelas registradas'."""
        farm = _create_farm_with_fields(db, with_fields=False)
        resp = client.post(f"/api/farms/{farm.id}/report", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"
        assert b"Sin parcelas registradas" in resp.content

    def test_report_farm_not_found(self, client, admin_headers):
        """Report for nonexistent farm returns 404."""
        resp = client.post("/api/farms/9999/report", headers=admin_headers)
        assert resp.status_code == 404
