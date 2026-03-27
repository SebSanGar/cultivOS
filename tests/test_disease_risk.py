"""Tests for disease/pest risk identification from NDVI anomalies — TDD first."""


# -- Pure service tests --------------------------------------------------------


class TestIdentifyDiseaseRisk:
    def test_low_ndvi_high_thermal_flags_disease(self):
        """Low NDVI cluster + high thermal stress → disease risk flag."""
        from cultivos.services.crop.disease import assess_disease_risk

        result = assess_disease_risk(
            ndvi_mean=0.3,
            stress_pct=65.0,  # 65% of NDVI pixels below 0.4
            thermal_stress_pct=60.0,  # 60% of thermal pixels above 35C
            thermal_temp_mean=37.0,
        )

        assert result["risk_level"] != "sin_riesgo"
        assert result["risk_level"] in ("alto", "medio")
        assert any("enfermedad" in r["tipo"].lower() or "disease" in r["tipo"].lower()
                    for r in result["risks"])

    def test_low_ndvi_no_thermal_flags_nutrient(self):
        """Low NDVI with no thermal stress → nutrient deficiency, not disease."""
        from cultivos.services.crop.disease import assess_disease_risk

        result = assess_disease_risk(
            ndvi_mean=0.35,
            stress_pct=60.0,
            thermal_stress_pct=5.0,  # minimal thermal stress
            thermal_temp_mean=25.0,
        )

        assert result["risk_level"] != "sin_riesgo"
        # Should flag nutrient deficiency rather than disease
        assert any("nutriente" in r["tipo"].lower() or "deficiencia" in r["tipo"].lower()
                    for r in result["risks"])


class TestPestPatterns:
    def test_patchy_ndvi_suggests_pest(self):
        """High NDVI std (patchy loss) → pest risk vs uniform decline (nutrient)."""
        from cultivos.services.crop.disease import assess_disease_risk

        result = assess_disease_risk(
            ndvi_mean=0.45,
            stress_pct=40.0,
            ndvi_std=0.25,  # high variability = patchy
            thermal_stress_pct=10.0,
            thermal_temp_mean=28.0,
        )

        assert any("plaga" in r["tipo"].lower() for r in result["risks"])

    def test_uniform_ndvi_decline_suggests_nutrient(self):
        """Low NDVI std (uniform decline) → nutrient deficiency, not pest."""
        from cultivos.services.crop.disease import assess_disease_risk

        result = assess_disease_risk(
            ndvi_mean=0.35,
            stress_pct=55.0,
            ndvi_std=0.05,  # low variability = uniform
            thermal_stress_pct=10.0,
            thermal_temp_mean=28.0,
        )

        # Uniform decline should NOT suggest pest
        assert not any("plaga" in r["tipo"].lower() for r in result["risks"])


class TestRiskRecommendations:
    def test_disease_risk_returns_organic_treatment(self):
        """Disease risk returns organic treatment suggestions in Spanish."""
        from cultivos.services.crop.disease import assess_disease_risk

        result = assess_disease_risk(
            ndvi_mean=0.3,
            stress_pct=65.0,
            thermal_stress_pct=55.0,
            thermal_temp_mean=36.0,
        )

        for risk in result["risks"]:
            assert "recomendacion" in risk
            assert len(risk["recomendacion"]) > 10  # meaningful text
            assert risk["organico"] is True


class TestNoRisk:
    def test_healthy_ndvi_no_risk(self):
        """Healthy NDVI values → 'sin riesgo detectado'."""
        from cultivos.services.crop.disease import assess_disease_risk

        result = assess_disease_risk(
            ndvi_mean=0.75,
            stress_pct=5.0,
            thermal_stress_pct=3.0,
            thermal_temp_mean=26.0,
        )

        assert result["risk_level"] == "sin_riesgo"
        assert result["mensaje"] == "Sin riesgo detectado"
        assert len(result["risks"]) == 0


# -- API integration tests ----------------------------------------------------


class TestDiseaseRiskAPI:
    def _seed_farm_field_with_ndvi_thermal(self, db):
        from cultivos.db.models import Farm, Field, NDVIResult, ThermalResult

        farm = Farm(
            name="Rancho Prueba",
            owner_name="Test",
            state="Jalisco",
            location_lat=20.6,
            location_lon=-103.3,
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field = Field(
            farm_id=farm.id, name="Parcela Enferma", crop_type="maiz", hectares=10
        )
        db.add(field)
        db.commit()
        db.refresh(field)

        # Add stressed NDVI result
        ndvi = NDVIResult(
            field_id=field.id,
            ndvi_mean=0.3,
            ndvi_std=0.2,
            ndvi_min=0.05,
            ndvi_max=0.7,
            pixels_total=10000,
            stress_pct=65.0,
            zones=[],
        )
        db.add(ndvi)

        # Add stressed thermal result
        thermal = ThermalResult(
            field_id=field.id,
            temp_mean=37.0,
            temp_std=3.0,
            temp_min=30.0,
            temp_max=42.0,
            pixels_total=10000,
            stress_pct=55.0,
            irrigation_deficit=True,
        )
        db.add(thermal)
        db.commit()

        return farm.id, field.id

    def test_disease_risk_endpoint(self, client, db):
        """GET /api/farms/{id}/fields/{id}/disease-risk returns risk assessment."""
        fid, flid = self._seed_farm_field_with_ndvi_thermal(db)

        resp = client.get(f"/api/farms/{fid}/fields/{flid}/disease-risk")
        assert resp.status_code == 200

        data = resp.json()
        assert "risk_level" in data
        assert "risks" in data
        assert data["field_id"] == flid
        assert data["risk_level"] != "sin_riesgo"  # stressed data should flag risk

    def test_disease_risk_no_data(self, client, db):
        """Field with no NDVI/thermal data returns sin_riesgo with note."""
        from cultivos.db.models import Farm, Field

        farm = Farm(name="Rancho Vacio", state="Jalisco")
        db.add(farm)
        db.commit()
        db.refresh(farm)

        field = Field(farm_id=farm.id, name="Sin Datos", crop_type="frijol", hectares=5)
        db.add(field)
        db.commit()
        db.refresh(field)

        resp = client.get(f"/api/farms/{farm.id}/fields/{field.id}/disease-risk")
        assert resp.status_code == 200

        data = resp.json()
        assert data["risk_level"] == "sin_riesgo"
        assert "nota" in data
