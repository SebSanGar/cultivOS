"""Tests for treatment effectiveness dashboard frontend elements on /intel page.

Verifies: ranked treatment list renders, composite score bars, crop type filter,
and the JS fetches from the report endpoint.
"""


def test_intel_has_treatment_report_section(client):
    """Intel page has the treatment effectiveness report container."""
    resp = client.get("/intel")
    assert resp.status_code == 200
    assert 'id="intel-treatment-report"' in resp.text


def test_intel_has_crop_type_filter(client):
    """Intel page has a crop type filter dropdown for treatment effectiveness."""
    resp = client.get("/intel")
    html = resp.text
    assert 'id="treatment-crop-filter"' in html


def test_intel_js_fetches_treatment_report(client):
    """intel.js references the treatment-effectiveness-report endpoint."""
    resp = client.get("/intel.js")
    assert resp.status_code == 200
    assert "treatment-effectiveness-report" in resp.text


def test_intel_js_renders_composite_score_bar(client):
    """intel.js renders composite score as a visual bar."""
    resp = client.get("/intel.js")
    assert "composite_score" in resp.text
    assert "score-bar" in resp.text


def test_intel_js_renders_success_rate(client):
    """intel.js renders feedback_success_rate percentage."""
    resp = client.get("/intel.js")
    assert "feedback_success_rate" in resp.text


def test_intel_js_renders_health_delta(client):
    """intel.js renders avg_health_delta."""
    resp = client.get("/intel.js")
    assert "avg_health_delta" in resp.text


def test_intel_js_handles_crop_filter(client):
    """intel.js has logic to filter by crop type."""
    resp = client.get("/intel.js")
    assert "crop_type" in resp.text
    assert "treatment-crop-filter" in resp.text
