"""Tests for PDF report download button on farm dashboard (index.html / app.js)."""


class TestFarmPdfDownloadButton:
    """PDF download button appears on farm dashboard when a farm is selected."""

    def test_download_button_exists_in_dashboard_html(self, client):
        """Farm dashboard contains a 'Descargar Reporte PDF' button."""
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.text
        assert 'id="btn-farm-pdf"' in html
        assert "Descargar Reporte PDF" in html

    def test_download_button_in_field_panel(self, client):
        """PDF button is inside the field-panel-actions area (next to CSV export)."""
        resp = client.get("/")
        html = resp.text
        actions_start = html.index('class="field-panel-actions"')
        # Find closing div after actions section
        actions_section = html[actions_start:actions_start + 500]
        assert 'id="btn-farm-pdf"' in actions_section

    def test_app_js_has_download_farm_pdf_function(self, client):
        """app.js contains the downloadFarmPDF function."""
        resp = client.get("/app.js")
        assert resp.status_code == 200
        js = resp.text
        assert "downloadFarmPDF" in js

    def test_download_function_calls_report_api(self, client):
        """downloadFarmPDF function POSTs to /api/farms/{id}/report."""
        resp = client.get("/app.js")
        js = resp.text
        assert "downloadFarmPDF" in js
        assert "/report" in js
        assert "POST" in js

    def test_download_function_uses_blob(self, client):
        """downloadFarmPDF creates a blob URL for PDF download."""
        resp = client.get("/app.js")
        js = resp.text
        # Look for blob handling in the context of PDF download
        assert "blob" in js.lower() or "Blob" in js

    def test_pdf_report_endpoint_returns_pdf(self, client, admin_headers):
        """POST /api/farms/{id}/report returns a PDF (backend sanity check)."""
        farm = client.post("/api/farms", json={
            "name": "Rancho Dashboard PDF",
            "owner_name": "Test",
            "location_lat": 20.67,
            "location_lon": -103.35,
            "total_hectares": 10,
            "municipality": "Zapopan",
            "state": "Jalisco",
            "country": "MX",
        }, headers=admin_headers).json()

        resp = client.post(f"/api/farms/{farm['id']}/report")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert b"%PDF" in resp.content
