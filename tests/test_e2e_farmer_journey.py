"""End-to-end farmer journey integration test.

Walks the full Cerebro pipeline from farm creation to treatment effectiveness,
proving the entire data flow works as an integrated system.

Pipeline: create farm → create field → POST soil → POST NDVI → POST thermal
→ POST microbiome → POST health score → POST treatment recommendations
→ POST treatment applied → GET treatment effectiveness

This test validates FODECIJAL TRL 4→5: integrated system operation.
"""

from datetime import datetime, timedelta

import pytest

from cultivos.db.models import HealthScore


class TestFarmerJourneyE2E:
    """Full pipeline integration test — one long journey through all Cerebro endpoints."""

    def test_full_pipeline_farm_to_effectiveness(self, client, db, admin_headers):
        """Walk the entire farmer journey: data in → intelligence out → action → result."""

        # ── Step 1: Create farm ──────────────────────────────────────
        farm_resp = client.post(
            "/api/farms",
            json={
                "name": "Finca El Nopal E2E",
                "owner_name": "Don Miguel",
                "location_lat": 20.6597,
                "location_lon": -103.3496,
                "total_hectares": 12.0,
                "municipality": "Tlajomulco",
                "state": "Jalisco",
                "country": "MX",
            },
            headers=admin_headers,
        )
        assert farm_resp.status_code == 201, f"Farm creation failed: {farm_resp.text}"
        farm = farm_resp.json()
        farm_id = farm["id"]
        assert farm["name"] == "Finca El Nopal E2E"

        # ── Step 2: Create field ─────────────────────────────────────
        field_resp = client.post(
            f"/api/farms/{farm_id}/fields",
            json={
                "name": "Parcela Maiz Norte",
                "crop_type": "Maiz",
                "hectares": 4.5,
            },
            headers=admin_headers,
        )
        assert field_resp.status_code == 201, f"Field creation failed: {field_resp.text}"
        field = field_resp.json()
        field_id = field["id"]
        assert field["crop_type"] == "Maiz"

        base = f"/api/farms/{farm_id}/fields/{field_id}"

        # ── Step 3: Submit soil analysis ─────────────────────────────
        soil_resp = client.post(
            f"{base}/soil",
            json={
                "sampled_at": "2026-03-01T10:00:00",
                "ph": 6.5,
                "organic_matter_pct": 3.2,
                "nitrogen_ppm": 45.0,
                "phosphorus_ppm": 22.0,
                "potassium_ppm": 180.0,
                "moisture_pct": 28.0,
                "texture": "franco-arcilloso",
            },
        )
        assert soil_resp.status_code == 201, f"Soil creation failed: {soil_resp.text}"
        soil = soil_resp.json()
        assert soil["ph"] == 6.5

        # ── Step 4: Submit NDVI drone scan ───────────────────────────
        # Simulate a 3x3 multispectral image (healthy vegetation: high NIR, low Red)
        nir_band = [[0.45, 0.48, 0.50], [0.42, 0.47, 0.44], [0.46, 0.49, 0.43]]
        red_band = [[0.08, 0.09, 0.07], [0.10, 0.08, 0.09], [0.07, 0.10, 0.08]]

        ndvi_resp = client.post(
            f"{base}/ndvi",
            json={"nir_band": nir_band, "red_band": red_band},
        )
        assert ndvi_resp.status_code == 201, f"NDVI creation failed: {ndvi_resp.text}"
        ndvi = ndvi_resp.json()
        assert ndvi["ndvi_mean"] > 0.5, "Healthy vegetation should have NDVI > 0.5"
        assert ndvi["pixels_total"] == 9

        # ── Step 5: Submit thermal drone scan ────────────────────────
        # Simulate 3x3 thermal image (moderate temps in Celsius)
        thermal_band = [[28.5, 29.0, 27.8], [30.1, 28.3, 29.5], [27.0, 28.8, 29.2]]

        thermal_resp = client.post(
            f"{base}/thermal",
            json={"thermal_band": thermal_band},
        )
        assert thermal_resp.status_code == 201, f"Thermal creation failed: {thermal_resp.text}"
        thermal = thermal_resp.json()
        assert thermal["temp_mean"] > 0
        assert thermal["pixels_total"] == 9

        # ── Step 6: Submit microbiome indicators ─────────────────────
        microbiome_resp = client.post(
            f"{base}/microbiome",
            json={
                "respiration_rate": 55.0,
                "microbial_biomass_carbon": 320.0,
                "fungi_bacteria_ratio": 1.2,
                "sampled_at": "2026-03-01T11:00:00",
            },
        )
        assert microbiome_resp.status_code == 201, f"Microbiome creation failed: {microbiome_resp.text}"
        microbiome = microbiome_resp.json()
        assert microbiome["classification"] == "healthy"

        # ── Step 7: Compute health score (Cerebro intelligence) ──────
        health_resp = client.post(f"{base}/health")
        assert health_resp.status_code == 201, f"Health score failed: {health_resp.text}"
        health = health_resp.json()
        health_score_id = health["id"]
        assert 0 <= health["score"] <= 100
        assert health["score"] > 50, "Healthy field data should produce score > 50"
        assert len(health["sources"]) > 0, "Health score should cite its data sources"

        # ── Step 8: Get treatment recommendations ────────────────────
        treatments_resp = client.post(f"{base}/treatments")
        assert treatments_resp.status_code == 201, f"Treatments failed: {treatments_resp.text}"
        treatments = treatments_resp.json()
        assert isinstance(treatments, list)
        assert len(treatments) > 0, "Should generate at least one recommendation"

        first_treatment = treatments[0]
        treatment_id = first_treatment["id"]
        assert first_treatment["organic"] is True, "All recommendations must be organic"
        assert first_treatment["problema"], "Treatment must describe the problem"
        assert first_treatment["tratamiento"], "Treatment must describe the solution"

        # ── Step 9: Apply the treatment ──────────────────────────────
        applied_resp = client.post(
            f"{base}/treatments/{treatment_id}/applied",
            json={
                "applied_at": "2026-03-15T08:00:00",
                "notes": "Aplicado composta en parcela norte",
            },
        )
        assert applied_resp.status_code == 200, f"Treatment applied failed: {applied_resp.text}"
        applied = applied_resp.json()
        assert applied["applied_at"] is not None

        # ── Step 10: Check treatment effectiveness ───────────────────
        effectiveness_resp = client.get(
            f"{base}/treatments/{treatment_id}/effectiveness"
        )
        assert effectiveness_resp.status_code == 200, f"Effectiveness failed: {effectiveness_resp.text}"
        effectiveness = effectiveness_resp.json()
        assert effectiveness["treatment_id"] == treatment_id
        assert effectiveness["applied_at"] is not None
        # Health score scored_at is "now" but applied_at is in the past,
        # so score_before may be None → insufficient_data is expected
        assert effectiveness["status"] in (
            "effective", "ineffective", "neutral", "insufficient_data"
        ), f"Unexpected status: {effectiveness['status']}"

    def test_full_pipeline_with_post_treatment_health(self, client, db, admin_headers):
        """Extended journey: re-score health after treatment to measure effectiveness."""

        # ── Setup: farm + field ──────────────────────────────────────
        farm = client.post(
            "/api/farms",
            json={"name": "Finca Regenerativa E2E", "total_hectares": 8.0},
            headers=admin_headers,
        ).json()
        farm_id = farm["id"]

        field = client.post(
            f"/api/farms/{farm_id}/fields",
            json={"name": "Parcela Frijol", "crop_type": "Frijol", "hectares": 3.0},
            headers=admin_headers,
        ).json()
        field_id = field["id"]
        base = f"/api/farms/{farm_id}/fields/{field_id}"

        # ── Collect data + score (pre-treatment) ─────────────────────
        client.post(f"{base}/soil", json={
            "sampled_at": "2026-02-01T10:00:00", "ph": 5.8,
            "organic_matter_pct": 2.1, "nitrogen_ppm": 30.0,
            "phosphorus_ppm": 15.0, "potassium_ppm": 120.0,
        })
        client.post(f"{base}/ndvi", json={
            "nir_band": [[0.35, 0.38], [0.33, 0.36]],
            "red_band": [[0.12, 0.11], [0.13, 0.14]],
        })
        client.post(f"{base}/thermal", json={
            "thermal_band": [[32.0, 33.5], [31.0, 34.0]],
        })
        client.post(f"{base}/microbiome", json={
            "respiration_rate": 25.0, "microbial_biomass_carbon": 180.0,
            "fungi_bacteria_ratio": 0.8, "sampled_at": "2026-02-01T11:00:00",
        })

        pre_health = client.post(f"{base}/health").json()
        pre_score = pre_health["score"]

        # Pin pre-treatment health score to a known time (before application)
        pre_hs = db.query(HealthScore).get(pre_health["id"])
        pre_hs.scored_at = datetime(2026, 2, 10, 12, 0, 0)
        db.commit()

        # ── Generate + apply treatment ───────────────────────────────
        treatments = client.post(f"{base}/treatments").json()
        assert len(treatments) > 0
        tid = treatments[0]["id"]

        # applied_at must be AFTER pre-treatment scored_at and BEFORE post-treatment scored_at
        client.post(f"{base}/treatments/{tid}/applied", json={
            "applied_at": "2026-02-15T08:00:00",
            "notes": "Tratamiento organico aplicado",
        })

        # ── Post-treatment: improved data + re-score ─────────────────
        client.post(f"{base}/soil", json={
            "sampled_at": "2026-03-15T10:00:00", "ph": 6.3,
            "organic_matter_pct": 3.5, "nitrogen_ppm": 50.0,
            "phosphorus_ppm": 25.0, "potassium_ppm": 200.0,
        })
        client.post(f"{base}/ndvi", json={
            "nir_band": [[0.50, 0.52], [0.48, 0.51]],
            "red_band": [[0.07, 0.06], [0.08, 0.07]],
        })
        client.post(f"{base}/thermal", json={
            "thermal_band": [[27.0, 26.5], [28.0, 27.5]],
        })
        client.post(f"{base}/microbiome", json={
            "respiration_rate": 60.0, "microbial_biomass_carbon": 400.0,
            "fungi_bacteria_ratio": 1.5, "sampled_at": "2026-03-15T11:00:00",
        })

        post_health = client.post(f"{base}/health").json()
        post_score = post_health["score"]

        # Pin post-treatment health score to a known time (after application)
        post_hs = db.query(HealthScore).get(post_health["id"])
        post_hs.scored_at = datetime(2026, 3, 20, 12, 0, 0)
        db.commit()

        # Post-treatment score should be at least as good (improved data)
        assert post_score >= pre_score, (
            f"Post-treatment score ({post_score}) should be >= pre-treatment ({pre_score})"
        )

        # ── Check effectiveness with both scores available ───────────
        eff = client.get(f"{base}/treatments/{tid}/effectiveness").json()
        assert eff["treatment_id"] == tid
        assert eff["score_before"] is not None
        assert eff["score_after"] is not None
        assert eff["status"] in ("effective", "ineffective", "neutral")
        # With improved data, delta should be positive → effective
        if eff["delta"] is not None and eff["delta"] > 5:
            assert eff["status"] == "effective"
