/* Portfolio report generation page — /reportes */

(function () {
    'use strict';

    async function fetchJSON(url) {
        try {
            const resp = await fetch(url);
            if (!resp.ok) return null;
            return await resp.json();
        } catch { return null; }
    }

    async function loadFarms() {
        const data = await fetchJSON('/api/farms');
        const select = document.getElementById('reportes-farm-select');
        if (!data || data.length === 0) {
            select.innerHTML = '<option value="">Sin granjas disponibles</option>';
            document.getElementById('reportes-empty').style.display = '';
            return;
        }

        select.innerHTML = '';
        let totalHa = 0;
        let totalFields = 0;
        data.forEach(function (farm) {
            const opt = document.createElement('option');
            opt.value = farm.id;
            opt.textContent = farm.name + ' (' + (farm.total_hectares || 0) + ' ha)';
            opt.selected = true;
            select.appendChild(opt);
            totalHa += farm.total_hectares || 0;
            totalFields += farm.field_count || 0;
        });

        document.getElementById('reportes-stat-farms').textContent = data.length;
        document.getElementById('reportes-stat-hectares').textContent = Math.round(totalHa);
        document.getElementById('reportes-stat-fields').textContent = totalFields;

        // Default date range: last 90 days
        var today = new Date();
        var start = new Date(today);
        start.setDate(start.getDate() - 90);
        document.getElementById('reportes-date-end').value = today.toISOString().split('T')[0];
        document.getElementById('reportes-date-start').value = start.toISOString().split('T')[0];
    }

    window.generateReport = async function () {
        var btn = document.getElementById('reportes-generate-btn');
        var downloadSection = document.getElementById('reportes-download');
        var statusEl = document.getElementById('reportes-download-status');

        btn.disabled = true;
        btn.textContent = 'Generando...';
        downloadSection.style.display = 'none';

        try {
            var resp = await fetch('/api/reports/portfolio', { method: 'POST' });
            if (!resp.ok) {
                statusEl.textContent = 'Error al generar el reporte. Intenta de nuevo.';
                downloadSection.style.display = '';
                return;
            }

            var blob = await resp.blob();
            var url = URL.createObjectURL(blob);
            var link = document.getElementById('reportes-download-link');
            link.href = url;
            statusEl.textContent = 'Tu reporte esta listo para descargar.';
            downloadSection.style.display = '';
        } catch (err) {
            statusEl.textContent = 'Error de conexion. Verifica tu red e intenta de nuevo.';
            downloadSection.style.display = '';
        } finally {
            btn.disabled = false;
            btn.textContent = 'Generar Reporte PDF';
        }
    };

    loadFarms();
})();
