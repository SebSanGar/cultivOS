/* Data completeness dashboard — /completitud */
(function () {
    "use strict";
    var API = "";
    var farmSel = document.getElementById("comp-farm-select");
    var emptyEl = document.getElementById("comp-empty");
    var contentEl = document.getElementById("comp-content");
    var statsEl = document.getElementById("comp-stats");
    var sourcesEl = document.getElementById("comp-sources");
    var recsEl = document.getElementById("comp-recommendations");

    function fetchJSON(url) {
        return fetch(url).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
    }
    function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

    function scoreColor(pct) {
        if (pct >= 80) return "#22c55e";
        if (pct >= 50) return "#eab308";
        return "#ef4444";
    }

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

    window.loadCompleteness = function () {
        var farmId = farmSel.value;
        if (!farmId) return;

        fetchJSON(API + "/api/farms/" + farmId + "/data-completeness").then(function (data) {
            if (!data) {
                emptyEl.style.display = "";
                contentEl.style.display = "none";
                return;
            }

            emptyEl.style.display = "none";
            contentEl.style.display = "";

            var overall = data.overall_score || data.completeness_pct || 0;
            var sources = data.sources || data.breakdown || [];

            statsEl.innerHTML =
                '<div class="stat-card"><div class="stat-value" style="color:' + scoreColor(overall) + '">' + Math.round(overall) + '%</div><div class="stat-label">Completitud general</div></div>' +
                '<div class="stat-card"><div class="stat-value">' + (Array.isArray(sources) ? sources.length : Object.keys(sources).length) + '</div><div class="stat-label">Fuentes de datos</div></div>';

            // Handle both array and object formats
            var sourceList = Array.isArray(sources) ? sources : Object.entries(sources).map(function (e) {
                return { source: e[0], score: typeof e[1] === "number" ? e[1] : (e[1].score || e[1].pct || 0), status: e[1].status || "" };
            });

            sourcesEl.innerHTML = sourceList.map(function (s) {
                var pct = s.score || s.pct || s.completeness_pct || 0;
                var name = s.source || s.name || "Desconocido";
                var color = scoreColor(pct);
                var barWidth = Math.max(5, Math.min(100, pct));
                return '<div class="intel-card">' +
                    '<div class="intel-card-title">' + esc(name) + '</div>' +
                    '<div style="display:flex;align-items:center;gap:12px;margin-top:8px;">' +
                    '<div style="flex:1;height:8px;background:rgba(255,255,255,0.1);border-radius:4px;overflow:hidden;">' +
                    '<div style="width:' + barWidth + '%;height:100%;background:' + color + ';border-radius:4px;transition:width 0.5s;"></div>' +
                    '</div>' +
                    '<span style="font-weight:700;color:' + color + ';min-width:40px;text-align:right;">' + Math.round(pct) + '%</span>' +
                    '</div>' +
                    (s.status ? '<div class="intel-card-meta" style="margin-top:6px;">' + esc(s.status) + '</div>' : '') +
                    '</div>';
            }).join("");

            var recs = data.recommendations || [];
            if (recs.length > 0) {
                recsEl.innerHTML = '<h3 style="font-size:0.9rem;font-weight:700;margin-bottom:12px;">Recomendaciones para mejorar completitud</h3>' +
                    recs.map(function (r) {
                        return '<div class="intel-card" style="border-left:3px solid #eab308;">' +
                            '<div class="intel-card-desc">' + esc(typeof r === "string" ? r : r.message || r.recommendation || "") + '</div>' +
                            '</div>';
                    }).join("");
            } else {
                recsEl.innerHTML = "";
            }
        });
    };

    loadFarms();
})();
