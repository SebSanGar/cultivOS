/* ── cultivOS Farm Comparison — comparar.js ── */

let healthChart = null;
let yieldChart = null;
let historyChart = null;

const COLORS = ['#3b82f6', '#10b981', '#f59e0b'];

// ── Helpers ──
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

async function fetchJSON(path) {
    try {
        const token = localStorage.getItem('cultivOS_token');
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const resp = await fetch(path, { headers });
        if (!resp.ok) return null;
        return await resp.json();
    } catch {
        return null;
    }
}

const TREND_MAP = {
    improving: 'Mejorando',
    stable: 'Estable',
    declining: 'Declinando',
};

function trendBadge(trend) {
    if (!trend) return '<span style="color:#94a3b8;">--</span>';
    const colors = { improving: '#10b981', stable: '#f59e0b', declining: '#ef4444' };
    const c = colors[trend] || '#94a3b8';
    return `<span style="color:${c}; font-weight:600;">${esc(TREND_MAP[trend] || trend)}</span>`;
}

// ── Load farms ──
async function loadFarms() {
    const data = await fetchJSON('/api/farms?page_size=100');
    if (!data || !data.farms) return;

    ['comp-farm-1', 'comp-farm-2', 'comp-farm-3'].forEach(id => {
        const sel = document.getElementById(id);
        data.farms.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.id;
            opt.textContent = f.name;
            sel.appendChild(opt);
        });
    });

    // Pre-select first two if available
    if (data.farms.length >= 2) {
        document.getElementById('comp-farm-1').value = data.farms[0].id;
        document.getElementById('comp-farm-2').value = data.farms[1].id;
    }
}

// ── Run comparison ──
async function runComparison() {
    const ids = [];
    for (let i = 1; i <= 3; i++) {
        const v = document.getElementById(`comp-farm-${i}`).value;
        if (v) ids.push(v);
    }

    if (ids.length < 2) {
        alert('Seleccione al menos 2 granjas para comparar.');
        return;
    }

    const btn = document.getElementById('comp-btn');
    btn.disabled = true;
    btn.textContent = 'Cargando...';

    const data = await fetchJSON(`/api/intel/compare?farm_ids=${ids.join(',')}`);

    btn.disabled = false;
    btn.textContent = 'Comparar';

    if (!data || !data.farms || data.farms.length === 0) {
        document.getElementById('comp-results').style.display = 'none';
        document.getElementById('comp-empty').style.display = 'block';
        return;
    }

    document.getElementById('comp-results').style.display = 'block';
    document.getElementById('comp-empty').style.display = 'none';

    buildTable(data.farms);
    buildHealthChart(data.farms);
    buildYieldChart(data.farms);
    buildHistoryChart(data.farms);
}

// ── Comparison table ──
function buildTable(farms) {
    const table = document.getElementById('comp-table');
    const thead = table.querySelector('thead tr');
    const tbody = table.querySelector('tbody');

    // Build header
    thead.innerHTML = '<th style="color:#94a3b8;">Metrica</th>' +
        farms.map((f, i) => `<th style="color:${COLORS[i]};">${esc(f.farm_name)}</th>`).join('');

    // Build rows
    const metrics = [
        { label: 'Campos', key: f => f.field_count },
        { label: 'Hectareas', key: f => f.total_hectares.toFixed(1) },
        { label: 'Salud Promedio', key: f => f.avg_health != null ? f.avg_health.toFixed(1) : '--' },
        { label: 'Tendencia', key: f => trendBadge(f.trend), html: true },
        { label: 'Rendimiento (kg)', key: f => f.yield_total_kg.toLocaleString('es-MX', { maximumFractionDigits: 0 }) },
        { label: 'Tratamientos', key: f => f.treatment_count },
    ];

    tbody.innerHTML = metrics.map(m => {
        const cells = farms.map(f => {
            const val = m.key(f);
            return `<td>${m.html ? val : esc(String(val))}</td>`;
        }).join('');
        return `<tr><td style="font-weight:600; color:#e2e8f0;">${m.label}</td>${cells}</tr>`;
    }).join('');
}

// ── Health bar chart ──
function buildHealthChart(farms) {
    const ctx = document.getElementById('comp-health-chart').getContext('2d');
    if (healthChart) healthChart.destroy();

    healthChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: farms.map(f => f.farm_name),
            datasets: [{
                label: 'Salud Promedio',
                data: farms.map(f => f.avg_health || 0),
                backgroundColor: farms.map((_, i) => COLORS[i]),
                borderRadius: 8,
            }],
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: { max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            },
        },
    });
}

// ── Yield bar chart ──
function buildYieldChart(farms) {
    const ctx = document.getElementById('comp-yield-chart').getContext('2d');
    if (yieldChart) yieldChart.destroy();

    yieldChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: farms.map(f => f.farm_name),
            datasets: [{
                label: 'Rendimiento Total (kg)',
                data: farms.map(f => f.yield_total_kg),
                backgroundColor: farms.map((_, i) => COLORS[i]),
                borderRadius: 8,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            },
        },
    });
}

// ── Health history line chart ──
function buildHistoryChart(farms) {
    const ctx = document.getElementById('comp-history-chart').getContext('2d');
    if (historyChart) historyChart.destroy();

    // Find the longest health_history
    const maxLen = Math.max(...farms.map(f => (f.health_history || []).length));
    const labels = Array.from({ length: maxLen }, (_, i) => `#${i + 1}`);

    const datasets = farms.map((f, i) => ({
        label: f.farm_name,
        data: f.health_history || [],
        borderColor: COLORS[i],
        backgroundColor: COLORS[i] + '22',
        fill: false,
        tension: 0.3,
        pointRadius: 3,
    }));

    historyChart = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#94a3b8' } } },
            scales: {
                x: { title: { display: true, text: 'Medicion', color: '#94a3b8' }, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { title: { display: true, text: 'Salud', color: '#94a3b8' }, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            },
        },
    });
}

// ── Init ──
document.addEventListener('DOMContentLoaded', loadFarms);
