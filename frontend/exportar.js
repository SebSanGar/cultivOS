(function () {
    'use strict';

    async function fetchJSON(url) {
        try {
            const resp = await fetch(url);
            if (!resp.ok) return null;
            return await resp.json();
        } catch { return null; }
    }

    async function init() {
        const farms = await fetchJSON('/api/farms');
        if (!farms || farms.length === 0) {
            var empty = document.getElementById('exportar-empty');
            if (empty) empty.style.display = 'block';
            return;
        }

        // Stats
        var totalHa = 0;
        var totalFields = 0;
        farms.forEach(function (f) {
            totalHa += f.total_hectares || 0;
            totalFields += f.field_count || 0;
        });
        var statFarms = document.getElementById('exportar-stat-farms');
        if (statFarms) statFarms.textContent = farms.length;
        var statHa = document.getElementById('exportar-stat-hectares');
        if (statHa) statHa.textContent = totalHa.toFixed(0);
        var statFields = document.getElementById('exportar-stat-fields');
        if (statFields) statFields.textContent = totalFields;

        // Populate farm selector
        var sel = document.getElementById('exportar-farm-select');
        if (sel) {
            sel.innerHTML = '<option value="">-- Seleccionar granja --</option>';
            farms.forEach(function (f) {
                var opt = document.createElement('option');
                opt.value = f.id;
                opt.textContent = f.name + ' (' + (f.total_hectares || 0) + ' ha)';
                sel.appendChild(opt);
            });
        }

        // Default dates (last 90 days)
        var now = new Date();
        var start = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        var dateStart = document.getElementById('exportar-date-start');
        var dateEnd = document.getElementById('exportar-date-end');
        if (dateStart) dateStart.value = start.toISOString().split('T')[0];
        if (dateEnd) dateEnd.value = now.toISOString().split('T')[0];
    }

    window.downloadExport = async function () {
        var farmSel = document.getElementById('exportar-farm-select');
        var categorySel = document.getElementById('exportar-category-select');
        var formatSel = document.getElementById('exportar-format-select');
        var btn = document.getElementById('exportar-download-btn');
        var statusDiv = document.getElementById('exportar-status');
        var statusText = document.getElementById('exportar-status-text');

        var farmId = farmSel ? farmSel.value : '';
        var category = categorySel ? categorySel.value : 'salud';
        var format = formatSel ? formatSel.value : 'csv';

        if (!farmId) {
            if (statusDiv) statusDiv.style.display = 'block';
            if (statusText) statusText.textContent = 'Selecciona una granja primero.';
            return;
        }

        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Generando...';
        }

        try {
            var url = '';
            var filename = '';

            if (category === 'inteligencia') {
                url = '/api/intel/export';
                filename = 'cultivOS_intel_export.csv';
            } else if (format === 'pdf') {
                url = '/api/farms/' + farmId + '/report';
                filename = 'reporte_granja.pdf';
            } else {
                url = '/api/farms/' + farmId + '/export?format=csv';
                filename = 'export_granja.csv';
            }

            var resp;
            if (format === 'pdf' && category !== 'inteligencia') {
                resp = await fetch(url, { method: 'POST' });
            } else {
                resp = await fetch(url);
            }

            if (!resp.ok) {
                throw new Error('Error ' + resp.status);
            }

            var blob = await resp.blob();
            var link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);

            if (statusDiv) statusDiv.style.display = 'block';
            if (statusText) statusText.textContent = 'Descarga completada.';
        } catch (err) {
            if (statusDiv) statusDiv.style.display = 'block';
            if (statusText) statusText.textContent = 'Error al exportar: ' + err.message;
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Descargar';
            }
        }
    };

    document.addEventListener('DOMContentLoaded', init);
})();
