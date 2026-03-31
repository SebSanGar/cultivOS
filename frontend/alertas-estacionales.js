/* Seasonal alerts (Inteligencia Ancestral) — /alertas-estacionales */
(function () {
    "use strict";
    var API = "";
    var farmSel = document.getElementById("seasonal-farm-select");
    var emptyEl = document.getElementById("seasonal-empty");
    var contentEl = document.getElementById("seasonal-content");
    var statsEl = document.getElementById("seasonal-stats");
    var alertsEl = document.getElementById("seasonal-alerts");

    function fetchJSON(url) {
        return fetch(url).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
    }
    function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

    var typeIcons = { preparacion: "🌱", siembra: "🌾", cosecha: "🪴", mantenimiento: "🔧", riego: "💧", fertilizacion: "🧪" };
    var typeColors = { preparacion: "#3b82f6", siembra: "#22c55e", cosecha: "#f59e0b", mantenimiento: "#8b5cf6", riego: "#06b6d4", fertilizacion: "#ec4899" };

    function loadFarms() {
        fetchJSON(API + "/api/farms").then(function (farms) {
            if (!farms) return;
            farms.forEach(function (f) {
                var opt = document.createElement("option");
                opt.value = f.id;
                opt.textContent = f.name;
                farmSel.appendChild(opt);
            });
        });
    }

    window.loadSeasonalAlerts = function () {
        var farmId = farmSel.value;
        if (!farmId) return;

        fetchJSON(API + "/api/farms/" + farmId + "/seasonal-alerts").then(function (data) {
            if (!data || !data.alerts || data.alerts.length === 0) {
                emptyEl.style.display = "";
                contentEl.style.display = "none";
                return;
            }

            emptyEl.style.display = "none";
            contentEl.style.display = "";

            var alerts = data.alerts;
            var season = data.current_season || data.season || "temporal";
            var crops = data.crops || [];

            statsEl.innerHTML =
                '<div class="stat-card"><div class="stat-value">' + esc(season) + '</div><div class="stat-label">Temporada actual</div></div>' +
                '<div class="stat-card"><div class="stat-value">' + alerts.length + '</div><div class="stat-label">Alertas activas</div></div>' +
                (crops.length ? '<div class="stat-card"><div class="stat-value">' + crops.length + '</div><div class="stat-label">Cultivos monitoreados</div></div>' : '');

            alertsEl.innerHTML = alerts.map(function (a) {
                var aType = (a.alert_type || a.type || "mantenimiento").toLowerCase();
                var icon = typeIcons[aType] || "📋";
                var color = typeColors[aType] || "#6b7280";
                var crop = a.crop || a.crop_type || "";
                var timing = a.timing || a.when || "";
                return '<div class="intel-card" style="border-left:3px solid ' + color + ';">' +
                    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">' +
                    '<span style="font-size:1.2rem;">' + icon + ' <span style="font-size:0.7rem;font-weight:600;color:' + color + ';">' + esc(aType) + '</span></span>' +
                    (crop ? '<span class="severity-badge" style="background:rgba(34,197,94,0.15);color:#22c55e;">' + esc(crop) + '</span>' : '') +
                    '</div>' +
                    '<div class="intel-card-title">' + esc(a.message || a.description || a.alert || "") + '</div>' +
                    (timing ? '<div class="intel-card-meta">Momento: ' + esc(timing) + '</div>' : '') +
                    (a.tek_source ? '<div class="intel-card-meta" style="color:#8b5cf6;">Fuente TEK: ' + esc(a.tek_source) + '</div>' : '') +
                    '</div>';
            }).join("");
        });
    };

    loadFarms();
})();
