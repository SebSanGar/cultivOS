"""Tests for cooperative WhatsApp digest aggregate (#202).

GET /api/cooperatives/{coop_id}/whatsapp-digest

Composes per-farm whatsapp-status (#185) into a cooperative digest.
Tests use monkeypatch on inner services so the composition logic is
tested deterministically without seeding the underlying alert pipelines.
"""

import pytest

from cultivos.db.models import Cooperative, Farm
from cultivos.services.intelligence import coop_whatsapp_digest as svc


@pytest.fixture
def coop(db):
    c = Cooperative(name="Cooperativa Digest", state="Jalisco")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _farm(db, coop, name="Rancho"):
    f = Farm(
        name=name,
        owner_name="Test",
        state="Jalisco",
        total_hectares=50.0,
        cooperative_id=coop.id,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _patch(monkeypatch, alerts_by_farm: dict):
    """Patch inner services keyed by farm.id.

    alerts_by_farm[farm_id] = (critical_count, high_count)
    The patched compute_active_alerts_summary returns the given counts.
    The patched compute_whatsapp_status returns a deterministic message_es.
    """

    def fake_active_alerts(farm, db):
        critical, high = alerts_by_farm.get(farm.id, (0, 0))
        safe = (critical + high) == 0
        return {
            "farm_id": farm.id,
            "critical_count": critical,
            "high_count": high,
            "top_action_es": "" if safe else "Atender estres hidrico severo",
            "next_check_date": "2026-04-13",
            "safe": safe,
        }

    def fake_whatsapp_status(farm, db):
        critical, high = alerts_by_farm.get(farm.id, (0, 0))
        has_alerts = (critical + high) > 0
        if has_alerts:
            msg = f"{farm.name} — 12/04/2026\nAlerta: Atender campo\nAccion: Revisar"
        else:
            msg = f"{farm.name} — 12/04/2026\nSin alertas activas\nMonitoreo al dia"
        return {
            "farm_id": farm.id,
            "message_es": msg,
            "has_alerts": has_alerts,
            "generated_at": "2026-04-12T12:00:00",
        }

    monkeypatch.setattr(svc, "compute_active_alerts_summary", fake_active_alerts)
    monkeypatch.setattr(svc, "compute_whatsapp_status", fake_whatsapp_status)


def test_coop_whatsapp_digest_basic(client, db, coop, monkeypatch):
    """3 farms with mixed alert states — structure correct, totals aggregated."""
    f1 = _farm(db, coop, name="Critico")
    f2 = _farm(db, coop, name="Alto")
    f3 = _farm(db, coop, name="Tranquilo")
    _patch(monkeypatch, {f1.id: (2, 1), f2.id: (0, 3), f3.id: (0, 0)})

    resp = client.get(f"/api/cooperatives/{coop.id}/whatsapp-digest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cooperative_id"] == coop.id
    assert data["total_farms"] == 3
    assert data["total_critical_alerts"] == 2
    assert data["total_high_alerts"] == 4
    assert data["farms_with_alerts"] == 2
    assert isinstance(data["top_attention_farms"], list)
    assert len(data["top_attention_farms"]) == 2  # only farms WITH alerts
    assert data["top_attention_farms"][0]["farm_name"] == "Critico"
    assert "message_es" in data["top_attention_farms"][0]
    assert isinstance(data["digest_message_es"], str)
    assert data["digest_message_es"].startswith("Cooperativa")


def test_coop_whatsapp_digest_no_alerts(client, db, coop, monkeypatch):
    """Coop with member farms but zero alerts → safe digest."""
    f1 = _farm(db, coop, name="Tranquilo1")
    f2 = _farm(db, coop, name="Tranquilo2")
    _patch(monkeypatch, {f1.id: (0, 0), f2.id: (0, 0)})

    resp = client.get(f"/api/cooperatives/{coop.id}/whatsapp-digest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_farms"] == 2
    assert data["total_critical_alerts"] == 0
    assert data["total_high_alerts"] == 0
    assert data["farms_with_alerts"] == 0
    assert data["top_attention_farms"] == []
    # Spanish "safe" message
    assert "Sin alertas" in data["digest_message_es"] or "Monitoreo" in data["digest_message_es"]


def test_coop_whatsapp_digest_spanish(client, db, coop, monkeypatch):
    """Digest message is Spanish-only farmer-facing text."""
    f1 = _farm(db, coop, name="Norte")
    _patch(monkeypatch, {f1.id: (1, 0)})

    resp = client.get(f"/api/cooperatives/{coop.id}/whatsapp-digest")
    data = resp.json()
    msg = data["digest_message_es"]
    # Must contain Spanish keyword and not English placeholders
    assert "Cooperativa" in msg
    assert "alert" not in msg.lower().replace("alerta", "")  # no English "alert"
    assert "warning" not in msg.lower()


def test_coop_whatsapp_digest_top3_ordering(client, db, coop, monkeypatch):
    """5 farms — top_attention_farms returns top 3 by (critical DESC, high DESC, farm_id ASC)."""
    f1 = _farm(db, coop, name="F1")  # (1, 0) → rank 4
    f2 = _farm(db, coop, name="F2")  # (3, 0) → rank 1
    f3 = _farm(db, coop, name="F3")  # (2, 5) → rank 2
    f4 = _farm(db, coop, name="F4")  # (2, 1) → rank 3
    f5 = _farm(db, coop, name="F5")  # (0, 0) → not in list
    _patch(
        monkeypatch,
        {
            f1.id: (1, 0),
            f2.id: (3, 0),
            f3.id: (2, 5),
            f4.id: (2, 1),
            f5.id: (0, 0),
        },
    )

    resp = client.get(f"/api/cooperatives/{coop.id}/whatsapp-digest")
    data = resp.json()
    top = data["top_attention_farms"]
    assert len(top) == 3
    assert [f["farm_name"] for f in top] == ["F2", "F3", "F4"]
    assert top[0]["critical_count"] == 3
    assert top[1]["critical_count"] == 2
    assert top[1]["high_count"] == 5
    assert top[2]["critical_count"] == 2
    assert top[2]["high_count"] == 1
    assert data["farms_with_alerts"] == 4
    assert data["total_critical_alerts"] == 8
    assert data["total_high_alerts"] == 6


def test_coop_whatsapp_digest_404(client):
    """Unknown cooperative returns 404."""
    resp = client.get("/api/cooperatives/99999/whatsapp-digest")
    assert resp.status_code == 404
