/* Drone mission planner page — /mision */
(function () {
    "use strict";

    var farmSel = document.getElementById("mission-farm-select");
    var fieldSel = document.getElementById("mission-field-select");
    var typeSel = document.getElementById("mission-type-select");
    var droneSel = document.getElementById("mission-drone-select");
    var emptyEl = document.getElementById("mission-empty");
    var contentEl = document.getElementById("mission-content");
    var waypointsBody = document.getElementById("mission-waypoints");

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

    var patternLabels = {
        lawnmower: "Corte de Cesped",
        crosshatch: "Cuadricula",
        spiral: "Espiral"
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
    window.loadFieldsForMission = function () {
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

    /* Generate mission plan */
    window.generateMission = function () {
        var farmId = farmSel.value;
        var fieldId = fieldSel.value;
        if (!farmId || !fieldId) {
            contentEl.style.display = "none";
            emptyEl.style.display = "";
            emptyEl.textContent = "Seleccione una granja y un campo para generar la mision.";
            resetStats();
            return;
        }
        emptyEl.style.display = "none";
        contentEl.style.display = "";

        var missionType = typeSel.value;
        var droneType = droneSel.value;
        var url = "/api/farms/" + farmId + "/fields/" + fieldId + "/mission-plan"
            + "?mission_type=" + encodeURIComponent(missionType)
            + "&drone_type=" + encodeURIComponent(droneType);

        fetchJSON(url).then(function (data) {
            if (!data || !data.waypoints) {
                contentEl.style.display = "none";
                emptyEl.style.display = "";
                emptyEl.textContent = "No se pudo generar la mision. Verifique que el campo tiene coordenadas de limites definidas.";
                resetStats();
                return;
            }
            renderMission(data);
        });
    };

    function resetStats() {
        document.getElementById("mission-duration").textContent = "--";
        document.getElementById("mission-area").textContent = "--";
        document.getElementById("mission-batteries").textContent = "--";
        document.getElementById("mission-photos").textContent = "--";
        document.getElementById("mission-distance").textContent = "--";
        document.getElementById("mission-altitude").textContent = "--";
        document.getElementById("mission-speed").textContent = "--";
        document.getElementById("mission-pattern").textContent = "--";
        document.getElementById("mission-overlap").textContent = "--";
        waypointsBody.innerHTML = "";
    }

    function renderMission(data) {
        /* Stats strip */
        document.getElementById("mission-duration").textContent = data.estimated_duration_min.toFixed(1);
        document.getElementById("mission-area").textContent = data.area_hectares.toFixed(2);
        document.getElementById("mission-batteries").textContent = data.batteries_needed;
        document.getElementById("mission-photos").textContent = data.estimated_photos;
        document.getElementById("mission-distance").textContent = Math.round(data.total_distance_m).toLocaleString();

        /* Flight params */
        document.getElementById("mission-altitude").textContent = data.altitude_m + " m";
        document.getElementById("mission-speed").textContent = data.speed_ms + " m/s";
        document.getElementById("mission-pattern").textContent = patternLabels[data.pattern] || data.pattern;
        document.getElementById("mission-overlap").textContent = data.overlap_pct + "%";

        /* Waypoints table */
        waypointsBody.innerHTML = "";
        data.waypoints.forEach(function (wp, idx) {
            var tr = document.createElement("tr");
            tr.style.borderBottom = "1px solid #222";
            tr.innerHTML =
                '<td style="padding:0.4rem 0.5rem;color:#ccc;font-size:0.85rem;">' + (idx + 1) + '</td>' +
                '<td style="padding:0.4rem 0.5rem;color:#ccc;font-size:0.85rem;font-family:monospace;">' + esc(wp[0].toFixed(6)) + '</td>' +
                '<td style="padding:0.4rem 0.5rem;color:#ccc;font-size:0.85rem;font-family:monospace;">' + esc(wp[1].toFixed(6)) + '</td>';
            waypointsBody.appendChild(tr);
        });
    }

    loadFarms();
})();
