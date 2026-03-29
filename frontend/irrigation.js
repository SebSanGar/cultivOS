/* Irrigation scheduling page — /riego */
(function () {
    "use strict";

    var farmSel = document.getElementById("irrigation-farm-select");
    var fieldSel = document.getElementById("irrigation-field-select");
    var emptyEl = document.getElementById("irrigation-empty");
    var contentEl = document.getElementById("irrigation-content");
    var scheduleBody = document.getElementById("irrigation-schedule-body");

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

    var urgencyColors = {
        alta: "#ef4444",
        media: "#eab308",
        baja: "#22c55e"
    };

    var urgencyLabels = {
        alta: "Alta",
        media: "Media",
        baja: "Baja"
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
    }

    /* Load fields for selected farm */
    window.loadFieldsForIrrigation = function () {
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

    /* Load irrigation schedule */
    window.loadIrrigation = function () {
        var farmId = farmSel.value;
        var fieldId = fieldSel.value;
        if (!farmId || !fieldId) {
            contentEl.style.display = "none";
            emptyEl.style.display = "";
            emptyEl.textContent = "Seleccione una granja y un campo para consultar el riego.";
            resetStats();
            return;
        }
        emptyEl.style.display = "none";
        contentEl.style.display = "";

        var url = "/api/farms/" + farmId + "/fields/" + fieldId + "/irrigation";

        fetchJSON(url).then(function (data) {
            if (!data) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                emptyEl.textContent = "No se pudo obtener la programacion de riego para este campo.";
                resetStats();
                return;
            }
            renderIrrigation(data);
        });
    };

    function resetStats() {
        document.getElementById("irrigation-total-liters").textContent = "--";
        document.getElementById("irrigation-urgency").textContent = "--";
        document.getElementById("irrigation-crop").textContent = "--";
        document.getElementById("irrigation-hectares").textContent = "--";
        document.getElementById("irrigation-days").textContent = "--";
        document.getElementById("irrigation-recommendation").textContent = "";
        scheduleBody.innerHTML = "";
    }

    function renderIrrigation(data) {
        /* Stats strip */
        document.getElementById("irrigation-total-liters").textContent =
            Math.round(data.liters_total_per_ha).toLocaleString();

        var urgEl = document.getElementById("irrigation-urgency");
        urgEl.textContent = urgencyLabels[data.urgencia] || data.urgencia;
        urgEl.style.color = urgencyColors[data.urgencia] || "#ccc";

        document.getElementById("irrigation-crop").textContent = data.crop_type || "--";
        document.getElementById("irrigation-hectares").textContent =
            data.hectares ? data.hectares.toFixed(1) : "--";
        document.getElementById("irrigation-days").textContent =
            data.schedule ? data.schedule.length : 0;

        /* Recommendation */
        document.getElementById("irrigation-recommendation").textContent =
            data.recomendacion || "Sin recomendacion disponible.";

        /* Schedule table */
        scheduleBody.innerHTML = "";
        if (data.schedule && data.schedule.length > 0) {
            data.schedule.forEach(function (entry) {
                var tr = document.createElement("tr");
                tr.style.borderBottom = "1px solid #222";
                tr.innerHTML =
                    '<td style="padding:0.4rem 0.5rem;color:#ccc;font-size:0.85rem;">Dia ' + entry.day + '</td>' +
                    '<td style="padding:0.4rem 0.5rem;color:#eee;font-size:0.85rem;font-family:monospace;font-weight:600;">' +
                        Math.round(entry.liters_per_ha).toLocaleString() + '</td>' +
                    '<td style="padding:0.4rem 0.5rem;color:#888;font-size:0.85rem;">' + esc(entry.nota) + '</td>';
                scheduleBody.appendChild(tr);
            });
        }
    }

    loadFarms();
})();
