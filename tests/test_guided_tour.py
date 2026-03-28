"""Tests for guided tour system — tooltip-based walkthrough for FODECIJAL reviewers."""

import pytest


class TestGuidedTourAssets:
    """Tour JS and CSS are served and included in pages."""

    def test_tour_js_served(self, client):
        """tour.js is accessible as a static asset."""
        resp = client.get("/tour.js")
        assert resp.status_code == 200
        assert "application/javascript" in resp.headers.get("content-type", "") or "text/javascript" in resp.headers.get("content-type", "")

    def test_tour_js_has_start_function(self, client):
        """tour.js exports a startTour function."""
        resp = client.get("/tour.js")
        assert "startTour" in resp.text

    def test_tour_js_has_exit_function(self, client):
        """tour.js has an exitTour function for early exit."""
        resp = client.get("/tour.js")
        assert "exitTour" in resp.text

    def test_tour_js_has_step_navigation(self, client):
        """tour.js has next/prev step navigation."""
        resp = client.get("/tour.js")
        text = resp.text
        assert "nextTourStep" in text or "nextStep" in text
        assert "prevTourStep" in text or "prevStep" in text

    def test_tour_js_uses_session_storage(self, client):
        """tour.js uses sessionStorage for cross-page tour state."""
        resp = client.get("/tour.js")
        assert "sessionStorage" in resp.text


class TestTourIntegrationInPages:
    """Tour script is included in all 4 tour pages."""

    def test_dashboard_includes_tour(self, client):
        """Dashboard (index.html) includes tour.js."""
        resp = client.get("/")
        assert "tour.js" in resp.text

    def test_field_detail_includes_tour(self, client):
        """Field detail page includes tour.js."""
        resp = client.get("/campo")
        assert "tour.js" in resp.text

    def test_intel_includes_tour(self, client):
        """Intel page includes tour.js."""
        resp = client.get("/intel")
        assert "tour.js" in resp.text

    def test_knowledge_includes_tour(self, client):
        """Knowledge page includes tour.js."""
        resp = client.get("/conocimiento")
        assert "tour.js" in resp.text


class TestTourStepDefinitions:
    """Tour defines steps for each page."""

    def test_tour_has_dashboard_steps(self, client):
        """Tour defines steps targeting dashboard elements."""
        resp = client.get("/tour.js")
        text = resp.text
        assert "dashboard" in text.lower() or "stats-strip" in text or "farm-grid" in text

    def test_tour_has_field_steps(self, client):
        """Tour defines steps targeting field detail elements."""
        resp = client.get("/tour.js")
        text = resp.text
        assert "campo" in text.lower() or "field" in text.lower()

    def test_tour_has_intel_steps(self, client):
        """Tour defines steps targeting intel page elements."""
        resp = client.get("/tour.js")
        assert "intel" in resp.text.lower()

    def test_tour_has_knowledge_steps(self, client):
        """Tour defines steps targeting knowledge page elements."""
        resp = client.get("/tour.js")
        assert "conocimiento" in resp.text.lower() or "knowledge" in resp.text.lower()


class TestWalkthroughTourButton:
    """Walkthrough page has a button to start the guided tour."""

    def test_walkthrough_has_tour_button(self, client):
        """Walkthrough page has a button/link to start the guided tour."""
        resp = client.get("/recorrido")
        html = resp.text
        assert "startTour" in html or "iniciar-tour" in html or "tour" in html.lower()


class TestTourCSS:
    """Tour overlay styles exist in styles.css."""

    def test_tour_overlay_styles(self, client):
        """styles.css has tour overlay/tooltip classes."""
        resp = client.get("/styles.css")
        text = resp.text
        assert "tour-overlay" in text or "tour-tooltip" in text

    def test_tour_highlight_styles(self, client):
        """styles.css has tour highlight/spotlight styles."""
        resp = client.get("/styles.css")
        text = resp.text
        assert "tour-highlight" in text or "tour-spotlight" in text
