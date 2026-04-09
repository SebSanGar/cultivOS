/* ejecutivo.js — Multi-farm executive dashboard */

const API = window.location.origin;
let activityChart = null;

function fetchJSON(url) {
    return fetch(url).then(r => r.ok ? r.json() : null);
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

/* ── Load on page init ────────────────────────────────────── */

(async function loadExecutiveDashboard() {
    const data = await fetchJSON(API + '/api/intel/executive-summary');
    if (!data || data.total_farms === 0) {
        document.getElementById('exec-empty').style.display = '';
        return;
    }

    document.getElementById('exec-empty').style.display = 'none';
    document.getElementById('exec-stats').style.display = '';
    document.getElementById('exec-chart-section').style.display = '';
    document.getElementById('exec-table-section').style.display = '';

    renderStats(data);
    renderActivityChart(data.activity_30d);
    renderFarmsTable(data.farms);
})();

/* ── Stats strip ──────────────────────────────────────────── */

function renderStats(data) {
    document.getElementById('exec-farms').textContent = data.total_farms;
    document.getElementById('exec-fields').textContent = data.total_fields;
    document.getElementById('exec-hectares').textContent = data.total_hectares.toLocaleString('es-MX');
    document.getElementById('exec-health').textContent =
        data.avg_health != null ? data.avg_health.toFixed(1) : '--';
    document.getElementById('exec-treatments').textContent = data.total_treatments;
    document.getElementById('exec-alerts').textContent = data.active_alerts;
    document.getElementById('exec-co2e').textContent = data.total_co2e_tonnes.toLocaleString('es-MX', { maximumFractionDigits: 1 });
}

/* ── Activity chart (30 days) ─────────────────────────────── */

function renderActivityChart(activity) {
    const ctx = document.getElementById('activity-chart');
    if (!ctx) return;

    const labels = activity.map(a => a.date.slice(5));
    const values = activity.map(a => a.count);

    if (activityChart) activityChart.destroy();
    activityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Actividad diaria',
                data: values,
                backgroundColor: 'rgba(34, 197, 94, 0.6)',
                borderColor: 'rgba(34, 197, 94, 1)',
                borderWidth: 1,
                borderRadius: 3,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1, color: '#94a3b8' },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                },
                x: {
                    ticks: { color: '#94a3b8', maxRotation: 45 },
                    grid: { display: false },
                },
            },
        },
    });
}

/* ── Farms table ──────────────────────────────────────────── */

function renderFarmsTable(farms) {
    const tbody = document.getElementById('farms-table-body');
    if (!tbody) return;

    tbody.innerHTML = farms.map(f => {
        const healthColor = f.avg_health == null ? '#94a3b8'
            : f.avg_health >= 70 ? '#22c55e'
            : f.avg_health >= 50 ? '#eab308'
            : '#ef4444';
        return `<tr style="border-bottom:1px solid var(--border-color);">
            <td style="padding:0.6rem 0.8rem;font-weight:500;">${esc(f.farm_name)}</td>
            <td style="padding:0.6rem 0.8rem;color:var(--text-secondary);">${esc(f.state)}</td>
            <td style="padding:0.6rem 0.8rem;text-align:right;">${f.field_count}</td>
            <td style="padding:0.6rem 0.8rem;text-align:right;">${f.hectares.toLocaleString('es-MX')}</td>
            <td style="padding:0.6rem 0.8rem;text-align:right;color:${healthColor};font-weight:600;">
                ${f.avg_health != null ? f.avg_health.toFixed(1) : '--'}
            </td>
            <td style="padding:0.6rem 0.8rem;text-align:right;">${f.treatment_count}</td>
        </tr>`;
    }).join('');
}
