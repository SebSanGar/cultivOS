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
            if (!data || !data.interventions || data.interventions.length === 0) {
                emptyEl.style.display = "";
                contentEl.style.display = "none";
                return;
            }

            emptyEl.style.display = "none";
            contentEl.style.display = "";

            var interventions = data.interventions;
            var topScore = interventions.length > 0 ? (interventions[0].score || interventions[0].impact_score || 0) : 0;
            var organicCount = interventions.filter(function (i) { return i.organic || i.is_organic; }).length;
            var ancestralCount = interventions.filter(function (i) { return i.ancestral || i.ancestral_method; }).length;

            statsEl.innerHTML =
                '<div class="stat-card"><div class="stat-value">' + interventions.length + '</div><div class="stat-label">Intervenciones</div></div>' +
                '<div class="stat-card"><div class="stat-value" style="color:#22c55e">' + Math.round(topScore) + '</div><div class="stat-label">Mayor impacto</div></div>' +
                '<div class="stat-card"><div class="stat-value">' + organicCount + '</div><div class="stat-label">Organicas</div></div>' +
                (ancestralCount > 0 ? '<div class="stat-card"><div class="stat-value" style="color:#8b5cf6">' + ancestralCount + '</div><div class="stat-label">Ancestrales</div></div>' : '');

            cardsEl.innerHTML = interventions.map(function (i, idx) {
                var score = i.score || i.impact_score || 0;
                var cost = i.cost_per_ha || i.costo_estimado_mxn || 0;
                var isOrganic = i.organic || i.is_organic;
                var isAncestral = i.ancestral || i.ancestral_method;
                var effectiveness = i.cost_effectiveness || (score > 0 && cost > 0 ? Math.round(score / cost * 1000) : 0);
                var rankColor = idx === 0 ? "#fbbf24" : idx === 1 ? "#9ca3af" : idx === 2 ? "#cd7c3b" : "#6b7280";

                return '<div class="intel-card">' +
                    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">' +
                    '<span style="font-size:1.2rem;font-weight:800;color:' + rankColor + ';">#' + (idx + 1) + '</span>' +
                    '<div style="display:flex;gap:6px;">' +
                    (isOrganic ? '<span class="severity-badge" style="background:rgba(34,197,94,0.15);color:#22c55e;">Organico</span>' : '') +
                    (isAncestral ? '<span class="severity-badge" style="background:rgba(139,92,246,0.15);color:#8b5cf6;">Ancestral</span>' : '') +
                    '</div>' +
                    '</div>' +
                    '<div class="intel-card-title">' + esc(i.treatment || i.name || i.tratamiento || "Intervencion") + '</div>' +
                    (i.problem || i.problema ? '<div class="intel-card-meta">Problema: ' + esc(i.problem || i.problema) + '</div>' : '') +
                    '<div style="display:flex;gap:16px;margin-top:8px;font-size:0.7rem;">' +
                    '<span>Impacto: <strong>' + Math.round(score) + '</strong></span>' +
                    (cost > 0 ? '<span>Costo: <strong>$' + Math.round(cost).toLocaleString() + ' MXN/ha</strong></span>' : '') +
                    (effectiveness > 0 ? '<span>Efectividad: <strong>' + effectiveness + '</strong></span>' : '') +
                    '</div>' +
                    '</div>';
            }).join("");
        });
    };

    loadFarms();
})();
