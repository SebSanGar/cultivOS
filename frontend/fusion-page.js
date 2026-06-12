/* Sensor fusion validation page — /fusion */
(function () {
    "use strict";

    var emptyEl = document.getElementById("fusion-empty");
    var contentEl = document.getElementById("fusion-content");
    var matrixEl = document.getElementById("fusion-matrix");
    var contradictionsEl = document.getElementById("fusion-contradictions");
    var fieldCardsEl = document.getElementById("fusion-field-cards");

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

    function t(key, fallback) { return (window.cultivOS_i18n && window.cultivOS_i18n.t) ? window.cultivOS_i18n.t(key) : fallback; }

    function getSensorLabels() {
        return {
            ndvi: "NDVI",
            thermal: t('fus.sensor.thermal', 'Thermal'),
            soil: t('fus.sensor.soil', 'Soil'),
            weather: t('fus.sensor.weather', 'Weather')
        };
    }

    var sensorColors = {
        ndvi: "#22c55e",
        thermal: "#ef4444",
        soil: "#a78bfa",
        weather: "#4da6ff"
    };

    window.loadFusionData = function () {
        emptyEl.style.display = "none";
        contentEl.style.display = "";
        matrixEl.innerHTML = '<div style="color:#888;">' + t('dash.loadingGeneric', 'Loading...') + '</div>';
        contradictionsEl.innerHTML = "";
        fieldCardsEl.innerHTML = "";

        fetchJSON("/api/intel/sensor-fusion").then(function (data) {
            if (!data) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                emptyEl.textContent = t('fus.fetchError', 'Could not fetch sensor fusion data.');
                resetStats();
                return;
            }
            renderFusion(data);
        });
    };

    function resetStats() {
        document.getElementById("fusion-total-fields").textContent = "--";
        document.getElementById("fusion-fields-with-data").textContent = "--";
        document.getElementById("fusion-avg-confidence").textContent = "--";
        document.getElementById("fusion-total-contradictions").textContent = "--";
    }

    function renderFusion(data) {
        /* Stats strip */
        document.getElementById("fusion-total-fields").textContent = data.total_fields;
        document.getElementById("fusion-fields-with-data").textContent = data.fields_with_data;
        document.getElementById("fusion-avg-confidence").textContent =
            (data.avg_confidence * 100).toFixed(0) + "%";

        var totalContra = document.getElementById("fusion-total-contradictions");
        totalContra.textContent = data.total_contradictions;
        totalContra.style.color = data.total_contradictions > 0 ? "#ef4444" : "#22c55e";

        /* Sensor consistency matrix */
        renderMatrix(data.fields);

        /* Contradictions */
        renderContradictions(data.fields);

        /* Per-field cards */
        renderFieldCards(data.fields);
    }

    function renderMatrix(fields) {
        if (!fields || fields.length === 0) {
            matrixEl.innerHTML = '<div style="color:#888;text-align:center;">' + t('fus.noFields', 'No fields with sensor data.') + '</div>';
            return;
        }

        var allSensors = ["ndvi", "thermal", "soil", "weather"];
        var html = '<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">';
        html += '<thead><tr>';
        html += '<th style="text-align:left;padding:0.5rem;color:#888;border-bottom:1px solid #333;">' + t('lbl.field', 'Field') + '</th>';
        html += '<th style="text-align:left;padding:0.5rem;color:#888;border-bottom:1px solid #333;">' + t('lbl.farm', 'Farm') + '</th>';
        var sL = getSensorLabels();
        allSensors.forEach(function (s) {
            html += '<th style="text-align:center;padding:0.5rem;color:' + sensorColors[s] + ';border-bottom:1px solid #333;">' + sL[s] + '</th>';
        });
        html += '<th style="text-align:center;padding:0.5rem;color:#888;border-bottom:1px solid #333;">' + t('fus.col.confidence', 'Confidence') + '</th>';
        html += '<th style="text-align:center;padding:0.5rem;color:#888;border-bottom:1px solid #333;">' + t('fus.col.status', 'Status') + '</th>';
        html += '</tr></thead><tbody>';

        fields.forEach(function (f) {
            var hasContra = f.contradictions && f.contradictions.length > 0;
            var rowColor = hasContra ? "#ef444422" : "transparent";
            html += '<tr style="background:' + rowColor + ';">';
            html += '<td style="padding:0.5rem;color:#eee;border-bottom:1px solid #222;">' + esc(f.field_name) + '</td>';
            html += '<td style="padding:0.5rem;color:#aaa;border-bottom:1px solid #222;">' + esc(f.farm_name) + '</td>';
            allSensors.forEach(function (s) {
                var active = f.sensors_used.indexOf(s) >= 0;
                var dot = active
                    ? '<span style="color:' + sensorColors[s] + ';font-size:1.2rem;">&#9679;</span>'
                    : '<span style="color:#444;font-size:1.2rem;">&#9675;</span>';
                html += '<td style="text-align:center;padding:0.5rem;border-bottom:1px solid #222;">' + dot + '</td>';
            });
            var confPct = (f.confidence * 100).toFixed(0) + "%";
            var confColor = f.confidence >= 0.7 ? "#22c55e" : f.confidence >= 0.4 ? "#eab308" : "#ef4444";
            html += '<td style="text-align:center;padding:0.5rem;border-bottom:1px solid #222;color:' + confColor + ';font-weight:600;">' + confPct + '</td>';
            var statusLabel = hasContra ? t('fus.status.inconsistent', 'Inconsistent') : t('fus.status.consistent', 'Consistent');
            var statusColor = hasContra ? "#ef4444" : "#22c55e";
            html += '<td style="text-align:center;padding:0.5rem;border-bottom:1px solid #222;"><span style="background:' + statusColor + '22;color:' + statusColor + ';padding:0.15rem 0.5rem;border-radius:4px;font-size:0.75rem;font-weight:600;">' + statusLabel + '</span></td>';
            html += '</tr>';
        });

        html += '</tbody></table>';
        matrixEl.innerHTML = html;
    }

    function renderContradictions(fields) {
        var allContras = [];
        fields.forEach(function (f) {
            if (f.contradictions && f.contradictions.length > 0) {
                f.contradictions.forEach(function (c) {
                    allContras.push({
                        field_name: f.field_name,
                        farm_name: f.farm_name,
                        tag: c.tag,
                        sensors: c.sensors,
                        description: c.description
                    });
                });
            }
        });

        if (allContras.length === 0) {
            contradictionsEl.innerHTML = '<div style="color:#22c55e;font-size:0.9rem;">' + t('fus.noContradictions', 'No contradictions detected — all sensors are consistent.') + '</div>';
            return;
        }

        var html = "";
        allContras.forEach(function (c) {
            var sensorBadges = c.sensors.map(function (s) {
                var color = sensorColors[s] || "#888";
                return '<span style="background:' + color + '22;color:' + color + ';padding:0.1rem 0.4rem;border-radius:3px;font-size:0.7rem;font-weight:600;margin-right:0.3rem;">' + (getSensorLabels()[s] || s) + '</span>';
            }).join("");

            html +=
                '<div style="padding:0.75rem 0;border-bottom:1px solid #222;">' +
                    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;">' +
                        '<span style="color:#eee;font-weight:600;font-size:0.9rem;">' + esc(c.field_name) + ' <span style="color:#666;font-weight:400;">(' + esc(c.farm_name) + ')</span></span>' +
                        '<div>' + sensorBadges + '</div>' +
                    '</div>' +
                    '<p style="color:#aaa;font-size:0.85rem;margin:0;line-height:1.4;">' + esc(c.description) + '</p>' +
                '</div>';
        });
        contradictionsEl.innerHTML = html;
    }

    function renderFieldCards(fields) {
        if (!fields || fields.length === 0) {
            fieldCardsEl.innerHTML = '<div class="intel-card" style="color:#888;text-align:center;">' + t('fus.noFieldCards', 'No fields with sensor data available.') + '</div>';
            return;
        }

        fields.forEach(function (f) {
            var hasContra = f.contradictions && f.contradictions.length > 0;
            var borderColor = hasContra ? "#ef4444" : "#22c55e";
            var confPct = (f.confidence * 100).toFixed(0) + "%";
            var confColor = f.confidence >= 0.7 ? "#22c55e" : f.confidence >= 0.4 ? "#eab308" : "#ef4444";

            var sensorDots = f.sensors_used.map(function (s) {
                var color = sensorColors[s] || "#888";
                return '<span style="background:' + color + '22;color:' + color + ';padding:0.1rem 0.4rem;border-radius:3px;font-size:0.7rem;font-weight:600;margin-right:0.3rem;">' + (getSensorLabels()[s] || s) + '</span>';
            }).join("");

            var card = document.createElement("div");
            card.className = "intel-card";
            card.style.borderLeft = "3px solid " + borderColor;
            card.innerHTML =
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">' +
                    '<span style="color:#eee;font-weight:600;font-size:0.95rem;">' + esc(f.field_name) + '</span>' +
                    '<span style="color:' + confColor + ';font-weight:700;font-size:0.9rem;">' + confPct + '</span>' +
                '</div>' +
                '<div style="color:#888;font-size:0.8rem;margin-bottom:0.5rem;">' + esc(f.farm_name) + '</div>' +
                '<div style="margin-bottom:0.5rem;">' + sensorDots + '</div>' +
                '<p style="color:#aaa;font-size:0.85rem;margin:0 0 0.5rem 0;line-height:1.4;">' + esc(f.assessment) + '</p>' +
                (hasContra ?
                    '<div style="margin-top:0.5rem;padding-top:0.5rem;border-top:1px solid #222;">' +
                        '<span style="color:#ef4444;font-size:0.8rem;font-weight:600;">' + f.contradictions.length + t('fus.contradictions', ' contradiction(s)') + '</span>' +
                        f.contradictions.map(function (c) {
                            return '<div style="color:#aaa;font-size:0.8rem;margin-top:0.25rem;">&bull; ' + esc(c.description) + '</div>';
                        }).join("") +
                    '</div>'
                : '<div style="color:#22c55e;font-size:0.8rem;">' + t('fus.sensorsConsistent', 'Sensors consistent') + '</div>'
                );
            fieldCardsEl.appendChild(card);
        });
    }
})();
