/* ── cultivOS Intelligence Dashboard — intel.js ── */

const API = '/api/intel';

// ── Helpers ──
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function healthClass(score) {
    if (score == null) return 'none';
    if (score > 70) return 'good';
    if (score >= 40) return 'warning';
    return 'critical';
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

// ── Summary ──
async function loadSummary() {
    const data = await fetchJSON(API + '/summary');
    if (!data) return;

    document.getElementById('intel-total-farms').textContent = data.total_farms;
    document.getElementById('intel-total-fields').textContent = data.total_fields;
    document.getElementById('intel-avg-health').textContent =
        data.avg_health != null ? Math.round(data.avg_health) : '--';

    if (data.worst_field) {
        const el = document.getElementById('intel-worst-field');
        el.textContent = esc(data.worst_field.field_name);
        el.title = esc(data.worst_field.farm_name) + ' — Salud: ' + Math.round(data.worst_field.score);
    }
}

// ── Anomalies ──
async function loadAnomalies() {
    const container = document.getElementById('intel-anomalies');
    const data = await fetchJSON(API + '/anomalies');

    if (!data || data.anomalies.length === 0) {
        container.innerHTML = '<div class="intel-empty">Sin anomalias detectadas</div>';
        document.getElementById('intel-anomaly-count').textContent = '0';
        return;
    }

    document.getElementById('intel-anomaly-count').textContent = data.anomalies.length;

    container.innerHTML = data.anomalies.map(a => {
        const cls = healthClass(a.latest_score);
        return `
        <div class="intel-anomaly-card">
            <div class="intel-anomaly-header">
                <span class="intel-anomaly-field">${esc(a.field_name)}</span>
                <span class="health-badge ${cls}">${Math.round(a.latest_score)}</span>
            </div>
            <div class="intel-anomaly-farm">${esc(a.farm_name)}</div>
            <div class="intel-anomaly-detail">
                ${a.consecutive_declines} caidas consecutivas
            </div>
            <div class="intel-anomaly-history">
                ${a.score_history.map(s => `<span class="intel-spark ${healthClass(s)}">${Math.round(s)}</span>`).join(' ')}
            </div>
        </div>`;
    }).join('');
}

// ── Soil Trends (Chart.js) ──
async function loadSoilTrends() {
    const data = await fetchJSON(API + '/soil-trends');
    const canvas = document.getElementById('intel-soil-chart');
    const fallback = document.getElementById('intel-soil-fallback');

    if (!data || data.trends.length === 0) {
        canvas.style.display = 'none';
        fallback.style.display = 'block';
        return;
    }

    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        canvas.style.display = 'none';
        fallback.style.display = 'block';
        fallback.textContent = 'Cargando Chart.js...';
        return;
    }

    const labels = data.trends.map(t => t.date);
    const phData = data.trends.map(t => t.avg_ph);
    const omData = data.trends.map(t => t.avg_organic_matter);

    new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'pH Promedio',
                    data: phData,
                    borderColor: '#16a34a',
                    backgroundColor: 'rgba(22,163,74,0.1)',
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y',
                },
                {
                    label: 'Materia Organica %',
                    data: omData,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37,99,235,0.1)',
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y1',
                },
            ],
        },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { labels: { color: '#e5e7eb' } },
            },
            scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.06)' } },
                y: {
                    position: 'left',
                    title: { display: true, text: 'pH', color: '#16a34a' },
                    ticks: { color: '#16a34a' },
                    grid: { color: 'rgba(255,255,255,0.06)' },
                },
                y1: {
                    position: 'right',
                    title: { display: true, text: 'Materia Organica %', color: '#2563eb' },
                    ticks: { color: '#2563eb' },
                    grid: { drawOnChartArea: false },
                },
            },
        },
    });
}

// ── Treatment Effectiveness ──
async function loadTreatments() {
    const container = document.getElementById('intel-treatments');
    const data = await fetchJSON(API + '/treatments');

    if (!data || data.treatments.length === 0) {
        container.innerHTML = '<div class="intel-empty">Sin datos de tratamientos</div>';
        return;
    }

    container.innerHTML = data.treatments.map(t => {
        const delta = t.delta != null ? (t.delta >= 0 ? '+' : '') + t.delta.toFixed(1) : '--';
        const deltaCls = t.delta != null ? (t.delta > 0 ? 'positive' : t.delta < 0 ? 'negative' : '') : '';
        return `
        <div class="intel-treatment-card">
            <div class="intel-treatment-header">
                <span class="intel-treatment-name">${esc(t.tratamiento)}</span>
                <span class="intel-treatment-delta ${deltaCls}">${delta}</span>
            </div>
            <div class="intel-treatment-field">${esc(t.field_name)} — ${esc(t.farm_name)}</div>
            <div class="intel-treatment-scores">
                <span>Antes: ${Math.round(t.health_before)}</span>
                ${t.health_after != null ? `<span>Despues: ${Math.round(t.health_after)}</span>` : '<span>Pendiente</span>'}
            </div>
            <div class="intel-treatment-urgency urgency-${t.urgencia.toLowerCase().replace(' ', '-')}">${esc(t.urgencia)}</div>
        </div>`;
    }).join('');
}

// ── Role-based UI ──
function applyRoleVisibility() {
    const token = localStorage.getItem('cultivOS_token');
    if (!token) return; // No auth — show everything by default

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.role === 'researcher') {
            document.querySelectorAll('.admin-only').forEach(el => {
                el.style.display = 'none';
            });
        }
    } catch {
        // Invalid token — keep defaults
    }
}

// ── Init ──
async function init() {
    applyRoleVisibility();
    await Promise.all([
        loadSummary(),
        loadAnomalies(),
        loadSoilTrends(),
        loadTreatments(),
    ]);
}

init();
