/* Cerebro IA Analytics — AI decision log and trends */

const API = window.location.origin;
let dailyChart = null;

function fetchJSON(url) {
    return fetch(url).then(r => r.ok ? r.json() : null);
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

/* ── Load analytics on page load ─────────────────────────────── */

(async function loadCerebroAnalytics() {
    const data = await fetchJSON(API + '/api/intel/cerebro-analytics');
    if (!data || data.total_decisions === 0) {
        document.getElementById('cerebro-empty').style.display = '';
        document.getElementById('cerebro-content').style.display = 'none';
        return;
    }

    document.getElementById('cerebro-empty').style.display = 'none';
    document.getElementById('cerebro-content').style.display = '';

    renderStats(data);
    renderDailyChart(data.decisions_per_day);
    renderDecisionsByType(data.decisions_by_type);
    renderAccuracy(data.accuracy, data.feedback_collected);
})();

/* ── Stats strip ─────────────────────────────────────────────── */

function renderStats(data) {
    document.getElementById('cerebro-stat-total').textContent = data.total_decisions.toLocaleString();
    document.getElementById('cerebro-stat-recommendations').textContent = data.decisions_by_type.treatment_recommendations.toLocaleString();
    const analyses = data.decisions_by_type.ndvi_analyses + data.decisions_by_type.thermal_analyses;
    document.getElementById('cerebro-stat-analyses').textContent = analyses.toLocaleString();
    document.getElementById('cerebro-stat-farms').textContent = data.farms_covered.toLocaleString();
    document.getElementById('cerebro-stat-accuracy').textContent = data.accuracy.feedback_positive_rate.toFixed(1) + '%';
}

/* ── Daily decisions chart ───────────────────────────────────── */

function renderDailyChart(days) {
    const canvas = document.getElementById('cerebro-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (dailyChart) dailyChart.destroy();

    dailyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: days.map(d => d.date),
            datasets: [{
                label: 'Decisiones',
                data: days.map(d => d.count),
                backgroundColor: 'rgba(76, 175, 80, 0.6)',
                borderColor: 'rgba(76, 175, 80, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                title: { display: false }
            },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1 } },
                x: { ticks: { maxRotation: 45 } }
            }
        }
    });
}

/* ── Decisions by type table ─────────────────────────────────── */

function renderDecisionsByType(byType) {
    const container = document.getElementById('cerebro-decisions-content');
    const rows = [
        { label: 'Evaluaciones de Salud', count: byType.health_assessments, icon: 'H' },
        { label: 'Recomendaciones de Tratamiento', count: byType.treatment_recommendations, icon: 'T' },
        { label: 'Analisis NDVI', count: byType.ndvi_analyses, icon: 'N' },
        { label: 'Analisis Termal', count: byType.thermal_analyses, icon: 'Th' },
        { label: 'Alertas Generadas', count: byType.alerts_generated, icon: 'A' },
    ];
    const total = rows.reduce((s, r) => s + r.count, 0) || 1;

    let html = '<div style="display:grid;gap:0.75rem;">';
    rows.forEach(r => {
        const pct = ((r.count / total) * 100).toFixed(1);
        html += '<div style="display:flex;align-items:center;gap:1rem;">'
            + '<span style="width:2rem;height:2rem;display:flex;align-items:center;justify-content:center;'
            + 'background:var(--accent,#4caf50);color:#fff;border-radius:6px;font-weight:700;font-size:0.75rem;">'
            + esc(r.icon) + '</span>'
            + '<div style="flex:1;">'
            + '<div style="display:flex;justify-content:space-between;">'
            + '<span>' + esc(r.label) + '</span>'
            + '<span style="font-weight:600;">' + r.count + ' (' + pct + '%)</span>'
            + '</div>'
            + '<div style="height:6px;background:#e0e0e0;border-radius:3px;margin-top:4px;">'
            + '<div style="height:100%;width:' + pct + '%;background:var(--accent,#4caf50);border-radius:3px;"></div>'
            + '</div></div></div>';
    });
    html += '</div>';
    container.innerHTML = html;
}

/* ── Accuracy section ────────────────────────────────────────── */

function renderAccuracy(accuracy, feedbackCount) {
    const container = document.getElementById('cerebro-accuracy-content');
    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;">';
    html += '<div class="intel-stat">'
        + '<div class="intel-stat-value">' + accuracy.feedback_positive_rate.toFixed(1) + '%</div>'
        + '<div class="intel-stat-label">Tasa de Retroalimentacion Positiva</div>'
        + '</div>';
    html += '<div class="intel-stat">'
        + '<div class="intel-stat-value">' + accuracy.total_feedback + '</div>'
        + '<div class="intel-stat-label">Total Retroalimentaciones</div>'
        + '</div>';
    html += '<div class="intel-stat">'
        + '<div class="intel-stat-value">' + feedbackCount + '</div>'
        + '<div class="intel-stat-label">Retroalimentaciones Recibidas</div>'
        + '</div>';
    html += '</div>';
    container.innerHTML = html;
}
