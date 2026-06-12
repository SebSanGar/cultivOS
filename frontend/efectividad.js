/* Treatment effectiveness report — /efectividad */
(function () {
    "use strict";
    var API = "";
    var emptyEl = document.getElementById("eff-empty");
    var contentEl = document.getElementById("eff-content");
    var statsEl = document.getElementById("eff-stats");
    var cardsEl = document.getElementById("eff-cards");

    function fetchJSON(url) {
        return fetch(url).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
    }
    function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
    function loc(o, base) { return window.cultivOS_i18n ? window.cultivOS_i18n.localized(o, base) : (o[base + '_es'] || o[base] || ''); }
    function _t(key, fallback) { return (window.cultivOS_i18n && window.cultivOS_i18n.t) ? window.cultivOS_i18n.t(key) : fallback; }

    window.loadEffectiveness = function () {
        fetchJSON(API + "/api/intel/treatment-effectiveness-report").then(function (data) {
            if (!data) {
                emptyEl.style.display = "";
                contentEl.style.display = "none";
                return;
            }

            emptyEl.style.display = "none";
            contentEl.style.display = "";

            var treatments = data.treatments || data.report || [];
            var totalApplied = treatments.reduce(function (sum, t) { return sum + (t.usage_count || t.times_applied || 0); }, 0);
            var avgDelta = treatments.length > 0
                ? Math.round(treatments.reduce(function (sum, t) { return sum + (t.avg_health_delta || t.health_delta || 0); }, 0) / treatments.length)
                : 0;
            var bestTreatment = treatments.length > 0 ? (treatments[0].treatment || treatments[0].name || "—") : "—";

            statsEl.innerHTML =
                '<div class="stat-card"><div class="stat-value">' + treatments.length + '</div><div class="stat-label">' + _t('eff.stat.evaluated', 'Treatments evaluated') + '</div></div>' +
                '<div class="stat-card"><div class="stat-value">' + totalApplied + '</div><div class="stat-label">' + _t('eff.stat.applications', 'Total applications') + '</div></div>' +
                '<div class="stat-card"><div class="stat-value" style="color:' + (avgDelta >= 0 ? '#22c55e' : '#ef4444') + '">' + (avgDelta >= 0 ? '+' : '') + avgDelta + '</div><div class="stat-label">' + _t('eff.stat.avgDelta', 'Avg health delta') + '</div></div>' +
                '<div class="stat-card"><div class="stat-value" style="font-size:0.75rem;">' + esc(bestTreatment) + '</div><div class="stat-label">' + _t('eff.stat.bestTreatment', 'Best treatment') + '</div></div>';

            cardsEl.innerHTML = treatments.map(function (t, idx) {
                var delta = t.avg_health_delta || t.health_delta || 0;
                var deltaColor = delta >= 10 ? "#22c55e" : delta >= 0 ? "#eab308" : "#ef4444";
                var deltaStr = (delta >= 0 ? "+" : "") + Math.round(delta);
                var count = t.usage_count || t.times_applied || 0;
                var isOrganic = t.organic || t.is_organic;
                var isAncestral = t.ancestral || t.ancestral_method;

                return '<div class="intel-card">' +
                    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">' +
                    '<div class="intel-card-title">' + esc(t.treatment || t.name || loc(t, 'tratamiento') || _t('eff.fallback.treatment', 'Treatment')) + '</div>' +
                    '<div style="font-size:1.2rem;font-weight:800;color:' + deltaColor + ';">' + deltaStr + '</div>' +
                    '</div>' +
                    '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px;">' +
                    (isOrganic ? '<span class="severity-badge" style="background:rgba(34,197,94,0.15);color:#22c55e;">' + _t('eff.badge.organic', 'Organic') + '</span>' : '') +
                    (isAncestral ? '<span class="severity-badge" style="background:rgba(139,92,246,0.15);color:#8b5cf6;">' + _t('eff.badge.ancestral', 'Ancestral') + '</span>' : '') +
                    '<span class="severity-badge" style="background:rgba(99,102,241,0.15);color:#6366f1;">' + count + _t('eff.suffix.apps', ' applications') + '</span>' +
                    '</div>' +
                    (t.best_for || t.crop ? '<div class="intel-card-meta">' + _t('eff.prefix.bestFor', 'Best for: ') + esc(t.best_for || t.crop || "") + '</div>' : '') +
                    '<div style="margin-top:8px;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;">' +
                    '<div style="width:' + Math.min(100, Math.max(5, Math.abs(delta) * 2)) + '%;height:100%;background:' + deltaColor + ';border-radius:3px;"></div>' +
                    '</div>' +
                    '</div>';
            }).join("");
        });
    };

    // Auto-load on page open
    loadEffectiveness();
})();
