/* Comprehensive field intelligence page — /inteligencia */
(function () {
    "use strict";

    var farmSel = document.getElementById("intel-farm-select");
    var fieldSel = document.getElementById("intel-field-select");
    var emptyEl = document.getElementById("intel-page-empty");
    var contentEl = document.getElementById("intel-page-content");

    /* Stats */
    var statHealth = document.getElementById("intel-stat-health");
    var statNdvi = document.getElementById("intel-stat-ndvi");
    var statRisk = document.getElementById("intel-stat-risk");
    var statTreatments = document.getElementById("intel-stat-treatments");
    var statFusion = document.getElementById("intel-stat-fusion");

    /* Section bodies */
    var healthBody = document.getElementById("intel-health-body");
    var ndviBody = document.getElementById("intel-ndvi-body");
    var thermalBody = document.getElementById("intel-thermal-body");
    var soilBody = document.getElementById("intel-soil-body");
    var microbiomeBody = document.getElementById("intel-microbiome-body");
    var weatherBody = document.getElementById("intel-weather-body");
    var growthBody = document.getElementById("intel-growth-body");
    var diseaseBody = document.getElementById("intel-disease-body");
    var yieldBody = document.getElementById("intel-yield-body");
    var treatmentsBody = document.getElementById("intel-treatments-body");
    var carbonBody = document.getElementById("intel-carbon-body");
    var fusionBody = document.getElementById("intel-fusion-body");
    var fieldInfoEl = document.getElementById("intel-field-info");

    function fetchJSON(url) {
        return fetch(url).then(function (r) {
            if (!r.ok) return null;
            return r.json();
        }).catch(function () { return null; });
    }

    function esc(s) {
        var d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    function resetStats() {
        statHealth.textContent = "--";
        statNdvi.textContent = "--";
        statRisk.textContent = "--";
        statTreatments.textContent = "--";
        statFusion.textContent = "--";
    }

    function resetSections() {
        healthBody.innerHTML = '<span style="color:#888;">Sin datos de salud</span>';
        ndviBody.innerHTML = '<span style="color:#888;">Sin datos NDVI</span>';
        thermalBody.innerHTML = '<span style="color:#888;">Sin datos termicos</span>';
        soilBody.innerHTML = '<span style="color:#888;">Sin datos de suelo</span>';
        microbiomeBody.innerHTML = '<span style="color:#888;">Sin datos de microbioma</span>';
        weatherBody.innerHTML = '<span style="color:#888;">Sin datos de clima</span>';
        growthBody.innerHTML = '<span style="color:#888;">Sin datos de crecimiento</span>';
        diseaseBody.innerHTML = '<span style="color:#888;">Sin datos de enfermedades</span>';
        yieldBody.innerHTML = '<span style="color:#888;">Sin prediccion de rendimiento</span>';
        treatmentsBody.innerHTML = '<span style="color:#888;">Sin tratamientos registrados</span>';
        carbonBody.innerHTML = '<span style="color:#888;">Sin datos de carbono</span>';
        fusionBody.innerHTML = '<span style="color:#888;">Sin datos de fusion</span>';
        fieldInfoEl.innerHTML = "";
    }

    var trendLabels = {
        improving: "Mejorando",
        stable: "Estable",
        declining: "Declinando"
    };

    var trendColors = {
        improving: "#22c55e",
        stable: "#eab308",
        declining: "#ef4444"
    };

    var riskColors = {
        alto: "#ef4444",
        medio: "#eab308",
        bajo: "#22c55e",
        sin_riesgo: "#22c55e"
    };

    var riskLabels = {
        alto: "Alto",
        medio: "Medio",
        bajo: "Bajo",
        sin_riesgo: "Sin Riesgo"
    };

    function dataRow(label, value, unit) {
        return '<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid #222;">' +
            '<span style="color:#aaa;">' + esc(label) + '</span>' +
            '<span style="color:#fff;font-weight:600;">' + esc(String(value)) + (unit ? ' <span style="color:#888;">' + esc(unit) + '</span>' : '') + '</span>' +
            '</div>';
    }

    function badge(text, color) {
        return '<span style="display:inline-block;padding:0.15rem 0.6rem;border-radius:4px;font-size:0.75rem;font-weight:600;background:' + color + '22;color:' + color + ';">' + esc(text) + '</span>';
    }

    /* --- Render functions for each section --- */

    function renderHealth(h) {
        if (!h) return;
        var tl = trendLabels[h.trend] || h.trend;
        var tc = trendColors[h.trend] || "#888";
        var html = dataRow("Puntaje", h.score.toFixed(1), "/ 100");
        html += '<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid #222;">' +
            '<span style="color:#aaa;">Tendencia</span>' +
            badge(tl, tc) + '</div>';
        html += dataRow("Fuentes", h.sources.join(", "), "");
        if (h.breakdown) {
            var keys = Object.keys(h.breakdown);
            for (var i = 0; i < keys.length; i++) {
                html += dataRow(keys[i].toUpperCase(), h.breakdown[keys[i]].toFixed(1), "pts");
            }
        }
        healthBody.innerHTML = html;
        statHealth.textContent = h.score.toFixed(1);
    }

    function renderNdvi(n) {
        if (!n) return;
        var html = dataRow("Media", n.ndvi_mean.toFixed(3), "");
        html += dataRow("Desviacion", n.ndvi_std.toFixed(3), "");
        html += dataRow("Min / Max", n.ndvi_min.toFixed(2) + " / " + n.ndvi_max.toFixed(2), "");
        html += dataRow("Estres", n.stress_pct.toFixed(1), "%");
        ndviBody.innerHTML = html;
        statNdvi.textContent = n.ndvi_mean.toFixed(2);
    }

    function renderThermal(t) {
        if (!t) return;
        var html = dataRow("Temp. Media", t.temp_mean.toFixed(1), "C");
        html += dataRow("Rango", t.temp_min.toFixed(1) + " - " + t.temp_max.toFixed(1), "C");
        html += dataRow("Estres", t.stress_pct.toFixed(1), "%");
        html += '<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid #222;">' +
            '<span style="color:#aaa;">Deficit de Riego</span>' +
            badge(t.irrigation_deficit ? "Si" : "No", t.irrigation_deficit ? "#ef4444" : "#22c55e") + '</div>';
        thermalBody.innerHTML = html;
    }

    function renderSoil(s) {
        if (!s) return;
        var html = "";
        if (s.ph != null) html += dataRow("pH", s.ph.toFixed(1), "");
        if (s.organic_matter_pct != null) html += dataRow("Materia Organica", s.organic_matter_pct.toFixed(1), "%");
        if (s.nitrogen_ppm != null) html += dataRow("Nitrogeno", s.nitrogen_ppm.toFixed(0), "ppm");
        if (s.phosphorus_ppm != null) html += dataRow("Fosforo", s.phosphorus_ppm.toFixed(0), "ppm");
        if (s.potassium_ppm != null) html += dataRow("Potasio", s.potassium_ppm.toFixed(0), "ppm");
        if (s.moisture_pct != null) html += dataRow("Humedad", s.moisture_pct.toFixed(1), "%");
        if (s.texture) html += dataRow("Textura", s.texture, "");
        soilBody.innerHTML = html;
    }

    function renderMicrobiome(m) {
        if (!m) return;
        var classColors = { healthy: "#22c55e", moderate: "#eab308", degraded: "#ef4444" };
        var classLabels = { healthy: "Saludable", moderate: "Moderado", degraded: "Degradado" };
        var html = '<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid #222;">' +
            '<span style="color:#aaa;">Clasificacion</span>' +
            badge(classLabels[m.classification] || m.classification, classColors[m.classification] || "#888") + '</div>';
        html += dataRow("Respiracion", m.respiration_rate.toFixed(1), "mg CO2/kg/dia");
        html += dataRow("Biomasa C", m.microbial_biomass_carbon.toFixed(0), "mg C/kg");
        html += dataRow("Relacion Hongos/Bacterias", m.fungi_bacteria_ratio.toFixed(2), "");
        microbiomeBody.innerHTML = html;
    }

    function renderWeather(w) {
        if (!w) return;
        var html = dataRow("Temperatura", w.temp_c.toFixed(1), "C");
        html += dataRow("Humedad", w.humidity_pct.toFixed(0), "%");
        html += dataRow("Viento", w.wind_kmh.toFixed(0), "km/h");
        html += dataRow("Lluvia", w.rainfall_mm.toFixed(1), "mm");
        html += dataRow("Condicion", w.description, "");
        weatherBody.innerHTML = html;
    }

    function renderGrowth(g) {
        if (!g) return;
        var html = dataRow("Etapa", g.stage_es, "");
        html += dataRow("Dias desde siembra", g.days_since_planting, "dias");
        html += dataRow("Dias en etapa", g.days_in_stage, "dias");
        if (g.days_until_next_stage != null) {
            html += dataRow("Dias para siguiente etapa", g.days_until_next_stage, "dias");
        }
        html += dataRow("Multiplicador de Agua", g.water_multiplier.toFixed(2), "x");
        html += dataRow("Enfoque Nutricional", g.nutrient_focus, "");
        growthBody.innerHTML = html;
    }

    function renderDisease(d) {
        if (!d) return;
        var rl = riskLabels[d.risk_level] || d.risk_level;
        var rc = riskColors[d.risk_level] || "#888";
        var html = '<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid #222;">' +
            '<span style="color:#aaa;">Nivel de Riesgo</span>' +
            badge(rl, rc) + '</div>';
        html += dataRow("Mensaje", d.mensaje, "");
        if (d.risks && d.risks.length > 0) {
            html += '<div style="margin-top:0.5rem;color:#aaa;font-size:0.8rem;">Riesgos detectados: ' + d.risks.length + '</div>';
        }
        diseaseBody.innerHTML = html;
        statRisk.textContent = rl;
        statRisk.style.color = rc;
    }

    function renderYield(y) {
        if (!y) return;
        var html = dataRow("Rendimiento Estimado", y.kg_per_ha.toFixed(0), "kg/ha");
        html += dataRow("Rango", y.min_kg_per_ha.toFixed(0) + " - " + y.max_kg_per_ha.toFixed(0), "kg/ha");
        html += dataRow("Total Estimado", y.total_kg.toFixed(0), "kg");
        html += dataRow("Nota", y.nota, "");
        yieldBody.innerHTML = html;
    }

    function renderTreatments(ts) {
        if (!ts || ts.length === 0) return;
        var urgColors = { alta: "#ef4444", media: "#eab308", baja: "#22c55e" };
        var urgLabels = { alta: "Alta", media: "Media", baja: "Baja" };
        var html = "";
        for (var i = 0; i < ts.length; i++) {
            var t = ts[i];
            html += '<div style="padding:0.5rem 0;border-bottom:1px solid #222;">' +
                '<div style="display:flex;justify-content:space-between;align-items:center;">' +
                '<span style="color:#fff;font-weight:600;">' + esc(t.problema) + '</span>' +
                badge(urgLabels[t.urgencia] || t.urgencia, urgColors[t.urgencia] || "#888") +
                '</div>' +
                '<div style="color:#aaa;font-size:0.8rem;margin-top:0.2rem;">' + esc(t.tratamiento) + '</div>' +
                '<div style="color:#666;font-size:0.75rem;">' + (t.organic ? "Organico" : "Convencional") + ' — $' + t.costo_estimado_mxn + ' MXN</div>' +
                '</div>';
        }
        treatmentsBody.innerHTML = html;
        statTreatments.textContent = ts.length;
    }

    function renderCarbon(c) {
        if (!c) return;
        var html = "";
        if (c.soc_pct != null) html += dataRow("SOC", c.soc_pct.toFixed(2), "%");
        if (c.soc_tonnes_per_ha != null) html += dataRow("SOC", c.soc_tonnes_per_ha.toFixed(1), "t/ha");
        if (c.clasificacion) html += dataRow("Clasificacion", c.clasificacion, "");
        html += dataRow("Tendencia", c.tendencia, "");
        carbonBody.innerHTML = html;
    }

    function renderFusion(f) {
        if (!f) return;
        var confColor = f.confidence >= 0.7 ? "#22c55e" : f.confidence >= 0.4 ? "#eab308" : "#ef4444";
        var html = '<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid #222;">' +
            '<span style="color:#aaa;">Confianza</span>' +
            '<span style="color:' + confColor + ';font-weight:700;">' + (f.confidence * 100).toFixed(0) + '%</span></div>';
        html += dataRow("Sensores", f.sensors_used.join(", "), "");
        html += dataRow("Evaluacion", f.assessment, "");
        if (f.contradictions && f.contradictions.length > 0) {
            html += '<div style="margin-top:0.5rem;color:#ef4444;font-size:0.8rem;">Contradicciones: ' + f.contradictions.length + '</div>';
        }
        fusionBody.innerHTML = html;
        statFusion.textContent = (f.confidence * 100).toFixed(0) + "%";
    }

    /* --- Load farms on init --- */
    function loadFarms() {
        fetchJSON("/api/farms").then(function (farms) {
            if (!farms) return;
            farms.forEach(function (f) {
                var opt = document.createElement("option");
                opt.value = f.id;
                opt.textContent = f.name;
                farmSel.appendChild(opt);
            });
        });
    }

    /* Load fields for selected farm */
    window.loadFieldsForIntelligence = function () {
        fieldSel.innerHTML = '<option value="">Seleccione un campo...</option>';
        contentEl.style.display = "none";
        emptyEl.style.display = "";
        resetStats();
        resetSections();
        var farmId = farmSel.value;
        if (!farmId) return;
        fetchJSON("/api/farms/" + farmId + "/fields").then(function (fields) {
            if (!fields) return;
            fields.forEach(function (f) {
                var opt = document.createElement("option");
                opt.value = f.id;
                opt.textContent = f.name + (f.crop_type ? " (" + f.crop_type + ")" : "");
                fieldSel.appendChild(opt);
            });
        });
    };

    /* Load comprehensive intelligence */
    window.loadFieldIntelligence = function () {
        var farmId = farmSel.value;
        var fieldId = fieldSel.value;
        if (!farmId || !fieldId) return;

        resetStats();
        resetSections();
        emptyEl.style.display = "none";
        contentEl.style.display = "";

        fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/intelligence").then(function (data) {
            if (!data) {
                emptyEl.style.display = "";
                contentEl.style.display = "none";
                return;
            }

            /* Field header */
            var headerHtml = '<div style="display:flex;gap:1.5rem;flex-wrap:wrap;align-items:center;">' +
                '<div><span style="color:#aaa;">Campo:</span> <strong style="color:#fff;">' + esc(data.field_name) + '</strong></div>';
            if (data.crop_type) {
                headerHtml += '<div><span style="color:#aaa;">Cultivo:</span> <strong style="color:#fff;">' + esc(data.crop_type) + '</strong></div>';
            }
            if (data.hectares) {
                headerHtml += '<div><span style="color:#aaa;">Hectareas:</span> <strong style="color:#fff;">' + data.hectares.toFixed(1) + ' ha</strong></div>';
            }
            headerHtml += '</div>';
            fieldInfoEl.innerHTML = headerHtml;

            /* Render all sections */
            renderHealth(data.health);
            renderNdvi(data.ndvi);
            renderThermal(data.thermal);
            renderSoil(data.soil);
            renderMicrobiome(data.microbiome);
            renderWeather(data.weather);
            renderGrowth(data.growth_stage);
            renderDisease(data.disease_risk);
            renderYield(data.yield_prediction);
            renderTreatments(data.treatments);
            renderCarbon(data.carbon);
            renderFusion(data.fusion);
        });
    };

    loadFarms();
})();
