/* thermal-dashboard.js — Thermal stress analysis with Chart.js trends */

(function () {
    'use strict';

    var farmSelect = document.getElementById('thermal-farm-select');
    var fieldSelect = document.getElementById('thermal-field-select');
    var emptyEl = document.getElementById('thermal-empty');
    var chartsSection = document.getElementById('thermal-charts-section');
    var tableContainer = document.getElementById('thermal-table');
    var tableBody = document.getElementById('thermal-table-body');
    var analysisCountEl = document.getElementById('thermal-analysis-count');
    var latestStressEl = document.getElementById('thermal-latest-stress');
    var latestTempEl = document.getElementById('thermal-latest-temp');
    var deficitCountEl = document.getElementById('thermal-deficit-count');

    var stressChart = null;
    var tempChart = null;
    var rangeChart = null;

    var chartDefaults = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#ccc' } } },
        scales: {
            x: { ticks: { color: '#aaa' }, grid: { color: 'rgba(255,255,255,0.06)' } },
            y: { ticks: { color: '#aaa' }, grid: { color: 'rgba(255,255,255,0.06)' } }
        }
    };

    async function fetchJSON(url) {
        try {
            var resp = await fetch(url);
            if (!resp.ok) return null;
            return await resp.json();
        } catch (e) {
            return null;
        }
    }

    function formatDate(iso) {
        if (!iso) return '--';
        var d = new Date(iso);
        return d.toLocaleDateString('es-MX', { year: 'numeric', month: 'short', day: 'numeric' });
    }

    function fmtNum(val, decimals) {
        if (val == null) return '--';
        return val.toFixed(decimals !== undefined ? decimals : 1);
    }

    function fmtInt(val) {
        if (val == null) return '--';
        return val.toLocaleString('es-MX');
    }

    // Load farms on startup
    async function loadFarms() {
        var data = await fetchJSON('/api/farms');
        if (!data) return;
        var farms = Array.isArray(data) ? data : (data.farms || []);
        farms.forEach(function (f) {
            var opt = document.createElement('option');
            opt.value = f.id;
            opt.textContent = f.name;
            farmSelect.appendChild(opt);
        });
        if (farms.length === 1) {
            farmSelect.value = farms[0].id;
            loadFieldsForThermal();
        }
    }

    window.loadFieldsForThermal = async function () {
        var farmId = farmSelect.value;
        fieldSelect.innerHTML = '<option value="">Seleccione un campo...</option>';
        resetView();
        if (!farmId) return;

        var data = await fetchJSON('/api/farms/' + farmId + '/fields');
        if (!data) return;
        var fields = Array.isArray(data) ? data : (data.fields || []);
        fields.forEach(function (f) {
            var opt = document.createElement('option');
            opt.value = f.id;
            opt.textContent = f.name + ' (' + (f.crop_type || '--') + ')';
            fieldSelect.appendChild(opt);
        });
        if (fields.length === 1) {
            fieldSelect.value = fields[0].id;
            loadThermalData();
        }
    };

    function resetView() {
        chartsSection.style.display = 'none';
        tableContainer.style.display = 'none';
        emptyEl.style.display = 'block';
        analysisCountEl.textContent = '--';
        latestStressEl.textContent = '--';
        latestTempEl.textContent = '--';
        deficitCountEl.textContent = '--';
    }

    window.loadThermalData = async function () {
        var farmId = farmSelect.value;
        var fieldId = fieldSelect.value;
        if (!farmId || !fieldId) {
            resetView();
            return;
        }

        emptyEl.style.display = 'none';

        var thermalData = await fetchJSON('/api/farms/' + farmId + '/fields/' + fieldId + '/thermal');
        if (!thermalData || thermalData.length === 0) {
            chartsSection.style.display = 'none';
            tableContainer.style.display = 'none';
            emptyEl.style.display = 'block';
            emptyEl.textContent = 'No hay datos termicos para este campo.';
            return;
        }

        // Sort by date ascending
        thermalData.sort(function (a, b) {
            return new Date(a.analyzed_at) - new Date(b.analyzed_at);
        });

        // Update stats
        analysisCountEl.textContent = thermalData.length;
        var latest = thermalData[thermalData.length - 1];
        latestStressEl.textContent = fmtNum(latest.stress_pct) + '%';
        latestTempEl.textContent = fmtNum(latest.temp_mean) + ' C';
        var deficits = thermalData.filter(function (t) { return t.irrigation_deficit; }).length;
        deficitCountEl.textContent = deficits + ' / ' + thermalData.length;

        // Render charts
        chartsSection.style.display = 'block';
        renderStressChart(thermalData);
        renderTempChart(thermalData);
        renderRangeChart(thermalData);

        // Render table
        tableContainer.style.display = 'block';
        renderTable(thermalData);
    };

    function getLabels(data) {
        return data.map(function (t) { return formatDate(t.analyzed_at); });
    }

    function renderStressChart(data) {
        var ctx = document.getElementById('thermal-stress-chart').getContext('2d');
        if (stressChart) stressChart.destroy();
        stressChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: getLabels(data),
                datasets: [{
                    label: 'Estres Termico %',
                    data: data.map(function (t) { return t.stress_pct; }),
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231,76,60,0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4
                }]
            },
            options: Object.assign({}, chartDefaults, {
                scales: Object.assign({}, chartDefaults.scales, {
                    y: Object.assign({}, chartDefaults.scales.y, { min: 0, max: 100 })
                })
            })
        });
    }

    function renderTempChart(data) {
        var ctx = document.getElementById('thermal-temp-chart').getContext('2d');
        if (tempChart) tempChart.destroy();
        tempChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: getLabels(data),
                datasets: [{
                    label: 'Temperatura Media (C)',
                    data: data.map(function (t) { return t.temp_mean; }),
                    borderColor: '#f0b429',
                    backgroundColor: 'rgba(240,180,41,0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4
                }]
            },
            options: chartDefaults
        });
    }

    function renderRangeChart(data) {
        var ctx = document.getElementById('thermal-range-chart').getContext('2d');
        if (rangeChart) rangeChart.destroy();
        rangeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: getLabels(data),
                datasets: [
                    {
                        label: 'Temp. Minima',
                        data: data.map(function (t) { return t.temp_min; }),
                        borderColor: '#4da6ff',
                        backgroundColor: 'rgba(77,166,255,0.08)',
                        tension: 0.3,
                        pointRadius: 4
                    },
                    {
                        label: 'Temp. Maxima',
                        data: data.map(function (t) { return t.temp_max; }),
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231,76,60,0.08)',
                        tension: 0.3,
                        pointRadius: 4
                    },
                    {
                        label: 'Temp. Media',
                        data: data.map(function (t) { return t.temp_mean; }),
                        borderColor: '#00c896',
                        backgroundColor: 'rgba(0,200,150,0.08)',
                        tension: 0.3,
                        pointRadius: 4,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: chartDefaults
        });
    }

    function renderTable(data) {
        var html = '';
        data.forEach(function (t) {
            var deficitLabel = t.irrigation_deficit ? 'Si' : 'No';
            var deficitClass = t.irrigation_deficit ? 'style="color:#e74c3c;font-weight:600;"' : '';
            html += '<tr>' +
                '<td>' + formatDate(t.analyzed_at) + '</td>' +
                '<td>' + fmtNum(t.temp_mean) + ' C</td>' +
                '<td>' + fmtNum(t.temp_min) + ' C</td>' +
                '<td>' + fmtNum(t.temp_max) + ' C</td>' +
                '<td>' + fmtNum(t.temp_std) + '</td>' +
                '<td>' + fmtNum(t.stress_pct) + '%</td>' +
                '<td>' + fmtInt(t.pixels_total) + '</td>' +
                '<td ' + deficitClass + '>' + deficitLabel + '</td>' +
            '</tr>';
        });
        tableBody.innerHTML = html;
    }

    // Init
    loadFarms();
    emptyEl.style.display = 'block';
})();
