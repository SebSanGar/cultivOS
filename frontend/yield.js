/* Yield prediction page — /rendimiento */
(function () {
    "use strict";

    var farmSel = document.getElementById("yield-farm-select");
    var fieldSel = document.getElementById("yield-field-select");
    var emptyEl = document.getElementById("yield-empty");
    var contentEl = document.getElementById("yield-content");
    var cardEl = document.getElementById("yield-card");
    var factorsEl = document.getElementById("yield-factors");
    var confidenceEl = document.getElementById("yield-confidence");
    var notaEl = document.getElementById("yield-nota");

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

    function fmtNum(v, decimals) {
        if (v === null || v === undefined) return "--";
        return Number(v).toLocaleString("es-MX", { maximumFractionDigits: decimals !== undefined ? decimals : 0 });
    }

    /* Load farms on init */
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
        emptyEl.style.display = "";
    }

    /* Load fields for selected farm */
    window.loadFieldsForYield = function () {
        fieldSel.innerHTML = '<option value="">Seleccione un campo...</option>';
        contentEl.style.display = "none";
        emptyEl.style.display = "";
        resetStats();
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

    /* Load yield prediction for selected field */
    window.loadYieldPrediction = function () {
        var farmId = farmSel.value;
        var fieldId = fieldSel.value;
        if (!farmId || !fieldId) {
            contentEl.style.display = "none";
            emptyEl.style.display = "";
            resetStats();
            return;
        }
        emptyEl.style.display = "none";
        contentEl.style.display = "";

        var url = "/api/farms/" + farmId + "/fields/" + fieldId + "/yield";
        fetchJSON(url).then(function (data) {
            if (!data) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                emptyEl.textContent = "No se pudo cargar la prediccion de rendimiento.";
                resetStats();
                return;
            }
            renderYield(data);
        });
    };

    function resetStats() {
        document.getElementById("yield-stat-estimate").textContent = "--";
        document.getElementById("yield-stat-range").textContent = "--";
        document.getElementById("yield-stat-total").textContent = "--";
        cardEl.innerHTML = "";
        factorsEl.innerHTML = "";
        confidenceEl.innerHTML = "";
        notaEl.innerHTML = "";
    }

    function renderYield(data) {
        /* Stats strip */
        document.getElementById("yield-stat-estimate").textContent = fmtNum(data.kg_per_ha, 0) + " kg/ha";
        document.getElementById("yield-stat-range").textContent = fmtNum(data.min_kg_per_ha, 0) + " — " + fmtNum(data.max_kg_per_ha, 0);
        document.getElementById("yield-stat-total").textContent = fmtNum(data.total_kg, 0) + " kg";

        /* Yield estimate card */
        var rangeWidth = data.max_kg_per_ha - data.min_kg_per_ha;
        var pointPosition = rangeWidth > 0 ? ((data.kg_per_ha - data.min_kg_per_ha) / rangeWidth) * 100 : 50;

        cardEl.innerHTML =
            '<div class="intel-card" style="border-left:4px solid #22c55e;">' +
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">' +
                    '<span style="color:#22c55e;font-weight:700;font-size:0.85rem;text-transform:uppercase;">Estimacion de Cosecha</span>' +
                    '<span style="background:#22c55e22;color:#22c55e;padding:0.2rem 0.6rem;border-radius:4px;font-size:0.75rem;font-weight:600;">' +
                        esc(data.crop_type) +
                    '</span>' +
                '</div>' +
                '<div style="font-size:2.5rem;font-weight:800;color:#eee;margin-bottom:0.25rem;font-family:monospace;">' +
                    fmtNum(data.kg_per_ha, 0) + ' <span style="font-size:1rem;color:#999;font-weight:400;">kg/ha</span>' +
                '</div>' +
                '<div style="color:#999;font-size:0.85rem;margin-bottom:1rem;">Cultivo: ' + esc(data.crop_type) + ' | ' + fmtNum(data.hectares, 1) + ' ha</div>' +
                /* Uncertainty bar */
                '<div style="margin-bottom:0.75rem;">' +
                    '<div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">' +
                        '<span style="color:#666;font-size:0.75rem;">' + fmtNum(data.min_kg_per_ha, 0) + '</span>' +
                        '<span style="color:#999;font-size:0.75rem;font-weight:600;">Rango de Incertidumbre</span>' +
                        '<span style="color:#666;font-size:0.75rem;">' + fmtNum(data.max_kg_per_ha, 0) + '</span>' +
                    '</div>' +
                    '<div style="position:relative;height:8px;background:#333;border-radius:4px;overflow:visible;">' +
                        '<div style="position:absolute;top:0;left:0;height:100%;width:100%;background:linear-gradient(90deg,#ef4444 0%,#eab308 30%,#22c55e 50%,#eab308 70%,#ef4444 100%);border-radius:4px;opacity:0.3;"></div>' +
                        '<div style="position:absolute;top:-4px;left:' + pointPosition + '%;transform:translateX(-50%);width:16px;height:16px;background:#22c55e;border-radius:50%;border:2px solid #0a0a0a;"></div>' +
                    '</div>' +
                '</div>' +
                /* Total */
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem;padding-top:1rem;border-top:1px solid #333;">' +
                    '<div>' +
                        '<div style="color:#eee;font-weight:700;font-size:1.25rem;font-family:monospace;">' + fmtNum(data.total_kg, 0) + ' kg</div>' +
                        '<div style="color:#666;font-size:0.75rem;">Produccion total estimada</div>' +
                    '</div>' +
                    '<div>' +
                        '<div style="color:#eee;font-weight:700;font-size:1.25rem;font-family:monospace;">' + fmtNum(data.total_kg / 1000.0, 1) + ' ton</div>' +
                        '<div style="color:#666;font-size:0.75rem;">Toneladas estimadas</div>' +
                    '</div>' +
                '</div>' +
            '</div>';

        /* Contributing factors */
        renderFactors(data);

        /* Confidence level */
        renderConfidence(data);

        /* Nota */
        notaEl.innerHTML =
            '<div class="intel-card" style="border-left:4px solid #4da6ff;">' +
                '<h3 style="color:#eee;margin:0 0 0.5rem 0;font-size:0.9rem;">Nota del Analisis</h3>' +
                '<p style="color:#999;font-size:0.85rem;line-height:1.6;margin:0;">' + esc(data.nota) + '</p>' +
            '</div>';
    }

    function renderFactors(data) {
        var healthScore = estimateHealthFromYield(data);
        var factors = [
            {
                label: "Salud del Campo",
                value: healthScore !== null ? healthScore.toFixed(0) + "/100" : "Sin datos",
                color: healthScore !== null ? (healthScore >= 70 ? "#22c55e" : healthScore >= 40 ? "#eab308" : "#ef4444") : "#666",
                desc: "Puntaje de salud compuesto (NDVI, suelo, clima)"
            },
            {
                label: "NDVI Actual",
                value: "Incluido en salud",
                color: "#4da6ff",
                desc: "Indice de vegetacion normalizado del ultimo vuelo"
            },
            {
                label: "Tipo de Cultivo",
                value: data.crop_type,
                color: "#22c55e",
                desc: "Base de rendimiento regional SIAP para " + data.crop_type
            },
            {
                label: "Area del Campo",
                value: fmtNum(data.hectares, 1) + " ha",
                color: "#eab308",
                desc: "Superficie de produccion"
            }
        ];

        var html = '<h3 style="color:#eee;margin:0 0 1rem 0;font-size:1rem;">Factores Contribuyentes</h3>' +
            '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:1rem;">';

        factors.forEach(function (f) {
            html +=
                '<div class="intel-card" style="border-left:3px solid ' + f.color + ';padding:1rem;">' +
                    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">' +
                        '<span style="color:#ccc;font-size:0.8rem;font-weight:600;">' + esc(f.label) + '</span>' +
                        '<span style="color:' + f.color + ';font-weight:700;font-size:0.9rem;font-family:monospace;">' + esc(f.value) + '</span>' +
                    '</div>' +
                    '<div style="color:#666;font-size:0.75rem;">' + esc(f.desc) + '</div>' +
                '</div>';
        });

        html += '</div>';
        factorsEl.innerHTML = html;
    }

    function estimateHealthFromYield(data) {
        /* Reverse-engineer health score from yield: health = (kg_per_ha/baseline - 0.20) / 0.80 * 100 */
        var baselines = {
            "maiz": 5500, "frijol": 900, "calabaza": 12000, "chile": 8000,
            "jitomate": 25000, "aguacate": 10000, "agave": 40000, "sorgo": 4500,
            "garbanzo": 1800, "cana de azucar": 80000, "nopal": 50000
        };
        var baseline = baselines[data.crop_type] || 5000;
        var multiplier = data.kg_per_ha / baseline;
        var score = (multiplier - 0.20) / 0.80 * 100;
        return Math.max(0, Math.min(100, Math.round(score)));
    }

    function renderConfidence(data) {
        var healthScore = estimateHealthFromYield(data);
        var level, color, desc;
        if (healthScore >= 70) {
            level = "Alta";
            color = "#22c55e";
            desc = "Datos de salud solidos — prediccion confiable.";
        } else if (healthScore >= 40) {
            level = "Media";
            color = "#eab308";
            desc = "Datos parciales — prediccion con incertidumbre moderada.";
        } else {
            level = "Baja";
            color = "#ef4444";
            desc = "Pocos datos o campo estresado — prediccion con alta incertidumbre.";
        }

        var barWidth = healthScore || 50;

        confidenceEl.innerHTML =
            '<div class="intel-card">' +
                '<h3 style="color:#eee;margin:0 0 0.75rem 0;font-size:1rem;">Nivel de Confianza</h3>' +
                '<div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem;">' +
                    '<span style="background:' + color + '22;color:' + color + ';padding:0.3rem 0.8rem;border-radius:4px;font-weight:700;font-size:0.85rem;">' + esc(level) + '</span>' +
                    '<span style="color:#999;font-size:0.85rem;">' + esc(desc) + '</span>' +
                '</div>' +
                '<div style="height:6px;background:#333;border-radius:3px;overflow:hidden;">' +
                    '<div style="height:100%;width:' + barWidth + '%;background:' + color + ';border-radius:3px;transition:width 0.3s;"></div>' +
                '</div>' +
            '</div>';
    }

    loadFarms();
})();
