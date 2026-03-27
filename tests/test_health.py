"""Tests for health check endpoint + health scoring engine."""

from datetime import datetime

from cultivos.services.crop.health import (
    NDVIInput,
    SoilInput,
    ThermalInput,
    _score_ndvi,
    _score_soil,
    compute_health_score,
)


# ── Health check smoke test ─────────────────────────────────────────────


def test_health_endpoint(client):
    """Health check returns 200."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# ── Pure service tests ──────────────────────────────────────────────────


class TestScoreNDVI:
    def test_excellent_ndvi(self):
        score = _score_ndvi(NDVIInput(ndvi_mean=0.85, ndvi_std=0.03, stress_pct=2.0))
        assert score > 85

    def test_poor_ndvi(self):
        score = _score_ndvi(NDVIInput(ndvi_mean=0.2, ndvi_std=0.15, stress_pct=60.0))
        assert score < 30

    def test_moderate_ndvi(self):
        score = _score_ndvi(NDVIInput(ndvi_mean=0.5, ndvi_std=0.08, stress_pct=15.0))
        assert 30 < score < 70

    def test_zero_ndvi(self):
        score = _score_ndvi(NDVIInput(ndvi_mean=0.0, ndvi_std=0.0, stress_pct=100.0))
        assert score == 0.0


class TestScoreSoil:
    def test_optimal_soil(self):
        score = _score_soil(SoilInput(
            ph=6.5, organic_matter_pct=6.0, nitrogen_ppm=40,
            phosphorus_ppm=25, potassium_ppm=180, moisture_pct=35,
        ))
        assert score == 100.0

    def test_poor_soil(self):
        score = _score_soil(SoilInput(
            ph=4.0, organic_matter_pct=0.5, nitrogen_ppm=5,
            phosphorus_ppm=3, potassium_ppm=20, moisture_pct=5,
        ))
        assert score < 40

    def test_partial_soil_data(self):
        score = _score_soil(SoilInput(ph=6.5))
        assert score == 100.0

    def test_no_soil_data(self):
        score = _score_soil(SoilInput())
        assert score == 50.0


class TestComputeHealthScore:
    def test_golden_healthy_field(self):
        """Golden guard: healthy NDVI + good soil -> score > 80."""
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.8, ndvi_std=0.04, stress_pct=3.0),
            soil=SoilInput(ph=6.5, organic_matter_pct=5.5, nitrogen_ppm=35),
        )
        assert result["score"] > 80
        assert "ndvi" in result["sources"]
        assert "soil" in result["sources"]

    def test_golden_stressed_field(self):
        """Golden guard: stressed NDVI + poor soil -> score < 40."""
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.15, ndvi_std=0.15, stress_pct=70.0),
            soil=SoilInput(ph=4.0, organic_matter_pct=0.3, nitrogen_ppm=3),
        )
        assert result["score"] < 40

    def test_ndvi_only(self):
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.7, ndvi_std=0.05, stress_pct=5.0),
        )
        assert result["score"] > 0
        assert result["sources"] == ["ndvi"]

    def test_soil_only(self):
        result = compute_health_score(
            soil=SoilInput(ph=6.5, organic_matter_pct=5.0, moisture_pct=30),
        )
        assert result["score"] > 0
        assert result["sources"] == ["soil"]

    def test_no_inputs(self):
        result = compute_health_score()
        assert result["score"] == 0
        assert result["sources"] == []

    def test_trend_improving(self):
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.8, ndvi_std=0.04, stress_pct=3.0),
            previous_score=50.0,
        )
        assert result["trend"] == "improving"

    def test_trend_declining(self):
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.3, ndvi_std=0.1, stress_pct=40.0),
            previous_score=80.0,
        )
        assert result["trend"] == "declining"

    def test_trend_stable_no_history(self):
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.6, ndvi_std=0.06, stress_pct=10.0),
        )
        assert result["trend"] == "stable"

    def test_score_clamped_0_100(self):
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=1.0, ndvi_std=0.0, stress_pct=0.0),
            soil=SoilInput(ph=6.5, organic_matter_pct=8.0, nitrogen_ppm=40,
                           phosphorus_ppm=25, potassium_ppm=180, moisture_pct=35),
        )
        assert 0 <= result["score"] <= 100

    def test_breakdown_present(self):
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.7, ndvi_std=0.05, stress_pct=5.0),
            soil=SoilInput(ph=6.5),
        )
        assert "ndvi" in result["breakdown"]
        assert "soil" in result["breakdown"]
        assert "trend" in result["breakdown"]

    # ── Thermal integration tests ──────────────────────────────────────

    def test_health_with_thermal(self):
        """Health score with high thermal stress (>50%) produces lower score than without."""
        base = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.7, ndvi_std=0.05, stress_pct=5.0),
            soil=SoilInput(ph=6.5, organic_matter_pct=5.0),
        )
        with_thermal = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.7, ndvi_std=0.05, stress_pct=5.0),
            soil=SoilInput(ph=6.5, organic_matter_pct=5.0),
            thermal=ThermalInput(stress_pct=60.0, temp_mean=38.0, irrigation_deficit=True),
        )
        assert with_thermal["score"] < base["score"]
        assert "thermal" in with_thermal["sources"]

    def test_health_thermal_weight(self):
        """Thermal contributes ~15% of total score (check breakdown exists and is reasonable)."""
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.7, ndvi_std=0.05, stress_pct=5.0),
            soil=SoilInput(ph=6.5, organic_matter_pct=5.0),
            thermal=ThermalInput(stress_pct=10.0, temp_mean=28.0, irrigation_deficit=False),
        )
        assert "thermal" in result["breakdown"]
        # Thermal sub-score should exist and be 0-100
        assert 0 <= result["breakdown"]["thermal"] <= 100

    def test_health_without_thermal(self):
        """Health score still computes when no thermal data exists (graceful degradation)."""
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.7, ndvi_std=0.05, stress_pct=5.0),
            soil=SoilInput(ph=6.5),
        )
        assert result["score"] > 0
        assert "thermal" not in result["sources"]

    def test_health_all_sources(self):
        """Score with NDVI + soil + microbiome + thermal uses all four inputs."""
        from cultivos.services.crop.health import MicrobiomeInput
        result = compute_health_score(
            ndvi=NDVIInput(ndvi_mean=0.8, ndvi_std=0.04, stress_pct=3.0),
            soil=SoilInput(ph=6.5, organic_matter_pct=5.0, nitrogen_ppm=35),
            microbiome=MicrobiomeInput(
                respiration_rate=60.0, microbial_biomass_carbon=350.0,
                fungi_bacteria_ratio=1.2, classification="healthy",
            ),
            thermal=ThermalInput(stress_pct=5.0, temp_mean=27.0, irrigation_deficit=False),
        )
        assert set(result["sources"]) == {"ndvi", "soil", "microbiome", "thermal"}
        assert result["score"] > 70


# ── API integration tests ───────────────────────────────────────────────


class TestHealthAPI:
    def _seed_farm_field(self, db):
        from cultivos.db.models import Farm, Field
        farm = Farm(name="Test Farm", owner_name="Test Owner")
        db.add(farm)
        db.commit()
        db.refresh(farm)
        field = Field(farm_id=farm.id, name="Test Field", crop_type="maiz", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)
        return farm.id, field.id

    def _seed_ndvi(self, db, field_id, ndvi_mean=0.75, ndvi_std=0.05, stress_pct=5.0):
        from cultivos.db.models import NDVIResult
        r = NDVIResult(
            field_id=field_id,
            ndvi_mean=ndvi_mean, ndvi_std=ndvi_std,
            ndvi_min=0.3, ndvi_max=0.9,
            pixels_total=1000, stress_pct=stress_pct,
            zones=[],
        )
        db.add(r)
        db.commit()
        return r

    def _seed_soil(self, db, field_id, ph=6.5, om=5.0):
        from cultivos.db.models import SoilAnalysis
        s = SoilAnalysis(
            field_id=field_id,
            ph=ph, organic_matter_pct=om,
            nitrogen_ppm=35, phosphorus_ppm=25, potassium_ppm=180,
            moisture_pct=30, sampled_at=datetime.utcnow(),
        )
        db.add(s)
        db.commit()
        return s

    def test_compute_health_ndvi_and_soil(self, client, db):
        fid, flid = self._seed_farm_field(db)
        self._seed_ndvi(db, flid)
        self._seed_soil(db, flid)
        resp = client.post(f"/api/farms/{fid}/fields/{flid}/health")
        assert resp.status_code == 201
        data = resp.json()
        assert data["score"] > 70
        assert "ndvi" in data["sources"]
        assert "soil" in data["sources"]
        assert data["trend"] == "stable"

    def test_compute_health_ndvi_only(self, client, db):
        fid, flid = self._seed_farm_field(db)
        self._seed_ndvi(db, flid)
        resp = client.post(f"/api/farms/{fid}/fields/{flid}/health")
        assert resp.status_code == 201
        assert resp.json()["sources"] == ["ndvi"]

    def test_compute_health_soil_only(self, client, db):
        fid, flid = self._seed_farm_field(db)
        self._seed_soil(db, flid)
        resp = client.post(f"/api/farms/{fid}/fields/{flid}/health")
        assert resp.status_code == 201
        assert resp.json()["sources"] == ["soil"]

    def test_compute_health_no_data_422(self, client, db):
        fid, flid = self._seed_farm_field(db)
        resp = client.post(f"/api/farms/{fid}/fields/{flid}/health")
        assert resp.status_code == 422

    def test_compute_health_nonexistent_farm_404(self, client, db):
        resp = client.post("/api/farms/999/fields/1/health")
        assert resp.status_code == 404

    def test_compute_health_nonexistent_field_404(self, client, db):
        fid, _ = self._seed_farm_field(db)
        resp = client.post(f"/api/farms/{fid}/fields/999/health")
        assert resp.status_code == 404

    def test_list_health_scores(self, client, db):
        fid, flid = self._seed_farm_field(db)
        self._seed_ndvi(db, flid)
        client.post(f"/api/farms/{fid}/fields/{flid}/health")
        client.post(f"/api/farms/{fid}/fields/{flid}/health")
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/health")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_health_score_by_id(self, client, db):
        fid, flid = self._seed_farm_field(db)
        self._seed_ndvi(db, flid)
        create_resp = client.post(f"/api/farms/{fid}/fields/{flid}/health")
        score_id = create_resp.json()["id"]
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/health/{score_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == score_id

    def test_get_health_score_not_found(self, client, db):
        fid, flid = self._seed_farm_field(db)
        resp = client.get(f"/api/farms/{fid}/fields/{flid}/health/999")
        assert resp.status_code == 404

    def test_trend_detection_across_scores(self, client, db):
        """Second score with worse NDVI -> declining trend."""
        fid, flid = self._seed_farm_field(db)
        self._seed_ndvi(db, flid, ndvi_mean=0.8, stress_pct=3.0)
        self._seed_soil(db, flid)
        client.post(f"/api/farms/{fid}/fields/{flid}/health")

        from cultivos.db.models import NDVIResult, SoilAnalysis
        db.query(NDVIResult).filter(NDVIResult.field_id == flid).delete()
        self._seed_ndvi(db, flid, ndvi_mean=0.2, ndvi_std=0.15, stress_pct=65.0)
        db.query(SoilAnalysis).filter(SoilAnalysis.field_id == flid).delete()
        self._seed_soil(db, flid, ph=4.0, om=0.5)

        resp = client.post(f"/api/farms/{fid}/fields/{flid}/health")
        assert resp.status_code == 201
        assert resp.json()["trend"] == "declining"
