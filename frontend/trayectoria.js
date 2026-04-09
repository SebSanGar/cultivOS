/* Trayectoria de Salud — health trajectory with treatment correlations */

const API = window.location.origin;
let trajChart = null;

function fetchJSON(url) {
    return fetch(url).then(r => r.ok ? r.json() : null);
}

/* ── Farm / Field selectors ─────────────────────────────────── */

(async function initFarms() {
    const farms = await fetchJSON(API + '/api/farms');
    if (!farms) return;
    const sel = document.getElementById('traj-farm-select');
    farms.forEach(f => {
        const o = document.createElement('option');
        o.value = f.id;
        o.textContent = f.name;
        sel.appendChild(o);
    });
    document.getElementById('traj-empty').style.display = '';
})();

async function loadFieldsForTrajectory() {
    const farmId = document.getElementById('traj-farm-select').value;
    const fSel = document.getElementById('traj-field-select');
    fSel.innerHTML = '<option value="">Seleccione un campo...</option>';
    document.getElementById('traj-content').style.display = 'none';
    document.getElementById('traj-empty').style.display = '';
    if (!farmId) return;

    const fields = await fetchJSON(API + '/api/farms/' + farmId + '/fields');
    if (!fields) return;
    fields.forEach(f => {
        const o = document.createElement('option');
        o.value = f.id;
        o.textContent = f.name;
        fSel.appendChild(o);
    });
}

/* ── Load trajectory data ───────────────────────────────────── */

async function loadTrajectory() {
    const farmId = document.getElementById('traj-farm-select').value;
    const fieldId = document.getElementById('traj-field-select').value;
    if (!farmId || !fieldId) return;

    const data = await fetchJSON(
        API + '/api/farms/' + farmId + '/fields/' + fieldId + '/health/trajectory'
    );
    if (!data) return;

    document.getElementById('traj-empty').style.display = 'none';
    document.getElementById('traj-content').style.display = '';

    renderStats(data);
    renderChart(data);
    renderProjection(data);
    renderRange(data);
    renderTreatments(data);
}

/* ── Stats strip ────────────────────────────────────────────── */

const TREND_LABELS = {
    improving: 'Mejorando',
    stable: 'Estable',
    declining: 'Declinando',
    insufficient_data: 'Datos insuficientes',
};

function renderStats(data) {
    document.getElementById('traj-stat-current').textContent =
        data.current_score != null ? data.current_score.toFixed(1) : '--';
    document.getElementById('traj-stat-trend').textContent =
        TREND_LABELS[data.trend] || data.trend;
    document.getElementById('traj-stat-projection').textContent =
        data.projection != null ? data.projection.toFixed(1) : '--';
    document.getElementById('traj-stat-range').textContent =
        data.score_range
            ? data.score_range.min.toFixed(1) + ' — ' + data.score_range.max.toFixed(1)
            : '--';
}

/* ── Chart ──────────────────────────────────────────────────── */

function renderChart(data) {
    const canvas = document.getElementById('traj-canvas');
    if (trajChart) { trajChart.destroy(); trajChart = null; }
    if (!data.scores || data.scores.length === 0) {
        canvas.parentElement.querySelector('.intel-card-title').textContent =
            'Linea de Tiempo de Salud — Sin datos';
        return;
    }

    const labels = data.scores.map(s =>
        new Date(s.scored_at).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })
    );
    const scores = data.scores.map(s => s.score);

    // Mark treatment application points
    const treatmentPoints = [];
    if (data.treatment_links) {
        data.treatment_links.forEach(t => {
            if (!t.applied_at) return;
            const tDate = new Date(t.applied_at);
            // Find closest score index
            let closestIdx = 0;
            let closestDiff = Infinity;
            data.scores.forEach((s, i) => {
                const diff = Math.abs(new Date(s.scored_at) - tDate);
                if (diff < closestDiff) { closestDiff = diff; closestIdx = i; }
            });
            treatmentPoints.push({
                x: closestIdx,
                y: scores[closestIdx],
                label: t.tratamiento,
            });
        });
    }

    trajChart = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Puntaje de Salud',
                    data: scores,
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34,197,94,0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 5,
                },
                {
                    label: 'Tratamientos aplicados',
                    data: treatmentPoints.map(p => ({ x: p.x, y: p.y })),
                    pointStyle: 'triangle',
                    pointRadius: 10,
                    pointBackgroundColor: '#f59e0b',
                    showLine: false,
                    parsing: false,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            if (ctx.datasetIndex === 1 && treatmentPoints[ctx.dataIndex]) {
                                return treatmentPoints[ctx.dataIndex].label;
                            }
                            return 'Salud: ' + ctx.parsed.y.toFixed(1);
                        },
                    },
                },
            },
            scales: {
                y: { min: 0, max: 100, title: { display: true, text: 'Puntaje' } },
            },
        },
    });
}

