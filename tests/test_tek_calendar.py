"""Tests for GET /api/knowledge/tek-calendar endpoint."""

import pytest
from cultivos.db.models import AncestralMethod


# ── Helpers ────────────────────────────────────────────────────────────────────

def _add_method(db, name, applicable_months, crops, ecological_benefit=3, timing_rationale="Test timing"):
    method = AncestralMethod(
        name=name,
        description_es=f"Descripcion de {name}",
        region="Jalisco",
        practice_type="soil_management",
        crops=crops,
        benefits_es="Beneficios",
        applicable_months=applicable_months,
        timing_rationale=timing_rationale,
        ecological_benefit=ecological_benefit,
    )
    db.add(method)
    db.commit()
    return method


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_month_6_returns_temporal_practices(client, db):
    """Month 6 (June) is temporal season — should return methods active in June."""
    _add_method(db, "Milpa Temporal", [5, 6, 7, 8, 9, 10], ["maiz", "frijol"])
    _add_method(db, "Siembra Secas", [11, 12, 1, 2, 3, 4], ["maiz"])

    r = client.get("/api/knowledge/tek-calendar?month=6")
    assert r.status_code == 200
    data = r.json()
    names = [m["method_name"] for m in data]
    assert "Milpa Temporal" in names
    assert "Siembra Secas" not in names


def test_month_12_returns_secas_practices(client, db):
    """Month 12 (December) is secas season — should return methods active in December."""
    _add_method(db, "Milpa Temporal", [5, 6, 7, 8, 9, 10], ["maiz"])
    _add_method(db, "Siembra Secas", [11, 12, 1, 2, 3, 4], ["maiz"])

    r = client.get("/api/knowledge/tek-calendar?month=12")
    assert r.status_code == 200
    data = r.json()
    names = [m["method_name"] for m in data]
    assert "Siembra Secas" in names
    assert "Milpa Temporal" not in names


def test_crop_type_filter(client, db):
    """crop_type param filters to methods that include that crop."""
    _add_method(db, "Metodo Maiz", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], ["maiz"])
    _add_method(db, "Metodo Agave", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], ["agave"])

    r = client.get("/api/knowledge/tek-calendar?month=6&crop_type=maiz")
    assert r.status_code == 200
    data = r.json()
    names = [m["method_name"] for m in data]
    assert "Metodo Maiz" in names
    assert "Metodo Agave" not in names


def test_no_match_returns_empty_list(client, db):
    """When no methods match, return empty list (not 404)."""
    _add_method(db, "Solo Temporal", [6, 7, 8], ["maiz"])

    r = client.get("/api/knowledge/tek-calendar?month=1")
    assert r.status_code == 200
    assert r.json() == []


def test_missing_month_returns_400(client, db):
    """Omitting month param returns 400 Bad Request."""
    r = client.get("/api/knowledge/tek-calendar")
    assert r.status_code == 422  # FastAPI validation error for missing required query param


def test_sorted_by_ecological_benefit_desc(client, db):
    """Results sorted by ecological_benefit descending."""
    _add_method(db, "Low Benefit", [6, 7], ["maiz"], ecological_benefit=1)
    _add_method(db, "High Benefit", [6, 7], ["maiz"], ecological_benefit=5)
    _add_method(db, "Mid Benefit", [6, 7], ["maiz"], ecological_benefit=3)

    r = client.get("/api/knowledge/tek-calendar?month=6")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    benefits = [m["ecological_benefit"] for m in data]
    assert benefits == sorted(benefits, reverse=True)
    assert data[0]["method_name"] == "High Benefit"


def test_response_schema_fields(client, db):
    """Response entries have required schema fields."""
    _add_method(db, "Test Method", [6], ["maiz"], timing_rationale="Inicio de lluvias en Jalisco")

    r = client.get("/api/knowledge/tek-calendar?month=6")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    entry = data[0]
    assert "method_name" in entry
    assert "description_es" in entry
    assert "timing_rationale" in entry
    assert "crop_types" in entry
    assert "ecological_benefit" in entry
    assert entry["timing_rationale"] == "Inicio de lluvias en Jalisco"
