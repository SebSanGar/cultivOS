/* Seasonal comparison page — /estaciones */
(function () {
    "use strict";

    var farmSel = document.getElementById("seasonal-farm-select");
    var fieldSel = document.getElementById("seasonal-field-select");
    var yearSel = document.getElementById("seasonal-year-select");
    var emptyEl = document.getElementById("seasonal-empty");
    var contentEl = document.getElementById("seasonal-content");
    var cardsEl = document.getElementById("seasonal-cards");
    var tableEl = document.getElementById("seasonal-comparison-table");
    var deltaEl = document.getElementById("seasonal-delta");

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

    function fmt(v, decimals) {
        if (v === null || v === undefined) return "--";
        return Number(v).toFixed(decimals !== undefined ? decimals : 1);
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
    window.loadFieldsForSeasonal = function () {
        fieldSel.innerHTML = '<option value="">Seleccione un campo...</option>';
        yearSel.innerHTML = '<option value="">Todos los anos</option>';
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

    /* Load seasonal comparison data */
    window.loadSeasonalComparison = function () {
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

        var url = "/api/farms/" + farmId + "/fields/" + fieldId + "/seasonal-comparison";
        var year = yearSel.value;
        if (year) url += "?year=" + year;

        fetchJSON(url).then(function (data) {
            if (!data) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                emptyEl.textContent = "No se pudo cargar la comparacion estacional.";
                resetStats();
                return;
            }
            renderComparison(data);
            populateYears(data.available_years);
        });
    };

    function populateYears(years) {
        if (!years || yearSel.options.length > 1) return;
        years.forEach(function (y) {
            var opt = document.createElement("option");
            opt.value = y;
            opt.textContent = y;
            yearSel.appendChild(opt);
        });
    }

    function resetStats() {
        document.getElementById("seasonal-stat-temporal").textContent = "--";
        document.getElementById("seasonal-stat-secas").textContent = "--";
        document.getElementById("seasonal-stat-delta").textContent = "--";
        cardsEl.innerHTML = "";
        tableEl.innerHTML = "";
        deltaEl.innerHTML = "";
    }

    function renderComparison(data) {
        var t = data.temporal || {};
        var s = data.secas || {};

        /* Stats strip */
        var tScore = t.avg_health_score;
        var sScore = s.avg_health_score;
        document.getElementById("seasonal-stat-temporal").textContent = tScore !== null && tScore !== undefined ? fmt(tScore, 1) : "--";
        document.getElementById("seasonal-stat-secas").textContent = sScore !== null && sScore !== undefined ? fmt(sScore, 1) : "--";

        if (tScore !== null && tScore !== undefined && sScore !== null && sScore !== undefined) {
            var delta = tScore - sScore;
            var sign = delta >= 0 ? "+" : "";
            document.getElementById("seasonal-stat-delta").textContent = sign + fmt(delta, 1);
            document.getElementById("seasonal-stat-delta").style.color = delta >= 0 ? "#22c55e" : "#ef4444";
        } else {
            document.getElementById("seasonal-stat-delta").textContent = "--";
            document.getElementById("seasonal-stat-delta").style.color = "";
        }

        /* Season cards */
        cardsEl.innerHTML = "";
        renderSeasonCard("Temporal (Jun-Oct)", "#22c55e", t);
        renderSeasonCard("Secas (Nov-May)", "#eab308", s);

        /* Comparison table */
        renderTable(t, s);

        /* Delta section */
        renderDelta(t, s);
    }

    function renderSeasonCard(label, color, season) {
        var card = document.createElement("div");
        card.className = "intel-card";
        card.style.cssText = "border-left:4px solid " + color + ";";

        var scoreText = season.avg_health_score !== null && season.avg_health_score !== undefined
            ? fmt(season.avg_health_score, 1) : "Sin datos";
        var ndviText = season.avg_ndvi !== null && season.avg_ndvi !== undefined
            ? fmt(season.avg_ndvi, 4) : "Sin datos";

        card.innerHTML =
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">' +
                '<span style="color:' + color + ';font-weight:700;font-size:0.85rem;text-transform:uppercase;">' +
                    esc(label) +
                '</span>' +
                '<span style="background:' + color + '22;color:' + color + ';padding:0.2rem 0.6rem;border-radius:4px;font-size:0.75rem;font-weight:600;">' +
                    (season.data_points || 0) + ' mediciones' +
                '</span>' +
            '</div>' +
            '<div style="font-size:2rem;font-weight:800;color:#eee;margin-bottom:0.5rem;">' + esc(scoreText) + '</div>' +
            '<div style="color:#999;font-size:0.85rem;margin-bottom:0.5rem;">Salud promedio</div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-top:0.75rem;">' +
                '<div>' +
                    '<div style="color:#eee;font-weight:600;font-size:1rem;">' + esc(ndviText) + '</div>' +
                    '<div style="color:#666;font-size:0.75rem;">NDVI promedio</div>' +
                '</div>' +
                '<div>' +
                    '<div style="color:#eee;font-weight:600;font-size:1rem;">' + (season.treatment_count || 0) + '</div>' +
                    '<div style="color:#666;font-size:0.75rem;">Tratamientos</div>' +
                '</div>' +
            '</div>';

        cardsEl.appendChild(card);
    }

    function renderTable(t, s) {
        var rows = [
            {label: "Salud promedio", tVal: fmt(t.avg_health_score, 1), sVal: fmt(s.avg_health_score, 1)},
            {label: "NDVI promedio", tVal: fmt(t.avg_ndvi, 4), sVal: fmt(s.avg_ndvi, 4)},
            {label: "Tratamientos aplicados", tVal: String(t.treatment_count || 0), sVal: String(s.treatment_count || 0)},
            {label: "Mediciones", tVal: String(t.data_points || 0), sVal: String(s.data_points || 0)},
        ];

        var html =
            '<table style="width:100%;border-collapse:collapse;background:#141414;border-radius:8px;overflow:hidden;">' +
            '<thead>' +
                '<tr style="border-bottom:1px solid #333;">' +
                    '<th style="padding:0.75rem 1rem;text-align:left;color:#999;font-size:0.8rem;font-weight:500;">Metrica</th>' +
                    '<th style="padding:0.75rem 1rem;text-align:center;color:#22c55e;font-size:0.8rem;font-weight:600;">Temporal</th>' +
                    '<th style="padding:0.75rem 1rem;text-align:center;color:#eab308;font-size:0.8rem;font-weight:600;">Secas</th>' +
                    '<th style="padding:0.75rem 1rem;text-align:center;color:#999;font-size:0.8rem;font-weight:500;">Diferencia</th>' +
                '</tr>' +
            '</thead><tbody>';

        rows.forEach(function (row) {
            var tNum = parseFloat(row.tVal);
            var sNum = parseFloat(row.sVal);
            var deltaText = "--";
            var deltaColor = "#999";
            if (!isNaN(tNum) && !isNaN(sNum)) {
                var d = tNum - sNum;
                var sign = d >= 0 ? "+" : "";
                deltaText = sign + d.toFixed(row.label.indexOf("NDVI") >= 0 ? 4 : 1);
                deltaColor = d >= 0 ? "#22c55e" : "#ef4444";
            }
            html +=
                '<tr style="border-bottom:1px solid #222;">' +
                    '<td style="padding:0.6rem 1rem;color:#ccc;font-size:0.85rem;">' + esc(row.label) + '</td>' +
                    '<td style="padding:0.6rem 1rem;text-align:center;color:#eee;font-family:monospace;">' + esc(row.tVal) + '</td>' +
                    '<td style="padding:0.6rem 1rem;text-align:center;color:#eee;font-family:monospace;">' + esc(row.sVal) + '</td>' +
                    '<td style="padding:0.6rem 1rem;text-align:center;color:' + deltaColor + ';font-family:monospace;font-weight:600;">' + esc(deltaText) + '</td>' +
                '</tr>';
        });

        html += '</tbody></table>';
        tableEl.innerHTML = html;
    }

    function renderDelta(t, s) {
        var tScore = t.avg_health_score;
        var sScore = s.avg_health_score;
        if (tScore === null || tScore === undefined || sScore === null || sScore === undefined) {
            deltaEl.innerHTML = '<div class="intel-card" style="text-align:center;color:#666;">Se necesitan datos en ambas temporadas para calcular la diferencia estacional.</div>';
            return;
        }
        var diff = tScore - sScore;
        var better = diff >= 0 ? "temporal" : "secas";
        var betterLabel = diff >= 0 ? "Temporal (Jun-Oct)" : "Secas (Nov-May)";
        var color = diff >= 0 ? "#22c55e" : "#eab308";

        deltaEl.innerHTML =
            '<div class="intel-card" style="border-left:4px solid ' + color + ';">' +
                '<h3 style="color:#eee;margin:0 0 0.5rem 0;">Resumen Estacional</h3>' +
                '<p style="color:#999;font-size:0.9rem;line-height:1.6;">' +
                    'La temporada <strong style="color:' + color + ';">' + esc(betterLabel) + '</strong> ' +
                    'muestra mejor rendimiento con <strong style="color:#eee;">' + fmt(Math.abs(diff), 1) + ' puntos</strong> de ventaja en salud promedio.' +
                '</p>' +
            '</div>';
    }

    loadFarms();
})();
