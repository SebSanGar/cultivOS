/* Anomaly detection center — /anomalias */
(function () {
    "use strict";

    var farmSel = document.getElementById("anom-farm-select");
    var fieldSel = document.getElementById("anom-field-select");
    var emptyEl = document.getElementById("anom-empty");
    var noneEl = document.getElementById("anom-none");
    var contentEl = document.getElementById("anom-content");
    var timelineEl = document.getElementById("anom-timeline");

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
    window.loadFieldsForAnom = function () {
        fieldSel.innerHTML = '<option value="">Seleccione un campo...</option>';
        contentEl.style.display = "none";
        timelineEl.style.display = "none";
        noneEl.style.display = "none";
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

    /* Load anomalies for selected field */
    window.loadAnomalies = function () {
        var farmId = farmSel.value;
        var fieldId = fieldSel.value;
        if (!farmId || !fieldId) {
            contentEl.style.display = "none";
            timelineEl.style.display = "none";
            noneEl.style.display = "none";
            emptyEl.style.display = "";
            resetStats();
            return;
        }
        emptyEl.style.display = "none";
        noneEl.style.display = "none";

        fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/anomalies").then(function (data) {
            if (!data) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                resetStats();
                return;
            }
            renderAnomalies(data);
        });
    };

    function resetStats() {
        document.getElementById("anom-total-count").textContent = "--";
        document.getElementById("anom-health-count").textContent = "--";
        document.getElementById("anom-ndvi-count").textContent = "--";
    }

    function severityClass(type, value) {
        /* Health: drop > 25 = critical, 15-25 = moderate */
        /* NDVI: drop_pct > 30 = critical, 20-30 = moderate */
        if (type === "health") {
            return value > 25 ? "anom-critical" : "anom-moderate";
        }
        return value > 30 ? "anom-critical" : "anom-moderate";
    }

    function severityLabel(type, value) {
        if (type === "health") {
            return value > 25 ? "Critica" : "Moderada";
        }
        return value > 30 ? "Critica" : "Moderada";
    }

    function renderAnomalies(data) {
        var healthList = data.health_anomalies || [];
        var ndviList = data.ndvi_anomalies || [];
        var total = healthList.length + ndviList.length;

        /* Stats strip */
        document.getElementById("anom-total-count").textContent = total;
        document.getElementById("anom-health-count").textContent = healthList.length;
        document.getElementById("anom-ndvi-count").textContent = ndviList.length;

        if (total === 0) {
            contentEl.style.display = "none";
            noneEl.style.display = "";
            return;
        }

        contentEl.style.display = "";
        noneEl.style.display = "none";
        timelineEl.style.display = "";

        /* Health anomaly cards */
        var healthContainer = document.getElementById("anom-health-cards");
        var healthNone = document.getElementById("anom-health-none");
        healthContainer.innerHTML = "";
        if (healthList.length === 0) {
            healthNone.style.display = "";
        } else {
            healthNone.style.display = "none";
            healthList.forEach(function (a) {
                var sev = severityClass("health", a.drop);
                var label = severityLabel("health", a.drop);
                var card = document.createElement("div");
                card.className = "regen-rec-card " + sev;
                card.innerHTML =
                    '<div class="anom-card-header">' +
                        '<span class="anom-badge ' + sev + '">' + esc(label) + '</span>' +
                        '<span class="anom-drop">-' + a.drop.toFixed(1) + ' pts</span>' +
                    '</div>' +
                    '<p class="anom-detail">' +
                        'Puntuacion anterior: <strong>' + a.previous_score.toFixed(1) + '</strong> &rarr; ' +
                        'Actual: <strong>' + a.current_score.toFixed(1) + '</strong>' +
                    '</p>' +
                    '<p class="regen-rec-text">' + esc(a.recommendation) + '</p>';
                healthContainer.appendChild(card);
            });
        }

        /* NDVI anomaly cards */
        var ndviContainer = document.getElementById("anom-ndvi-cards");
        var ndviNone = document.getElementById("anom-ndvi-none");
        ndviContainer.innerHTML = "";
        if (ndviList.length === 0) {
            ndviNone.style.display = "";
        } else {
            ndviNone.style.display = "none";
            ndviList.forEach(function (a) {
                var sev = severityClass("ndvi", a.drop_pct);
                var label = severityLabel("ndvi", a.drop_pct);
                var card = document.createElement("div");
                card.className = "regen-rec-card " + sev;
                card.innerHTML =
                    '<div class="anom-card-header">' +
                        '<span class="anom-badge ' + sev + '">' + esc(label) + '</span>' +
                        '<span class="anom-drop">-' + a.drop_pct.toFixed(1) + '%</span>' +
                    '</div>' +
                    '<p class="anom-detail">' +
                        'NDVI actual: <strong>' + a.current_ndvi.toFixed(2) + '</strong> | ' +
                        'Promedio historico: <strong>' + a.historical_avg.toFixed(2) + '</strong>' +
                    '</p>' +
                    '<p class="regen-rec-text">' + esc(a.recommendation) + '</p>';
                ndviContainer.appendChild(card);
            });
        }

        /* Recommendations summary */
        var recsContainer = document.getElementById("anom-recommendations");
        recsContainer.innerHTML = "";
        var allRecs = [];
        healthList.forEach(function (a) { if (a.recommendation) allRecs.push(a.recommendation); });
        ndviList.forEach(function (a) { if (a.recommendation) allRecs.push(a.recommendation); });
        allRecs.forEach(function (rec) {
            var el = document.createElement("div");
            el.className = "regen-rec-card";
            el.innerHTML = '<p class="regen-rec-text">' + esc(rec) + '</p>';
            recsContainer.appendChild(el);
        });
    }

    loadFarms();
})();
