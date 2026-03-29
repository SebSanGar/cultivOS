/* Crop rotation planner page — /rotacion */
(function () {
    "use strict";

    var farmSel = document.getElementById("rotation-farm-select");
    var fieldSel = document.getElementById("rotation-field-select");
    var emptyEl = document.getElementById("rotation-empty");
    var contentEl = document.getElementById("rotation-content");
    var cardsEl = document.getElementById("rotation-cards");

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

    var seasonLabels = {
        secas: "Secas (Nov-May)",
        temporal: "Temporal (Jun-Oct)",
        transicion: "Transicion"
    };

    var seasonColors = {
        secas: "#eab308",
        temporal: "#22c55e",
        transicion: "#4da6ff"
    };

    var purposeIcons = {
        "fijacion de nitrogeno": "N+",
        "cobertura / abono verde": "CV",
        "cultivo principal": "CP",
        "diversificacion": "DIV"
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
        emptyEl.style.display = "";
    }

    /* Load fields for selected farm */
    window.loadFieldsForRotation = function () {
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

    /* Load rotation plan for selected field */
    window.loadRotationPlan = function () {
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

        fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/rotation").then(function (data) {
            if (!data || !data.plan) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                emptyEl.textContent = data && data.detail
                    ? data.detail
                    : "No se pudo generar el plan de rotacion. Verifique que el campo tiene un cultivo asignado.";
                resetStats();
                return;
            }
            renderPlan(data);
        });
    };

    function resetStats() {
        document.getElementById("rotation-last-crop").textContent = "--";
        document.getElementById("rotation-region").textContent = "--";
        document.getElementById("rotation-seasons").textContent = "--";
        cardsEl.innerHTML = "";
    }

    function renderPlan(data) {
        /* Stats strip */
        document.getElementById("rotation-last-crop").textContent = capitalize(data.last_crop);
        document.getElementById("rotation-region").textContent = capitalize(data.region);
        document.getElementById("rotation-seasons").textContent = data.plan.length;

        /* Season cards */
        cardsEl.innerHTML = "";
        data.plan.forEach(function (entry, idx) {
            var color = seasonColors[entry.season] || "#4da6ff";
            var seasonLabel = seasonLabels[entry.season] || capitalize(entry.season);
            var purposeIcon = purposeIcons[entry.purpose] || "";

            var card = document.createElement("div");
            card.className = "intel-card";
            card.style.cssText = "border-left:4px solid " + color + ";";

            card.innerHTML =
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">' +
                    '<span style="color:' + color + ';font-weight:700;font-size:0.85rem;text-transform:uppercase;">' +
                        esc(seasonLabel) +
                    '</span>' +
                    '<span style="background:' + color + '22;color:' + color + ';padding:0.2rem 0.6rem;border-radius:4px;font-size:0.75rem;font-weight:600;">' +
                        'Temporada ' + (idx + 1) +
                    '</span>' +
                '</div>' +
                '<h3 style="color:#eee;font-size:1.3rem;margin:0 0 0.5rem 0;">' + esc(capitalize(entry.crop)) + '</h3>' +
                (purposeIcon
                    ? '<div style="margin-bottom:0.5rem;"><span style="background:#333;color:#ccc;padding:0.15rem 0.5rem;border-radius:3px;font-size:0.75rem;font-weight:500;">' + esc(purposeIcon) + ' ' + esc(capitalize(entry.purpose)) + '</span></div>'
                    : '') +
                '<p style="color:#999;font-size:0.85rem;line-height:1.5;margin:0 0 0.75rem 0;">' + esc(entry.reason) + '</p>' +
                '<div style="color:#666;font-size:0.8rem;">' + esc(entry.months) + '</div>';

            cardsEl.appendChild(card);
        });
    }

    function capitalize(s) {
        if (!s) return "";
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    loadFarms();
})();
