"""Tests for TEK validation visualization on intel page."""

import pytest


class TestTEKValidationFrontend:
    """Frontend: TEK validation card renders on intel page."""

    def test_intel_page_has_tek_validation_panel(self, client, admin_headers):
        """intel.html contains the TEK validation panel container."""
        resp = client.get("/intel")
        assert resp.status_code == 200
        html = resp.text
        assert "intel-tek-validation" in html
        assert "Validacion TEK" in html

    def test_intel_js_has_load_tek_validation(self, client, admin_headers):
        """intel.js contains the loadTEKValidation function."""
        resp = client.get("/intel.js")
        assert resp.status_code == 200
        js = resp.text
        assert "loadTEKValidation" in js

    def test_intel_js_calls_tek_validation_on_init(self, client, admin_headers):
        """intel.js init() calls loadTEKValidation."""
        resp = client.get("/intel.js")
        assert resp.status_code == 200
        js = resp.text
        assert "loadTEKValidation()" in js

    def test_tek_validation_empty_message(self, client, admin_headers):
        """intel.js contains an empty-state message for TEK validation."""
        resp = client.get("/intel.js")
        assert resp.status_code == 200
        js = resp.text
        assert "Sin datos de validacion TEK" in js

    def test_tek_validation_shows_trust_score_bar(self, client, admin_headers):
        """intel.js renders trust score as a bar for each method."""
        resp = client.get("/intel.js")
        assert resp.status_code == 200
        js = resp.text
        assert "trust_score" in js
        assert "tek-method-card" in js

    def test_tek_validation_shows_method_name(self, client, admin_headers):
        """intel.js renders method_name for each TEK method."""
        resp = client.get("/intel.js")
        assert resp.status_code == 200
        js = resp.text
        assert "method_name" in js

    def test_tek_validation_shows_feedback_counts(self, client, admin_headers):
        """intel.js renders positive and negative feedback counts."""
        resp = client.get("/intel.js")
        assert resp.status_code == 200
        js = resp.text
        assert "positive_count" in js
        assert "negative_count" in js

    def test_tek_validation_panel_is_wide(self, client, admin_headers):
        """TEK validation panel spans full width (intel-panel-wide)."""
        resp = client.get("/intel")
        assert resp.status_code == 200
        html = resp.text
        # The panel containing tek-validation should have intel-panel-wide class
        assert 'id="intel-tek-validation"' in html
        # Check the parent panel has wide class
        idx = html.index('id="intel-tek-validation"')
        # Look backwards for the panel div
        panel_start = html.rfind('intel-panel-wide', 0, idx)
        assert panel_start != -1, "TEK validation panel should have intel-panel-wide class"
