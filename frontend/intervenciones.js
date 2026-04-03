/* Intervention ranking page — /intervenciones */
(function () {
    "use strict";
    var API = "";
    var farmSel = document.getElementById("interv-farm-select");
    var fieldSel = document.getElementById("interv-field-select");
    var emptyEl = document.getElementById("interv-empty");
    var contentEl = document.getElementById("interv-content");
    var statsEl = document.getElementById("interv-stats");
    var cardsEl = document.getElementById("interv-cards");

    function fetchJSON(url) {
        return fetch(url).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
    }
    function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

    function loadFarms() {
        fetchJSON(API + "/api/farms").then(function (resp) {
            if (!resp) return;
            var farms = resp.data || resp;
            farms.forEach(function (f) {
                var opt = document.createElement("option");
                opt.value = f.id;
                opt.textContent = f.name;
                farmSel.appendChild(opt);
            });
        });
    }

    window.loadFieldsForInterventions = function () {
        fieldSel.innerHTML = '<option value="">Seleccione un campo...</option>';
        var farmId = farmSel.value;
        if (!farmId) return;
        fetchJSON(API + "/api/farms/" + farmId + "/fields").then(function (fields) {
            if (!fields) return;
            fields.forEach(function (f) {
                var opt = document.createElement("option");
                opt.value = f.id;
                opt.textContent = f.name + " (" + f.crop_type + ")";
                fieldSel.appendChild(opt);
            });
        });
    };

    window.loadInterventions = function () {
        var farmId = farmSel.value;
        var fieldId = fieldSel.value;
        if (!farmId || !fieldId) return;

        fetchJSON(API + "/api/farms/" + farmId + "/fields/" + fieldId + "/intervention-scores").then(function (data) {
            if (!data || data.length === 0) {
                emptyEl.style.display = "";
                contentEl.style.display = "none";
                return;
            }

            emptyEl.style.display = "none";
            contentEl.style.display = "";

            var interventions = data;
            var topScore = interventions[0].intervention_score || 0;
            var avgRoi = interventions.reduce(function (s, i) { return s + (i.expected_roi || 0); }, 0) / interventions.length;
            var positiveRoi = interventions.filter(function (i) { return (i.expected_roi || 0) > 0; }).length;
            var ancestralCount = interventions.filter(function (i) { return i.metodo_ancestral; }).length;

            statsEl.innerHTML =
                '<div class="stat-card"><div class="stat-value">' + interventions.length + '</div><div class="stat-label">Intervenciones</div></div>' +
                '<div class="stat-card"><div class="stat-value" style="color:#22c55e">' + Math.round(topScore) + '</div><div class="stat-label">Mayor impacto</div></div>' +
                '<div class="stat-card"><div class="stat-value" style="color:' + (avgRoi >= 0 ? "#22c55e" : "#ef4444") + '">' + Math.round(avgRoi) + '%</div><div class="stat-label">ROI promedio</div></div>' +
                '<div class="stat-card"><div class="stat-value">' + positiveRoi + '/' + interventions.length + '</div><div class="stat-label">ROI positivo</div></div>' +
                (ancestralCount > 0 ? '<div class="stat-card"><div class="stat-value" style="color:#8b5cf6">' + ancestralCount + '</div><div class="stat-label">Ancestrales</div></div>' : '');

            cardsEl.innerHTML = interventions.map(function (i, idx) {
                var score = i.intervention_score || 0;
                var costHa = i.cost_per_hectare || 0;
                var roi = i.expected_roi || 0;
                var payback = i.payback_days || 0;
                var isAncestral = i.metodo_ancestral;
                var rankColor = idx === 0 ? "#fbbf24" : idx === 1 ? "#9ca3af" : idx === 2 ? "#cd7c3b" : "#6b7280";
                var roiColor = roi >= 50 ? "#22c55e" : roi >= 0 ? "#f59e0b" : "#ef4444";
                var paybackLabel = payback === 0 ? "Gratis" : payback >= 999 ? ">999 dias" : payback + " dias";

                return '<div class="intel-card">' +
                    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">' +
                    '<span style="font-size:1.2rem;font-weight:800;color:' + rankColor + ';">#' + (idx + 1) + '</span>' +
                    '<div style="display:flex;gap:6px;">' +
                    (isAncestral ? '<span class="severity-badge" style="background:rgba(139,92,246,0.15);color:#8b5cf6;">Ancestral</span>' : '') +
                    '<span class="severity-badge" style="background:rgba(34,197,94,0.15);color:#22c55e;">Organico</span>' +
                    '</div>' +
                    '</div>' +
                    '<div class="intel-card-title">' + esc(i.tratamiento || "Intervencion") + '</div>' +
                    (i.problema ? '<div class="intel-card-meta">Problema: ' + esc(i.problema) + '</div>' : '') +
                    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;">' +
                    '<div style="text-align:center;padding:8px;background:rgba(255,255,255,0.04);border-radius:6px;">' +
                    '<div style="font-size:1.1rem;font-weight:700;color:' + roiColor + ';">' + Math.round(roi) + '%</div>' +
                    '<div style="font-size:0.65rem;opacity:0.7;">ROI esperado</div></div>' +
                    '<div style="text-align:center;padding:8px;background:rgba(255,255,255,0.04);border-radius:6px;">' +
                    '<div style="font-size:1.1rem;font-weight:700;">' + paybackLabel + '</div>' +
                    '<div style="font-size:0.65rem;opacity:0.7;">Recuperacion</div></div>' +
                    '<div style="text-align:center;padding:8px;background:rgba(255,255,255,0.04);border-radius:6px;">' +
                    '<div style="font-size:1.1rem;font-weight:700;">' + Math.round(score) + '</div>' +
                    '<div style="font-size:0.65rem;opacity:0.7;">Impacto</div></div>' +
                    '<div style="text-align:center;padding:8px;background:rgba(255,255,255,0.04);border-radius:6px;">' +
                    '<div style="font-size:1.1rem;font-weight:700;">$' + Math.round(costHa).toLocaleString() + '</div>' +
                    '<div style="font-size:0.65rem;opacity:0.7;">MXN/ha</div></div>' +
                    '</div>' +
                    '</div>';
            }).join("");
        });
    };

    loadFarms();
})();