/* ── Projection card ────────────────────────────────────────── */

function renderProjection(data) {
    const el = document.getElementById('traj-projection-content');
    if (data.projection == null) {
        el.innerHTML = '<p style="color:var(--text-muted)">Datos insuficientes para proyeccion.</p>';
        return;
    }
    const dir = data.rate_of_change > 0 ? 'positiva' : data.rate_of_change < 0 ? 'negativa' : 'neutra';
    el.innerHTML =
        '<div style="display:flex;gap:2rem;flex-wrap:wrap;">' +
        '<div><strong>Proyeccion siguiente:</strong> ' + data.projection.toFixed(1) + ' / 100</div>' +
        '<div><strong>Tasa de cambio:</strong> ' + data.rate_of_change.toFixed(2) + ' por observacion (' + dir + ')</div>' +
        '<div><strong>Observaciones:</strong> ' + data.data_points + '</div>' +
        '</div>';
}

/* ── Score range ────────────────────────────────────────────── */

function renderRange(data) {
    const el = document.getElementById('traj-range-content');
    if (!data.score_range) {
        el.innerHTML = '<p style="color:var(--text-muted)">Sin datos de rango.</p>';
        return;
    }
    const min = data.score_range.min;
    const max = data.score_range.max;
    const spread = max - min;
    el.innerHTML =
        '<div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;">' +
        '<div><strong>Minimo:</strong> ' + min.toFixed(1) + '</div>' +
        '<div style="flex:1;height:8px;background:linear-gradient(to right,#ef4444,#f59e0b,#22c55e);border-radius:4px;min-width:200px;"></div>' +
        '<div><strong>Maximo:</strong> ' + max.toFixed(1) + '</div>' +
        '<div><strong>Variacion:</strong> ' + spread.toFixed(1) + ' puntos</div>' +
        '</div>';
}

/* ── Treatment correlations ─────────────────────────────────── */

function renderTreatments(data) {
    const el = document.getElementById('traj-treatments-content');
    if (!data.treatment_links || data.treatment_links.length === 0) {
        el.innerHTML = '<p style="color:var(--text-muted)">No hay tratamientos con correlacion de salud registrados.</p>';
        return;
    }

    // Sort by delta descending (best improvements first)
    const sorted = [...data.treatment_links].sort((a, b) => b.delta - a.delta);

    el.innerHTML = sorted.map(t => {
        const deltaColor = t.delta > 0 ? '#22c55e' : t.delta < 0 ? '#ef4444' : '#94a3b8';
        const deltaSign = t.delta > 0 ? '+' : '';
        const dateStr = t.applied_at
            ? new Date(t.applied_at).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
            : 'Sin fecha';
        return '<div class="intel-card" style="margin-bottom:1rem;padding:1rem;">' +
            '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">' +
            '<div>' +
            '<strong>' + esc(t.tratamiento) + '</strong>' +
            '<div style="color:var(--text-muted);font-size:0.85rem;">' + esc(t.problema) + ' — ' + dateStr + '</div>' +
            '</div>' +
            '<div style="display:flex;gap:1.5rem;align-items:center;">' +
            '<div><span style="color:var(--text-muted)">Antes:</span> ' + t.health_before.toFixed(1) + '</div>' +
            '<div><span style="color:var(--text-muted)">Despues:</span> ' + t.health_after.toFixed(1) + '</div>' +
            '<div style="font-size:1.2rem;font-weight:700;color:' + deltaColor + ';">' + deltaSign + t.delta.toFixed(1) + '</div>' +
            '</div>' +
            '</div>' +
            '</div>';
    }).join('');
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
}
