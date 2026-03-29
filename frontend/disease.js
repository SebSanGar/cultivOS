/* Disease risk assessment page — /enfermedades */
(function () {
    "use strict";

    var farmSel = document.getElementById("disease-farm-select");
    var fieldSel = document.getElementById("disease-field-select");
    var emptyEl = document.getElementById("disease-empty");
    var contentEl = document.getElementById("disease-risk-content");
    var cardsEl = document.getElementById("disease-risk-cards");
    var resultsEl = document.getElementById("disease-identify-results");

    function fetchJSON(url, opts) {
        return fetch(url, opts).then(function (r) {
            if (!r.ok) return null;
            return r.json();
        }).catch(function () { return null; });
    }

    function esc(s) {
        var d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    var severityColors = {
        alta: "#ef4444",
        media: "#eab308",
        baja: "#22c55e",
        alto: "#ef4444",
        medio: "#eab308",
        bajo: "#22c55e",
        sin_riesgo: "#22c55e"
    };

    var severityLabels = {
        alta: "Alta",
        media: "Media",
        baja: "Baja",
        alto: "Alto",
        medio: "Medio",
        bajo: "Bajo",
        sin_riesgo: "Sin Riesgo"
    };

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
    }

    /* Load fields for selected farm */
    window.loadFieldsForDisease = function () {
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

    /* Load disease risk */
    window.loadDiseaseRisk = function () {
        var farmId = farmSel.value;
        var fieldId = fieldSel.value;
        if (!farmId || !fieldId) {
            contentEl.style.display = "none";
            emptyEl.style.display = "";
            emptyEl.textContent = "Seleccione una granja y un campo para consultar el riesgo.";
            resetStats();
            return;
        }
        emptyEl.style.display = "none";
        contentEl.style.display = "";

        var url = "/api/farms/" + farmId + "/fields/" + fieldId + "/disease-risk";

        fetchJSON(url).then(function (data) {
            if (!data) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                emptyEl.textContent = "No se pudo obtener la evaluacion de riesgo para este campo.";
                resetStats();
                return;
            }
            renderRisk(data);
        });
    };

    function resetStats() {
        document.getElementById("disease-risk-level").textContent = "--";
        document.getElementById("disease-risk-count").textContent = "--";
        document.getElementById("disease-humidity").textContent = "--";
        document.getElementById("disease-temp").textContent = "--";
        document.getElementById("disease-rainfall").textContent = "--";
        document.getElementById("disease-mensaje").textContent = "";
        cardsEl.innerHTML = "";
    }

    function renderRisk(data) {
        /* Stats strip */
        var levelEl = document.getElementById("disease-risk-level");
        levelEl.textContent = severityLabels[data.risk_level] || data.risk_level;
        levelEl.style.color = severityColors[data.risk_level] || "#ccc";

        document.getElementById("disease-risk-count").textContent =
            data.risks ? data.risks.length : 0;

        if (data.weather_context) {
            document.getElementById("disease-humidity").textContent =
                data.weather_context.humidity_pct.toFixed(0) + "%";
            document.getElementById("disease-temp").textContent =
                data.weather_context.temp_c.toFixed(1);
            document.getElementById("disease-rainfall").textContent =
                data.weather_context.rainfall_mm.toFixed(1);
        }

        /* Message */
        document.getElementById("disease-mensaje").textContent =
            data.mensaje || "Sin evaluacion disponible.";

        /* Risk cards */
        cardsEl.innerHTML = "";
        if (data.risks && data.risks.length > 0) {
            data.risks.forEach(function (risk) {
                var color = severityColors[risk.urgencia] || "#888";
                var card = document.createElement("div");
                card.className = "intel-card";
                card.style.borderLeft = "3px solid " + color;
                card.innerHTML =
                    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">' +
                        '<span style="color:#eee;font-weight:600;font-size:0.95rem;">' + esc(risk.tipo) + '</span>' +
                        '<span class="disease-severity-badge" style="background:' + color + '22;color:' + color + ';padding:0.15rem 0.5rem;border-radius:4px;font-size:0.75rem;font-weight:600;">' +
                            esc(severityLabels[risk.urgencia] || risk.urgencia) + '</span>' +
                    '</div>' +
                    '<p style="color:#aaa;font-size:0.85rem;margin:0 0 0.5rem 0;">' + esc(risk.descripcion) + '</p>' +
                    '<div style="color:#4da6ff;font-size:0.8rem;">' + esc(risk.recomendacion) + '</div>';
                cardsEl.appendChild(card);
            });
        } else {
            cardsEl.innerHTML = '<div class="intel-card" style="color:#888;text-align:center;">Sin riesgos detectados para este campo.</div>';
        }
    }

    /* Identify disease by symptoms */
    window.identifyDisease = function (e) {
        e.preventDefault();
        var symptomsRaw = document.getElementById("disease-symptoms-input").value.trim();
        if (!symptomsRaw) return;
        var symptoms = symptomsRaw.split(",").map(function (s) { return s.trim(); }).filter(Boolean);
        var crop = document.getElementById("disease-crop-input").value.trim() || null;

        var body = { symptoms: symptoms };
        if (crop) body.crop = crop;

        resultsEl.innerHTML = '<div style="color:#888;">Buscando...</div>';

        fetchJSON("/api/knowledge/diseases/identify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        }).then(function (matches) {
            if (!matches || matches.length === 0) {
                resultsEl.innerHTML = '<div style="color:#888;">Sin coincidencias encontradas.</div>';
                return;
            }
            var html = "";
            matches.forEach(function (m) {
                var confPct = (m.confidence * 100).toFixed(0);
                var confColor = m.confidence >= 0.6 ? "#ef4444" : m.confidence >= 0.3 ? "#eab308" : "#22c55e";
                var sevColor = severityColors[m.severity] || "#888";
                html +=
                    '<div class="intel-card" style="margin-top:0.75rem;border-left:3px solid ' + confColor + ';">' +
                        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">' +
                            '<span style="color:#eee;font-weight:600;">' + esc(m.name) + '</span>' +
                            '<span class="disease-confidence-badge" style="background:' + confColor + '22;color:' + confColor + ';padding:0.15rem 0.5rem;border-radius:4px;font-size:0.75rem;font-weight:600;">' +
                                confPct + '% confianza</span>' +
                        '</div>' +
                        '<p style="color:#aaa;font-size:0.85rem;margin:0 0 0.5rem 0;">' + esc(m.description_es) + '</p>' +
                        '<div style="margin-bottom:0.3rem;">' +
                            '<span style="color:#888;font-size:0.8rem;">Severidad: </span>' +
                            '<span style="color:' + sevColor + ';font-size:0.8rem;font-weight:600;">' + esc(severityLabels[m.severity] || m.severity) + '</span>' +
                        '</div>' +
                        '<div style="margin-bottom:0.3rem;">' +
                            '<span style="color:#888;font-size:0.8rem;">Sintomas coincidentes: </span>' +
                            '<span style="color:#ccc;font-size:0.8rem;">' + m.symptoms_matched.map(esc).join(", ") + '</span>' +
                        '</div>' +
                        (m.treatments && m.treatments.length > 0 ?
                            '<div style="margin-top:0.5rem;padding-top:0.5rem;border-top:1px solid #222;">' +
                                '<span style="color:#4da6ff;font-size:0.8rem;font-weight:600;">Tratamientos:</span>' +
                                m.treatments.map(function (t) {
                                    return '<div style="color:#aaa;font-size:0.8rem;margin-top:0.25rem;">&bull; ' +
                                        esc(t.name) + ' — ' + esc(t.description_es) +
                                        (t.organic ? ' <span style="color:#22c55e;font-size:0.7rem;">(organico)</span>' : '') +
                                    '</div>';
                                }).join("") +
                            '</div>'
                        : '') +
                    '</div>';
            });
            resultsEl.innerHTML = html;
        });
    };

    loadFarms();
})();
