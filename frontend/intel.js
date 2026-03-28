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

// ── Treatment Effectiveness Report ──
async function loadTreatmentReport() {
    const container = document.getElementById('intel-treatment-report');
    const filter = document.getElementById('treatment-crop-filter');
    const crop_type = filter ? filter.value : '';
    const qs = crop_type ? '?crop_type=' + encodeURIComponent(crop_type) : '';
    const data = await fetchJSON(API + '/treatment-effectiveness-report' + qs);

    if (!data || data.treatments.length === 0) {
        container.innerHTML = '<div class="intel-empty">Sin datos de tratamientos</div>';
        return;
    }

    container.innerHTML = data.treatments.map(t => {
        const scoreWidth = Math.min(Math.round(t.composite_score), 100);
        const scoreCls = scoreWidth > 60 ? 'good' : scoreWidth >= 30 ? 'warning' : 'critical';

        const successRate = t.feedback_success_rate != null
            ? Math.round(t.feedback_success_rate) + '%'
            : '--';

        const delta = t.avg_health_delta != null
            ? (t.avg_health_delta >= 0 ? '+' : '') + t.avg_health_delta.toFixed(1)
            : '--';
        const deltaCls = t.avg_health_delta != null
            ? (t.avg_health_delta > 0 ? 'positive' : t.avg_health_delta < 0 ? 'negative' : '')
            : '';

        return `
        <div class="treatment-report-card">
            <div class="treatment-report-header">
                <span class="treatment-report-name">${esc(t.tratamiento)}</span>
                <span class="treatment-report-apps">${t.total_applications} aplicaciones</span>
            </div>
            <div class="treatment-report-score-row">
                <span class="treatment-report-label">Puntaje</span>
                <div class="treatment-report-score-bar">
                    <div class="score-bar-fill ${scoreCls}" style="width:${scoreWidth}%"></div>
                </div>
                <span class="treatment-report-score-val">${t.composite_score.toFixed(1)}</span>
            </div>
            <div class="treatment-report-metrics">
                <div class="treatment-report-metric">
                    <span class="treatment-report-metric-label">Tasa de exito</span>
                    <span class="treatment-report-metric-value">${successRate}</span>
                </div>
                <div class="treatment-report-metric">
                    <span class="treatment-report-metric-label">Delta salud</span>
                    <span class="treatment-report-metric-value ${deltaCls}">${delta}</span>
                </div>
                <div class="treatment-report-metric">
                    <span class="treatment-report-metric-label">Feedback</span>
                    <span class="treatment-report-metric-value">${t.feedback_count}</span>
                </div>
            </div>
        </div>`;
    }).join('');
}

// ── Economic Impact ──
async function loadEconomics() {
    const container = document.getElementById('intel-economics');
    const data = await fetchJSON(API + '/economics');

    if (!data || data.total_farms === 0) {
        container.innerHTML = '<div class="intel-empty">Sin datos economicos</div>';
        return;
    }

    const fmt = (n) => '$' + Number(n).toLocaleString('es-MX') + ' MXN';

    container.innerHTML = `
        <div class="economics-summary">
            <div class="economics-total">
                <span class="economics-total-label">Ahorro Total Estimado</span>
                <span class="economics-total-value">${fmt(data.total_savings_mxn)}</span>
            </div>
            <div class="economics-meta">
                ${data.total_farms} granjas — ${data.total_hectares} ha
            </div>
            <div class="economics-breakdown">
                <div class="economics-row">
                    <span class="economics-row-label">Agua</span>
                    <div class="economics-row-bar">
                        <div class="score-bar-fill good" style="width:${Math.min(100, Math.round(data.water_savings_mxn / data.total_savings_mxn * 100))}%"></div>
                    </div>
                    <span class="economics-row-value">${fmt(data.water_savings_mxn)}</span>
                </div>
                <div class="economics-row">
                    <span class="economics-row-label">Fertilizante</span>
                    <div class="economics-row-bar">
                        <div class="score-bar-fill good" style="width:${Math.min(100, Math.round(data.fertilizer_savings_mxn / data.total_savings_mxn * 100))}%"></div>
                    </div>
                    <span class="economics-row-value">${fmt(data.fertilizer_savings_mxn)}</span>
                </div>
                <div class="economics-row">
                    <span class="economics-row-label">Rendimiento</span>
                    <div class="economics-row-bar">
                        <div class="score-bar-fill good" style="width:${Math.min(100, Math.round(data.yield_improvement_mxn / data.total_savings_mxn * 100))}%"></div>
                    </div>
                    <span class="economics-row-value">${fmt(data.yield_improvement_mxn)}</span>
                </div>
            </div>
        </div>
        ${data.farms.length > 0 ? `
        <div class="economics-farms">
            ${data.farms.map(f => `
                <div class="economics-farm-row">
                    <span class="economics-farm-name">${esc(f.farm_name)}</span>
                    <span class="economics-farm-ha">${f.hectares} ha</span>
                    <span class="economics-farm-savings">${fmt(f.total_savings_mxn)}</span>
                </div>
            `).join('')}
        </div>` : ''}
    `;
}

async function loadCropTypeOptions() {
    const filter = document.getElementById('treatment-crop-filter');
    if (!filter) return;
    const fields = await fetchJSON('/api/fields');
    if (!fields) return;
    const types = [...new Set(
        (Array.isArray(fields) ? fields : (fields.data || []))
            .map(f => f.crop_type)
            .filter(Boolean)
    )].sort();
    types.forEach(ct => {
        const opt = document.createElement('option');
        opt.value = ct;
        opt.textContent = ct.charAt(0).toUpperCase() + ct.slice(1);
        filter.appendChild(opt);
    });
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
        loadEconomics(),
        loadCropTypeOptions().then(() => loadTreatmentReport()),
    ]);
}

init();
