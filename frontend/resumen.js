/* ── cultivOS Executive Portfolio Summary — resumen.js ── */

let healthDistChart = null;
let savingsChart = null;
let roiChart = null;

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

function fmtMXN(n) {
    if (n == null) return '--';
    return '$' + n.toLocaleString('es-MX', { maximumFractionDigits: 0 });
}

function healthClass(score) {
    if (score == null) return 'none';
    if (score > 70) return 'good';
    if (score >= 40) return 'warning';
    return 'critical';
}

function healthColor(score) {
    if (score == null) return '#94a3b8';
    if (score > 70) return '#10b981';
    if (score >= 40) return '#f59e0b';
    return '#ef4444';
}

// ── Load all data ──
let portfolioData = [];

async function loadAll() {
    const [summary, economics, farms] = await Promise.all([
        fetchJSON('/api/intel/summary'),
        fetchJSON('/api/intel/economics'),
        fetchJSON('/api/farms?page_size=100'),
    ]);

    // KPIs
    if (summary) {
        document.getElementById('kpi-farms').textContent = summary.total_farms;
        document.getElementById('kpi-fields').textContent = summary.total_fields;
        document.getElementById('kpi-health').textContent =
            summary.avg_health != null ? Math.round(summary.avg_health) : '--';
    }

    if (economics) {
        document.getElementById('kpi-hectares').textContent =
            economics.total_hectares ? economics.total_hectares.toFixed(0) : '--';
        document.getElementById('kpi-savings').textContent = fmtMXN(economics.total_savings_mxn);

        // ROI = total savings / estimated technology cost (conservative: $15,000 MXN per hectare per year)
        const techCost = (economics.total_hectares || 1) * 2500;
        const roi = economics.total_savings_mxn > 0
            ? ((economics.total_savings_mxn / techCost) * 100).toFixed(0)
            : '--';
        document.getElementById('kpi-roi').textContent = roi !== '--' ? roi + '%' : '--';

        buildSavingsChart(economics);
        buildROIChart(economics);
    }

    // Farm table + health distribution
    if (farms && farms.farms && economics && economics.farms) {
        portfolioData = buildPortfolioTable(farms.farms, economics.farms);
        buildHealthDist(portfolioData);
        document.getElementById('resumen-farm-count').textContent = farms.farms.length;
    }
}

// ── Portfolio table ──
function buildPortfolioTable(farms, econFarms) {
    const tbody = document.getElementById('resumen-tbody');
    const econMap = {};
    (econFarms || []).forEach(e => { econMap[e.farm_id] = e; });

    const rows = farms.map(f => {
        const e = econMap[f.id] || {};
        return {
            name: f.name,
            municipality: f.municipality || f.state || '--',
            hectares: f.total_hectares || 0,
            health: e.hectares != null ? null : null, // Will be computed below
            savings: e.total_savings_mxn || 0,
            fields: 0, // Not directly available; use placeholder
            farm: f,
            econ: e,
        };
    });

    // We don't have per-farm health from the list endpoint, so show econ data
    tbody.innerHTML = farms.map(f => {
        const e = econMap[f.id] || {};
        return `<tr>
            <td style="font-weight:600; color:#e2e8f0;">${esc(f.name)}</td>
            <td>${esc(f.municipality || f.state || '--')}</td>
            <td>${(f.total_hectares || 0).toFixed(1)}</td>
            <td>--</td>
            <td style="color:#10b981;">${fmtMXN(e.total_savings_mxn || 0)}</td>
            <td>--</td>
        </tr>`;
    }).join('');

    // Async: load dashboard for each farm to get field count and health
    farms.forEach(async (f) => {
        const dash = await fetchJSON(`/api/farms/${f.id}/dashboard`);
        if (!dash) return;

        const row = tbody.querySelector(`tr:nth-child(${farms.indexOf(f) + 1})`);
        if (!row) return;

        const cells = row.querySelectorAll('td');
        const health = dash.overall_health;
        cells[3].innerHTML = health != null
            ? `<span style="color:${healthColor(health)}; font-weight:700;">${Math.round(health)}</span>`
            : '--';
        cells[5].textContent = dash.fields ? dash.fields.length : 0;
    });

    return rows;
}

