/* Calendario Fenologico — Gantt-like crop phenology timeline */
/* global fetchJSON */

(function () {
    'use strict';

    function fetchJSON(url) {
        return fetch(url).then(function (r) { return r.ok ? r.json() : null; });
    }

    // ---- Load all crops phenology on page load ----
    loadAllCrops();
    loadFarmsForCalendario();

    function loadAllCrops() {
        fetchJSON('/api/phenology/calendar').then(function (data) {
            if (!data || !data.crops || !data.crops.length) {
                document.getElementById('cal-empty').style.display = 'block';
                document.getElementById('cal-content').style.display = 'none';
                return;
            }
            document.getElementById('cal-empty').style.display = 'none';
            document.getElementById('cal-content').style.display = 'block';

            var crops = data.crops;
            var maxDays = Math.max.apply(null, crops.map(function (c) { return c.total_days; }));

            document.getElementById('cal-crop-count').textContent = crops.length;
            document.getElementById('cal-total-days').textContent = maxDays + 'd';

            var container = document.getElementById('cal-all-crops');
            container.innerHTML = '';

            crops.forEach(function (crop) {
                var row = document.createElement('div');
                row.className = 'cal-timeline-row';

                var label = document.createElement('div');
                label.className = 'cal-crop-label';
                label.textContent = crop.crop_type;
                row.appendChild(label);

                var track = document.createElement('div');
                track.className = 'cal-bar-track';

                crop.stages.forEach(function (stage) {
                    var seg = document.createElement('div');
                    seg.className = 'cal-bar-segment cal-stage-' + stage.name;
                    var pct = ((stage.end_day - stage.start_day) / maxDays) * 100;
                    seg.style.width = pct + '%';
                    seg.title = stage.name_es + ' (dia ' + stage.start_day + '-' + stage.end_day + ')';
                    if (pct > 8) {
                        seg.textContent = stage.name_es;
                    }
                    track.appendChild(seg);
                });

                row.appendChild(track);
                container.appendChild(row);
            });

            // Day axis
            var axis = document.getElementById('cal-day-axis');
            axis.innerHTML = '';
            var ticks = [0, Math.round(maxDays * 0.25), Math.round(maxDays * 0.5), Math.round(maxDays * 0.75), maxDays];
            ticks.forEach(function (d) {
                var span = document.createElement('span');
                span.textContent = d + 'd';
                axis.appendChild(span);
            });

            // Also populate timeline container for test selector
            document.getElementById('cal-timeline').innerHTML = container.innerHTML;
        });
    }

    // ---- Farm/field selectors ----
    function loadFarmsForCalendario() {
        fetchJSON('/api/farms').then(function (data) {
            if (!data) return;
            var farms = Array.isArray(data) ? data : (data.farms || []);
            var sel = document.getElementById('cal-farm-select');
            farms.forEach(function (f) {
                var opt = document.createElement('option');
                opt.value = f.id;
                opt.textContent = f.name;
                sel.appendChild(opt);
            });
        });
    }

    window.loadFieldsForCalendario = function () {
        var farmId = document.getElementById('cal-farm-select').value;
        var fieldSel = document.getElementById('cal-field-select');
        fieldSel.innerHTML = '<option value="">Seleccione un campo...</option>';
        document.getElementById('cal-field-detail').style.display = 'none';
        document.getElementById('cal-field-stage').textContent = '--';
        if (!farmId) return;

        fetchJSON('/api/farms/' + farmId + '/fields').then(function (data) {
            if (!data) return;
            var fields = Array.isArray(data) ? data : (data.fields || []);
            fields.forEach(function (f) {
                var opt = document.createElement('option');
                opt.value = f.id;
                opt.textContent = f.name + (f.crop_type ? ' (' + f.crop_type + ')' : '');
                fieldSel.appendChild(opt);
            });
        });
    };

    window.loadFieldGrowthStage = function () {
        var farmId = document.getElementById('cal-farm-select').value;
        var fieldId = document.getElementById('cal-field-select').value;
        if (!farmId || !fieldId) {
            document.getElementById('cal-field-detail').style.display = 'none';
            document.getElementById('cal-field-stage').textContent = '--';
            return;
        }

        fetchJSON('/api/farms/' + farmId + '/fields/' + fieldId + '/growth-stage').then(function (data) {
            if (!data) {
                document.getElementById('cal-field-detail').style.display = 'none';
                document.getElementById('cal-field-stage').textContent = 'Sin datos';
                return;
            }
            document.getElementById('cal-field-detail').style.display = 'block';
            document.getElementById('cal-field-stage').textContent = data.stage_es;

            var info = document.getElementById('cal-field-info');
            info.innerHTML =
                '<p><strong>Cultivo:</strong> ' + data.crop_type + '</p>' +
                '<p><strong>Etapa actual:</strong> <span class="cal-field-stage cal-stage-' + data.stage + '">' + data.stage_es + '</span></p>' +
                '<p><strong>Dias desde siembra:</strong> ' + data.days_since_planting + '</p>' +
                '<p><strong>Dias en etapa:</strong> ' + data.days_in_stage + '</p>' +
                (data.days_until_next_stage !== null
                    ? '<p><strong>Dias para siguiente etapa:</strong> ' + data.days_until_next_stage + '</p>'
                    : '') +
                '<p><strong>Multiplicador de riego:</strong> x' + data.water_multiplier + '</p>' +
                '<p><strong>Enfoque nutricional:</strong> ' + data.nutrient_focus + '</p>';
        });
    };
})();
