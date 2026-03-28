"""Tests for PDF report download button on field detail page."""

import pytest


class TestPdfDownloadButton:
    """PDF download button appears on field detail page and backend generates PDF."""

    def test_download_button_exists_in_html(self, client):
        """Field detail page contains a 'Descargar Reporte' download button."""
        resp = client.get("/campo")
        assert resp.status_code == 200
        html = resp.text
        assert 'id="btn-download-report"' in html
        assert "Descargar Reporte" in html

    def test_download_button_in_header(self, client):
        """Download button is inside the campo-header section."""
        resp = client.get("/campo")
        html = resp.text
        # Button should be in the header area (campo-header div)
        header_start = html.index('class="campo-header"')
        header_end = html.index("</div>", html.index("</div>", header_start) + 1)
        header_section = html[header_start:header_end]
        assert 'id="btn-download-report"' in header_section

    def test_field_js_has_download_function(self, client):
        """field.js contains the downloadReport function."""
        resp = client.get("/field.js")
        assert resp.status_code == 200
        js = resp.text
        assert "downloadReport" in js

    def test_download_function_calls_report_api(self, client):
        """downloadReport function fetches POST /api/farms/{farmId}/report."""
        resp = client.get("/field.js")
        js = resp.text
        assert "/report" in js
        assert "POST" in js

    def test_download_handles_blob(self, client):
        """downloadReport creates a blob URL for PDF download."""
        resp = client.get("/field.js")
        js = resp.text
        assert "blob" in js.lower() or "Blob" in js

    def test_pdf_report_endpoint_returns_pdf(self, client, admin_headers):
        """POST /api/farms/{id}/report returns a PDF for a farm with data."""
        farm = client.post("/api/farms", json={
            "name": "Rancho PDF",
            "owner_name": "Test",
            "location_lat": 20.67,
            "location_lon": -103.35,
            "total_hectares": 10,
            "municipality": "Zapopan",
            "state": "Jalisco",
            "country": "MX",
        }, headers=admin_headers).json()

        field = client.post(f"/api/farms/{farm['id']}/fields", json={
            "name": "Parcela PDF",
            "crop_type": "maiz",
            "hectares": 5,
        }).json()

        # Add health data so report has content
        client.post(f"/api/farms/{farm['id']}/fields/{field['id']}/health")

        resp = client.post(f"/api/farms/{farm['id']}/report")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert b"%PDF" in resp.content

    def test_pdf_report_404_for_missing_farm(self, client):
        """POST /api/farms/9999/report returns 404."""
        resp = client.post("/api/farms/9999/report")
        assert resp.status_code == 404

    def test_download_button_has_error_handling(self, client):
        """downloadReport function has error handling (try/catch or .catch)."""
        resp = client.get("/field.js")
        js = resp.text
        assert "catch" in js or "error" in js.lower()
