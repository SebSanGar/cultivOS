"""Tests for cooperative FODECIJAL evidence pack (task #208).

GET /api/cooperatives/{coop_id}/evidence-pack

Composes 6 existing services into one grant-ready rollup. Tests monkeypatch
the 6 compute functions so we verify aggregation/strength-weakness logic
independently of the underlying services' internals.
"""

import pytest

from cultivos.db.models import Cooperative


@pytest.fixture
def coop(db):
    c = Cooperative(name="Cooperativa Evidencia", state="Jalisco")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _patch_all(monkeypatch, readiness=70.0, portfolio_health=65.0,
               carbon=12.5, outbreak="medium", regen=60.0, shannon=1.234):
    """Patch the 6 composed compute functions at the service module path."""
    from cultivos.services.intelligence import coop_evidence_pack as svc

    class _ReadinessOut:
        def __init__(self, score): self.overall_score = score

    monkeypatch.setattr(
        svc, "compute_fodecijal_readiness",
        lambda coop, db: _ReadinessOut(readiness),
    )
    monkeypatch.setattr(
        svc, "compute_portfolio_health",
        lambda coop, db: {"avg_health_score": portfolio_health},
    )
    monkeypatch.setattr(
        svc, "compute_coop_carbon_summary",
        lambda coop, db: {"total_co2e_baseline_t": carbon},
    )
    monkeypatch.setattr(
        svc, "compute_outbreak_risk",
        lambda coop, db: {"overall_risk_level": outbreak},
    )
    monkeypatch.setattr(
        svc, "compute_regen_adoption",
        lambda coop, days, db: {"overall_regen_score_avg": regen},
    )
    monkeypatch.setattr(
        svc, "compute_coop_crop_diversity",
        lambda coop_id, db: {"shannon_index": shannon},
    )


def test_evidence_pack_basic(client, db, coop, monkeypatch):
    _patch_all(monkeypatch)
    resp = client.get(f"/api/cooperatives/{coop.id}/evidence-pack")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["cooperative_name"] == "Cooperativa Evidencia"
    assert data["readiness_score"] == 70.0
    assert data["portfolio_health_avg"] == 65.0
    assert data["total_co2e_sequestered_t"] == 12.5
    assert data["outbreak_risk_level"] == "medium"
    assert data["regen_adoption_pct"] == 60.0
    assert data["shannon_diversity_index"] == 1.234
    assert "top_strength_es" in data
    assert "top_weakness_es" in data
    assert "generated_at" in data


def test_evidence_pack_strength_identified(client, db, coop, monkeypatch):
    # Readiness highest → strength mentions readiness
    _patch_all(monkeypatch, readiness=90.0, portfolio_health=50.0, regen=40.0)
    resp = client.get(f"/api/cooperatives/{coop.id}/evidence-pack")
    assert resp.status_code == 200
    data = resp.json()
    assert "preparación" in data["top_strength_es"].lower() or \
           "readiness" in data["top_strength_es"].lower() or \
           "fodecijal" in data["top_strength_es"].lower()
    # Lowest is regen_adoption (40) → weakness mentions adopción regenerativa
    assert "regenerativ" in data["top_weakness_es"].lower() or \
           "adopción" in data["top_weakness_es"].lower()


def test_evidence_pack_weakness_identified(client, db, coop, monkeypatch):
    # Portfolio health lowest → weakness mentions salud/portfolio
    _patch_all(monkeypatch, readiness=80.0, portfolio_health=20.0, regen=70.0)
    resp = client.get(f"/api/cooperatives/{coop.id}/evidence-pack")
    assert resp.status_code == 200
    data = resp.json()
    assert "salud" in data["top_weakness_es"].lower() or \
           "portafolio" in data["top_weakness_es"].lower() or \
           "portfolio" in data["top_weakness_es"].lower()


def test_evidence_pack_empty_coop(client, db, coop, monkeypatch):
    # All zeros / None — service must still return a valid payload
    _patch_all(
        monkeypatch,
        readiness=0.0, portfolio_health=None, carbon=0.0,
        outbreak="low", regen=0.0, shannon=0.0,
    )
    resp = client.get(f"/api/cooperatives/{coop.id}/evidence-pack")
    assert resp.status_code == 200
    data = resp.json()
    assert data["readiness_score"] == 0.0
    assert data["portfolio_health_avg"] is None
    assert data["total_co2e_sequestered_t"] == 0.0
    assert data["regen_adoption_pct"] == 0.0
    assert data["shannon_diversity_index"] == 0.0
    # Still produces strength + weakness strings (non-empty)
    assert data["top_strength_es"]
    assert data["top_weakness_es"]


def test_evidence_pack_404(client, db):
    resp = client.get("/api/cooperatives/999999/evidence-pack")
    assert resp.status_code == 404
