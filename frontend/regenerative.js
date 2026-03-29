/* Regenerative scorecard page — /regenerativo */
(function () {
    "use strict";

    var farmSel = document.getElementById("regen-farm-select");
    var fieldSel = document.getElementById("regen-field-select");
    var emptyEl = document.getElementById("regen-empty");
    var contentEl = document.getElementById("regen-content");

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
    window.loadFieldsForRegen = function () {
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
                opt.textContent = f.name;
                fieldSel.appendChild(opt);
            });
        });
    };

    /* Load regenerative score for selected field */
    window.loadRegenScore = function () {
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

        fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/regenerative-score").then(function (data) {
            if (!data) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                resetStats();
                return;
            }
            renderScore(data);
        });
    };

    function resetStats() {
        document.getElementById("regen-total-score").textContent = "--";
        document.getElementById("regen-treatments-count").textContent = "--";
        document.getElementById("regen-recs-count").textContent = "--";
        document.getElementById("regen-score-value").textContent = "0";
        document.getElementById("regen-score-label").textContent = "Sin datos";
    }

    function renderScore(data) {
        var score = data.score;
        var breakdown = data.breakdown;
        var recs = data.recommendations;

        /* Stats strip */
        document.getElementById("regen-total-score").textContent = score.toFixed(1);
        var totalComponents = Object.values(breakdown).filter(function (v) { return v > 0; }).length;
        document.getElementById("regen-treatments-count").textContent = totalComponents + "/5";
        document.getElementById("regen-recs-count").textContent = recs.length;

        /* Gauge */
        renderGauge(score);

        /* Breakdown cards */
        renderBreakdownCard("organic", breakdown.organic_treatments, 25);
        renderBreakdownCard("ancestral", breakdown.ancestral_methods, 20);
        renderBreakdownCard("soil", breakdown.soil_organic_trend, 25);
        renderBreakdownCard("microbiome", breakdown.microbiome_health, 20);
        renderBreakdownCard("diversity", breakdown.treatment_diversity, 10);

        /* Recommendations */
        var recsContainer = document.getElementById("regen-recommendations");
        var noRecsEl = document.getElementById("regen-no-recs");
        recsContainer.innerHTML = "";
        if (recs.length === 0) {
            noRecsEl.style.display = "";
        } else {
            noRecsEl.style.display = "none";
            recs.forEach(function (rec) {
                var card = document.createElement("div");
                card.className = "regen-rec-card";
                card.innerHTML = '<p class="regen-rec-text">' + esc(rec) + "</p>";
                recsContainer.appendChild(card);
            });
        }
    }

    function renderGauge(score) {
        var arc = document.getElementById("regen-gauge-arc");
        var totalLen = 251.33; // half-circle arc length
        var fill = (score / 100) * totalLen;
        arc.setAttribute("stroke-dasharray", fill + " " + totalLen);

        // Color based on score
        var color = score >= 75 ? "#22c55e" : score >= 50 ? "#eab308" : score >= 25 ? "#f97316" : "#ef4444";
        arc.setAttribute("stroke", color);

        document.getElementById("regen-score-value").textContent = Math.round(score);

        var label = score >= 75 ? "Excelente" : score >= 50 ? "Bueno" : score >= 25 ? "En progreso" : "Necesita atencion";
        document.getElementById("regen-score-label").textContent = label;
    }

    function renderBreakdownCard(key, value, max) {
        document.getElementById("regen-" + key + "-val").textContent = value.toFixed(1);
        var bar = document.getElementById("regen-" + key + "-bar");
        var pct = max > 0 ? (value / max) * 100 : 0;
        bar.style.width = Math.min(pct, 100) + "%";
        var color = pct >= 75 ? "#22c55e" : pct >= 50 ? "#eab308" : pct >= 25 ? "#f97316" : "#ef4444";
        bar.style.backgroundColor = color;
    }

    loadFarms();
})();