// ── Health distribution doughnut ──
function buildHealthDist(rows) {
    // Use summary data to create categories
    // For now, fetch compare with all farm IDs
    const ctx = document.getElementById('resumen-health-dist').getContext('2d');
    if (healthDistChart) healthDistChart.destroy();

    // We'll build this from async dashboard calls
    // Start with placeholder and update
    healthDistChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Buena (>70)', 'Moderada (40-70)', 'Critica (<40)', 'Sin datos'],
            datasets: [{
                data: [0, 0, 0, rows.length],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#374151'],
                borderWidth: 0,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8', padding: 16 },
                },
            },
        },
    });

    // Load health for each farm async
    updateHealthDist();
}

async function updateHealthDist() {
    const farms = await fetchJSON('/api/farms?page_size=100');
    if (!farms || !farms.farms) return;

    let good = 0, moderate = 0, critical = 0, noData = 0;

    const promises = farms.farms.map(async f => {
        const dash = await fetchJSON(`/api/farms/${f.id}/dashboard`);
        if (!dash || dash.overall_health == null) {
            noData++;
        } else if (dash.overall_health > 70) {
            good++;
        } else if (dash.overall_health >= 40) {
            moderate++;
        } else {
            critical++;
        }
    });

    await Promise.all(promises);

    if (healthDistChart) {
        healthDistChart.data.datasets[0].data = [good, moderate, critical, noData];
        healthDistChart.update();
    }
}

// ── Savings breakdown chart ──
function buildSavingsChart(economics) {
    const ctx = document.getElementById('resumen-savings-chart').getContext('2d');
    if (savingsChart) savingsChart.destroy();

    savingsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Agua', 'Fertilizante', 'Rendimiento'],
            datasets: [{
                label: 'Ahorro (MXN)',
                data: [
                    economics.water_savings_mxn || 0,
                    economics.fertilizer_savings_mxn || 0,
                    economics.yield_improvement_mxn || 0,
                ],
                backgroundColor: ['#3b82f6', '#10b981', '#f59e0b'],
                borderRadius: 8,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8', callback: v => fmtMXN(v) }, grid: { color: 'rgba(255,255,255,0.05)' } },
            },
        },
    });
}

// ── ROI projection (3 years) ──
function buildROIChart(economics) {
    const ctx = document.getElementById('resumen-roi-chart').getContext('2d');
    if (roiChart) roiChart.destroy();

    const annualSavings = economics.total_savings_mxn || 0;
    const hectares = economics.total_hectares || 1;
    // Conservative tech cost: $2,500 MXN per hectare initial investment
    const initialInvestment = hectares * 2500;

    // Project 3 years with 15% annual growth in savings
    const years = ['Inversion Inicial', 'Ano 1', 'Ano 2', 'Ano 3'];
    const cumSavings = [-initialInvestment];
    let cumulative = -initialInvestment;
    for (let y = 1; y <= 3; y++) {
        cumulative += annualSavings * Math.pow(1.15, y - 1);
        cumSavings.push(Math.round(cumulative));
    }

    roiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                {
                    label: 'Retorno Acumulado (MXN)',
                    data: cumSavings,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16,185,129,0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 6,
                    pointBackgroundColor: cumSavings.map(v => v >= 0 ? '#10b981' : '#ef4444'),
                },
                {
                    label: 'Punto de equilibrio',
                    data: years.map(() => 0),
                    borderColor: '#94a3b8',
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#94a3b8' } },
            },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8', callback: v => fmtMXN(v) }, grid: { color: 'rgba(255,255,255,0.05)' } },
            },
        },
    });
}

// ── Export CSV ──
function exportPortfolio() {
    window.location.href = '/api/intel/export';
}

// ── Init ──
document.addEventListener('DOMContentLoaded', loadAll);
