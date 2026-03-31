/* Action timeline page — /acciones */
(function () {
    "use strict";

    var farmSel = document.getElementById("actions-farm-select");
    var fieldSel = document.getElementById("actions-field-select");
    var emptyEl = document.getElementById("actions-empty");
    var contentEl = document.getElementById("actions-content");
    var listEl = document.getElementById("actions-list");
    var weatherEl = document.getElementById("actions-weather");
    var weatherBody = document.getElementById("actions-weather-body");
    var dateEl = document.getElementById("actions-date");

    var statTotal = document.getElementById("actions-stat-total");
    var statPriority = document.getElementById("actions-stat-priority");
    var statWeather = document.getElementById("actions-stat-weather");

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

    function resetStats() {
        statTotal.textContent = "--";
        statPriority.textContent = "--";
        statWeather.textContent = "--";
        dateEl.textContent = "";
    }

    /* Priority badge color */
    function priorityClass(p) {
        if (p <= 1) return "badge-alta";
        if (p <= 2) return "badge-media";
        return "badge-baja";
    }

    function priorityLabel(p) {
        if (p <= 1) return "Alta";
        if (p <= 2) return "Media";
        return "Baja";
    }

    /* Action type icon */
    function actionTypeLabel(t) {
        var map = {
            "preparacion": "Preparacion",
            "siembra": "Siembra",
            "cosecha": "Cosecha",
            "mantenimiento": "Mantenimiento",
            "cuidado": "Cuidado",
            "tratamiento": "Tratamiento"
        };
        return map[t] || t;
    }

    function sourceLabel(s) {
        var map = {
            "seasonal_calendar": "Calendario TEK",
            "growth_stage": "Etapa de Crecimiento",
            "treatment": "Tratamiento Pendiente"
        };
        return map[s] || s;
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
    window.loadFieldsForActions = function () {
        fieldSel.innerHTML = '<option value="">Seleccione un campo...</option>';
        contentEl.style.display = "none";
        weatherEl.style.display = "none";
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

    /* Load action timeline for selected field */
    window.loadActionTimeline = function () {
        var farmId = farmSel.value;
        var fieldId = fieldSel.value;
        if (!farmId || !fieldId) {
            contentEl.style.display = "none";
            weatherEl.style.display = "none";
            emptyEl.style.display = "";
            resetStats();
            return;
        }
        emptyEl.style.display = "none";
        contentEl.style.display = "";

        var url = "/api/farms/" + farmId + "/fields/" + fieldId + "/action-timeline";
        fetchJSON(url).then(function (data) {
            if (!data) {
                listEl.innerHTML = '<p class="intel-subtitle">No se pudieron cargar las acciones.</p>';
                resetStats();
                return;
            }

            // Date
            dateEl.textContent = "Fecha de referencia: " + data.reference_date +
                (data.crop_type ? " | Cultivo: " + data.crop_type : "");

            // Stats
            statTotal.textContent = data.action_count;
            var highPriority = data.actions.filter(function (a) { return a.priority <= 1; });
            statPriority.textContent = highPriority.length;

            // Weather summary
            if (data.weather_summary) {
                weatherEl.style.display = "";
                var ws = data.weather_summary;
                statWeather.textContent = ws.total_rainfall_mm;
                weatherBody.innerHTML =
                    '<div style="display:flex; gap:2rem; flex-wrap:wrap;">' +
                    '<span>Lluvia total: <strong>' + ws.total_rainfall_mm + ' mm</strong></span>' +
                    '<span>Temp max: <strong>' + ws.max_temp_c + ' C</strong></span>' +
                    '<span>Temp min: <strong>' + ws.min_temp_c + ' C</strong></span>' +
                    '<span>Dias lluviosos: <strong>' + ws.rainy_days + '/' + ws.forecast_days + '</strong></span>' +
                    '</div>';
            } else {
                weatherEl.style.display = "none";
                statWeather.textContent = "--";
            }

            // Render action cards
            if (data.actions.length === 0) {
                listEl.innerHTML = '<p class="intel-subtitle">No hay acciones recomendadas para este periodo.</p>';
                return;
            }

            var html = "";
            data.actions.forEach(function (a) {
                var badgeClass = priorityClass(a.priority);
                html += '<div class="intel-card action-card">';
                html += '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">';
                html += '<span class="intel-badge ' + badgeClass + '">Prioridad: ' + esc(priorityLabel(a.priority)) + '</span>';
                html += '<span class="intel-badge badge-source">' + esc(actionTypeLabel(a.action_type)) + '</span>';
                html += '</div>';
                html += '<p style="font-size:0.85rem; opacity:0.7; margin-bottom:0.3rem;">' + esc(sourceLabel(a.source)) + '</p>';
                html += '<p style="margin-bottom:0.5rem;">' + esc(a.description) + '</p>';

                // Source-specific details
                if (a.source === "growth_stage" && a.stage_es) {
                    html += '<p style="font-size:0.85rem;">Etapa: <strong>' + esc(a.stage_es) + '</strong>';
                    if (a.days_in_stage !== null) html += ' (' + a.days_in_stage + ' dias)';
                    if (a.days_until_next_stage !== null) html += ' | Siguiente etapa en ' + a.days_until_next_stage + ' dias';
                    html += '</p>';
                    if (a.water_multiplier !== null) {
                        html += '<p style="font-size:0.85rem;">Multiplicador de riego: <strong>x' + a.water_multiplier + '</strong></p>';
                    }
                }

                if (a.source === "seasonal_calendar" && a.crop) {
                    html += '<p style="font-size:0.85rem;">Cultivo: <strong>' + esc(a.crop) + '</strong>';
                    if (a.month_range) html += ' | Periodo: ' + esc(a.month_range);
                    html += '</p>';
                }

                if (a.source === "treatment") {
                    if (a.problema) html += '<p style="font-size:0.85rem;">Problema: ' + esc(a.problema) + '</p>';
                    if (a.urgencia) html += '<p style="font-size:0.85rem;">Urgencia: <strong>' + esc(a.urgencia) + '</strong></p>';
                    if (a.costo_estimado_mxn) html += '<p style="font-size:0.85rem;">Costo estimado: $' + Number(a.costo_estimado_mxn).toLocaleString("es-MX") + ' MXN</p>';
                }

                if (a.weather_note) {
                    html += '<p style="font-size:0.85rem; color:#f0b429; margin-top:0.4rem;">' + esc(a.weather_note) + '</p>';
                }

                html += '</div>';
            });

            listEl.innerHTML = html;
        });
    };

    loadFarms();
})();
