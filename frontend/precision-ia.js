/* precision-ia.js — Prediction accuracy tracker dashboard */

const API = window.location.origin;
let predChart = null;

function fetchJSON(url) {
    return fetch(url).then(r => r.ok ? r.json() : null);
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

/* ── Load on page init ─────────────────────────��────────────── */

(async function loadPredictionAccuracy() {
    const data = await fetchJSON(API + '/api/intel/prediction-accuracy');
    if (!data || data.total_predictions === 0) {
        document.getElementById('pred-empty').style.display = '';
        document.getElementById('pred-content').style.display = 'none';
        return;
    }

    document.getElementById('pred-empty').style.display = 'none';
    document.getElementById('pred-content').style.display = '';

    renderStats(data);
    renderStatus(data.status);
    renderByType(data.by_type);
    renderRecentTable(data.recent);
    renderErrorChart(data.recent);
})();

/* ── Stats strip ────────────────────────────────────────────── */

function renderStats(data) {
    document.getElementById('pred-stat-total').textContent = data.total_predictions;
    document.getElementById('pred-stat-resolved').textContent = data.resolved;
    document.getElementById('pred-stat-pending').textContent = data.pending;
    document.getElementById('pred-stat-mape').textContent =
        data.mape != null ? data.mape.toFixed(1) + '%' : '--';
}

function renderStatus(status) {
    const el = document.getElementById('pred-status');
    const labels = { green: 'Precision Alta', yellow: 'Precision Media', red: 'Recalibrar' };
    const colors = { green: '#22c55e', yellow: '#eab308', red: '#ef4444' };
    el.textContent = labels[status] || status;
    el.style.background = colors[status] || '#64748b';
    el.style.color = '#fff';
}

/* ── By type breakdown ──────────────────────────────────────── */

function renderByType(byType) {
    const container = document.getElementById('pred-by-type-content');
    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem;margin-top:1rem;">';

    for (const [ptype, info] of Object.entries(byType)) {
        const label = ptype === 'yield' ? 'Rendimiento' : ptype === 'health' ? 'Salud' : ptype;
        const mapeStr = info.mape != null ? info.mape.toFixed(1) + '%' : '--';
        const barColor = info.mape == null ? '#64748b' : info.mape <= 30 ? '#22c55e' : info.mape <= 40 ? '#eab308' : '#ef4444';

        html += '<div style="background:rgba(255,255,255,0.05);border-radius:12px;padding:1.2rem;">'
            + '<div style="font-weight:700;font-size:1.1rem;margin-bottom:0.5rem;">' + esc(label) + '</div>'
            + '<div style="display:flex;justify-content:space-between;font-size:0.85rem;color:#94a3b8;margin-bottom:0.3rem;">'
            + '<span>Resueltas: ' + info.resolved + '/' + info.total + '</span>'
            + '<span>MAPE: ' + mapeStr + '</span>'
            + '</div>'
            + '<div style="height:8px;background:rgba(255,255,255,0.1);border-radius:4px;">'
            + '<div style="width:' + Math.min(100, info.mape || 0) + '%;height:100%;background:' + barColor + ';border-radius:4px;"></div>'
            + '</div>'
            + '</div>';
    }

    html += '</div>';
    container.innerHTML = html;
}

/* ── Recent predictions table ────────────────────────────────�� */

function renderRecentTable(recent) {
    const container = document.getElementById('pred-recent-content');
    if (!recent.length) { container.innerHTML = '<p>Sin predicciones recientes.</p>'; return; }

    let html = '<table style="width:100%;border-collapse:collapse;margin-top:1rem;">'
        + '<thead><tr style="border-bottom:1px solid rgba(255,255,255,0.1);">'
        + '<th style="text-align:left;padding:0.5rem;">Tipo</th>'
        + '<th style="text-align:right;padding:0.5rem;">Predicho</th>'
        + '<th style="text-align:right;padding:0.5rem;">Real</th>'
        + '<th style="text-align:right;padding:0.5rem;">Error %</th>'
        + '<th style="text-align:right;padding:0.5rem;">Fecha</th>'
        + '</tr></thead><tbody>';

    recent.forEach(p => {
        const typeLabel = p.prediction_type === 'yield' ? 'Rendimiento' : p.prediction_type === 'health' ? 'Salud' : p.prediction_type;
        const actual = p.actual_value != null ? p.actual_value.toLocaleString() : 'Pendiente';
        const error = p.error_pct != null ? p.error_pct.toFixed(1) + '%' : '--';
        const date = p.predicted_at ? p.predicted_at.split('T')[0] : '--';
        const errorColor = p.error_pct == null ? '#64748b' : p.error_pct <= 10 ? '#22c55e' : p.error_pct <= 20 ? '#eab308' : '#ef4444';

        html += '<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">'
            + '<td style="padding:0.5rem;">' + esc(typeLabel) + '</td>'
            + '<td style="text-align:right;padding:0.5rem;">' + p.predicted_value.toLocaleString() + '</td>'
            + '<td style="text-align:right;padding:0.5rem;">' + actual + '</td>'
            + '<td style="text-align:right;padding:0.5rem;color:' + errorColor + ';">' + error + '</td>'
            + '<td style="text-align:right;padding:0.5rem;color:#64748b;">' + date + '</td>'
            + '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

/* ── Error chart ────────────────────────────────────────────── */

function renderErrorChart(recent) {
    const canvas = document.getElementById('pred-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const resolved = recent.filter(p => p.error_pct != null);
    if (!resolved.length) return;

    if (predChart) predChart.destroy();

    predChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: resolved.map((p, i) => {
                const label = p.prediction_type === 'yield' ? 'Rend' : 'Salud';
                return label + ' #' + (i + 1);
            }),
            datasets: [{
                label: 'Error %',
                data: resolved.map(p => p.error_pct),
                backgroundColor: resolved.map(p =>
                    p.error_pct <= 10 ? 'rgba(34,197,94,0.6)' :
                    p.error_pct <= 20 ? 'rgba(234,179,8,0.6)' :
                    'rgba(239,68,68,0.6)'
                ),
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Error (%)' }, ticks: { stepSize: 5 } },
                x: { ticks: { maxRotation: 45 } },
            }
        }
    });
}
