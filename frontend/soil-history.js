/* soil-history.js — Soil analysis history with Chart.js trends */

(function () {
    'use strict';

    var farmSelect = document.getElementById('soil-farm-select');
    var fieldSelect = document.getElementById('soil-field-select');
    var emptyEl = document.getElementById('soil-empty');
    var chartsSection = document.getElementById('soil-charts-section');
    var tableContainer = document.getElementById('soil-table');
    var tableBody = document.getElementById('soil-table-body');
    var sampleCountEl = document.getElementById('soil-sample-count');
    var latestPhEl = document.getElementById('soil-latest-ph');
    var latestOmEl = document.getElementById('soil-latest-om');
    var latestNEl = document.getElementById('soil-latest-n');

    var phChart = null;
    var omChart = null;
    var npkChart = null;

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

    function esc(str) {
        var d = document.createElement('div');
        d.textContent = str || '';
        return d.innerHTML;
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
            loadFieldsForSoil();
        }
    }

    window.loadFieldsForSoil = async function () {
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
            loadSoilData();
        }
    };

    function resetView() {
        chartsSection.style.display = 'none';
        tableContainer.style.display = 'none';
        emptyEl.style.display = 'block';
        sampleCountEl.textContent = '--';
        latestPhEl.textContent = '--';
        latestOmEl.textContent = '--';
        latestNEl.textContent = '--';
    }

    window.loadSoilData = async function () {
        var farmId = farmSelect.value;
        var fieldId = fieldSelect.value;
        if (!farmId || !fieldId) {
            resetView();
            return;
        }

        emptyEl.style.display = 'none';

        var soilData = await fetchJSON('/api/farms/' + farmId + '/fields/' + fieldId + '/soil');
        if (!soilData || soilData.length === 0) {
            chartsSection.style.display = 'none';
            tableContainer.style.display = 'none';
            emptyEl.style.display = 'block';
            emptyEl.textContent = 'No hay datos de suelo para este campo.';
            return;
        }

        // Sort by date ascending
        soilData.sort(function (a, b) {
            return new Date(a.sampled_at) - new Date(b.sampled_at);
        });

        // Update stats
        sampleCountEl.textContent = soilData.length;
        var latest = soilData[soilData.length - 1];
        latestPhEl.textContent = fmtNum(latest.ph);
        latestOmEl.textContent = fmtNum(latest.organic_matter_pct);
        latestNEl.textContent = fmtNum(latest.nitrogen_ppm, 0);

        // Render charts
        chartsSection.style.display = 'block';
        renderPhChart(soilData);
        renderOmChart(soilData);
        renderNpkChart(soilData);

        // Render table
        tableContainer.style.display = 'block';
        renderTable(soilData);
    };

    function getLabels(data) {
        return data.map(function (s) { return formatDate(s.sampled_at); });
    }

    function renderPhChart(data) {
        var ctx = document.getElementById('soil-ph-chart').getContext('2d');
        if (phChart) phChart.destroy();
        phChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: getLabels(data),
                datasets: [{
                    label: 'pH',
                    data: data.map(function (s) { return s.ph; }),
                    borderColor: '#00c896',
                    backgroundColor: 'rgba(0,200,150,0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4
                }]
            },
            options: Object.assign({}, chartDefaults, {
                scales: Object.assign({}, chartDefaults.scales, {
                    y: Object.assign({}, chartDefaults.scales.y, { min: 4, max: 9 })
                })
            })
        });
    }

    function renderOmChart(data) {
        var ctx = document.getElementById('soil-om-chart').getContext('2d');
        if (omChart) omChart.destroy();
        omChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: getLabels(data),
                datasets: [{
                    label: 'Materia Organica %',
                    data: data.map(function (s) { return s.organic_matter_pct; }),
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

    function renderNpkChart(data) {
        var ctx = document.getElementById('soil-npk-chart').getContext('2d');
        if (npkChart) npkChart.destroy();
        npkChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: getLabels(data),
                datasets: [
                    {
                        label: 'Nitrogeno (N)',
                        data: data.map(function (s) { return s.nitrogen_ppm; }),
                        borderColor: '#4da6ff',
                        backgroundColor: 'rgba(77,166,255,0.08)',
                        tension: 0.3,
                        pointRadius: 4
                    },
                    {
                        label: 'Fosforo (P)',
                        data: data.map(function (s) { return s.phosphorus_ppm; }),
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231,76,60,0.08)',
                        tension: 0.3,
                        pointRadius: 4
                    },
                    {
                        label: 'Potasio (K)',
                        data: data.map(function (s) { return s.potassium_ppm; }),
                        borderColor: '#9b59b6',
                        backgroundColor: 'rgba(155,89,182,0.08)',
                        tension: 0.3,
                        pointRadius: 4
                    }
                ]
            },
            options: chartDefaults
        });
    }

    function renderTable(data) {
        var html = '';
        data.forEach(function (s) {
            html += '<tr>' +
                '<td>' + formatDate(s.sampled_at) + '</td>' +
                '<td>' + fmtNum(s.ph) + '</td>' +
                '<td>' + fmtNum(s.organic_matter_pct) + '</td>' +
                '<td>' + fmtNum(s.nitrogen_ppm, 0) + '</td>' +
                '<td>' + fmtNum(s.phosphorus_ppm, 0) + '</td>' +
                '<td>' + fmtNum(s.potassium_ppm, 0) + '</td>' +
                '<td>' + esc(s.texture) + '</td>' +
                '<td>' + fmtNum(s.moisture_pct) + '</td>' +
            '</tr>';
        });
        tableBody.innerHTML = html;
    }

    // Init
    loadFarms();
    emptyEl.style.display = 'block';
})();
