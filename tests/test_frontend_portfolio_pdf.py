"""Tests for the portfolio PDF download button on the dashboard."""


def test_portfolio_pdf_button_present_in_dashboard(client):
    """Dashboard HTML contains the portfolio PDF download button."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="btn-portfolio-pdf"' in html
    assert "Descargar Reporte de Portafolio" in html


def test_portfolio_pdf_button_has_onclick(client):
    """Button wires to downloadPortfolioPDF() function."""
    resp = client.get("/")
    html = resp.text
    assert "downloadPortfolioPDF()" in html


def test_portfolio_pdf_js_function_exists(client):
    """app.js contains the downloadPortfolioPDF function."""
    resp = client.get("/app.js")
    assert resp.status_code == 200
    assert "downloadPortfolioPDF" in resp.text


def test_portfolio_pdf_endpoint_returns_pdf_with_farms(client, db):
    """POST /api/reports/portfolio returns PDF when farms exist."""
    from cultivos.db.models import Farm, Field, HealthScore
    from cultivos.db.seeds import seed_fertilizers

    seed_fertilizers(db)
    farm = Farm(
        name="Rancho PDF", location_lat=20.6, location_lon=-103.3,
        total_hectares=50, municipality="Tequila", state="Jalisco", country="MX",
    )
    db.add(farm)
    db.flush()
    field = Field(farm_id=farm.id, name="Parcela 1", crop_type="maiz", hectares=25)
    db.add(field)
    db.flush()
    hs = HealthScore(
        field_id=field.id, score=72.0, trend="stable",
        sources=["ndvi"], breakdown={"ndvi": 72.0},
    )
    db.add(hs)
    db.commit()

    resp = client.post("/api/reports/portfolio")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b"%PDF-"


def test_portfolio_pdf_endpoint_handles_empty(client, db):
    """POST /api/reports/portfolio returns PDF even with no farms."""
    from cultivos.db.seeds import seed_fertilizers
    seed_fertilizers(db)

    resp = client.post("/api/reports/portfolio")
    assert resp.status_code == 200
    assert resp.content[:5] == b"%PDF-"
