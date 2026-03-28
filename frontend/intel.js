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

// ── Carbon Sequestration ──
async function loadCarbon() {
    const container = document.getElementById('intel-carbon');
    const data = await fetchJSON(API + '/carbon');

    if (!data || data.total_fields === 0) {
        container.innerHTML = '<div class="intel-empty">Sin datos de carbono</div>';
        return;
    }

    const tendenciaLabel = {
        ganando: 'Ganando',
        estable: 'Estable',
        perdiendo: 'Perdiendo',
        datos_insuficientes: 'Sin tendencia',
    };

    const tendenciaClass = {
        ganando: 'positive',
        estable: '',
        perdiendo: 'negative',
        datos_insuficientes: '',
    };

    container.innerHTML = `
        <div class="carbon-summary">
            <div class="carbon-total">
                <span class="carbon-total-label">Secuestro Total Estimado</span>
                <span class="carbon-total-value">${Number(data.total_sequestration_tonnes).toLocaleString('es-MX', {maximumFractionDigits: 1})} t CO2e</span>
            </div>
            <div class="carbon-meta">
                ${data.total_fields} campos — ${data.total_hectares} ha — SOC promedio ${data.avg_soc_tonnes_per_ha} t/ha
            </div>
            <div class="carbon-fields">
                ${data.fields.map(f => {
                    const cls = tendenciaClass[f.tendencia] || '';
                    const label = tendenciaLabel[f.tendencia] || f.tendencia;
                    return `
                    <div class="carbon-field-row">
                        <div class="carbon-field-info">
                            <span class="carbon-field-name">${esc(f.field_name)}</span>
                            <span class="carbon-field-farm">${esc(f.farm_name)}</span>
                        </div>
                        <span class="carbon-field-soc">${f.soc_tonnes_per_ha} t/ha</span>
                        <span class="carbon-field-trend ${cls}">${label}</span>
                    </div>`;
                }).join('')}
            </div>
        </div>
    `;
}

// ── TEK Validation ──
async function loadTEKValidation() {
    const container = document.getElementById('intel-tek-validation');
    const data = await fetchJSON(API + '/tek-validation');

    if (!data || data.methods.length === 0) {
        container.innerHTML = '<div class="intel-empty">Sin datos de validacion TEK</div>';
        return;
    }

    container.innerHTML = data.methods.map(m => {
        const trustWidth = Math.min(Math.round(m.trust_score), 100);
        const trustCls = trustWidth > 60 ? 'good' : trustWidth >= 30 ? 'warning' : 'critical';

        return `
        <div class="tek-method-card">
            <div class="tek-method-header">
                <span class="tek-method-name">${esc(m.method_name)}</span>
                <span class="tek-method-feedback">${m.total_feedback} reportes</span>
            </div>
            <div class="tek-method-score-row">
                <span class="tek-method-label">Confianza</span>
                <div class="tek-method-score-bar">
                    <div class="score-bar-fill ${trustCls}" style="width:${trustWidth}%"></div>
                </div>
                <span class="tek-method-score-val">${m.trust_score.toFixed(1)}</span>
            </div>
            <div class="tek-method-counts">
                <span class="tek-count-positive">${m.positive_count} positivos</span>
                <span class="tek-count-negative">${m.negative_count} negativos</span>
                <span class="tek-method-rating">${m.average_rating.toFixed(1)}/5</span>
            </div>
        </div>`;
    }).join('');
}

// ── Sensor Fusion Overview ──
async function loadSensorFusion() {
    const container = document.getElementById('intel-sensor-fusion');
    const badge = document.getElementById('intel-fusion-confidence');
    const data = await fetchJSON(API + '/sensor-fusion');

    if (!data || data.fields_with_data === 0) {
        container.innerHTML = '<div class="intel-empty">Sin datos de fusion de sensores</div>';
        if (badge) badge.textContent = '--';
        return;
    }

    if (badge) badge.textContent = Math.round(data.avg_confidence * 100) + '%';

    const sensorLabels = { ndvi: 'NDVI', thermal: 'Termico', soil: 'Suelo', weather: 'Clima' };

    const summaryHtml = `
        <div class="fusion-overview-summary">
            <div class="fusion-overview-stat">
                <span class="fusion-overview-stat-value">${data.fields_with_data}/${data.total_fields}</span>
                <span class="fusion-overview-stat-label">Campos con datos</span>
            </div>
            <div class="fusion-overview-stat">
                <span class="fusion-overview-stat-value">${Math.round(data.avg_confidence * 100)}%</span>
                <span class="fusion-overview-stat-label">Confianza promedio</span>
            </div>
            <div class="fusion-overview-stat">
                <span class="fusion-overview-stat-value ${data.total_contradictions > 0 ? 'negative' : ''}">${data.total_contradictions}</span>
                <span class="fusion-overview-stat-label">Inconsistencias</span>
            </div>
        </div>
    `;

    const fieldsHtml = data.fields.map(f => {
        const confPct = Math.round(f.confidence * 100);
        const confCls = confPct >= 60 ? 'good' : confPct >= 30 ? 'warning' : 'critical';
        const sensors = ['ndvi', 'thermal', 'soil', 'weather'].map(s => {
            const active = f.sensors_used.includes(s);
            return '<span class="fusion-sensor-badge ' + (active ? 'active' : 'inactive') + '">' + sensorLabels[s] + '</span>';
        }).join('');

        let contradictionsHtml = '';
        if (f.contradictions.length > 0) {
            contradictionsHtml = f.contradictions.map(c =>
                '<div class="fusion-overview-contradiction">' +
                '<span class="fusion-overview-contradiction-tag">' + c.sensors.map(s => sensorLabels[s] || s).join(' vs ') + '</span> ' +
                '<span class="fusion-overview-contradiction-desc">' + esc(c.description) + '</span>' +
                '</div>'
            ).join('');
        }

        return `
        <div class="fusion-overview-field">
            <div class="fusion-overview-field-header">
                <span class="fusion-overview-field-name">${esc(f.field_name)}</span>
                <span class="fusion-overview-field-farm">${esc(f.farm_name)}</span>
                <span class="health-badge ${confCls}">${confPct}%</span>
            </div>
            <div class="fusion-overview-field-sensors">${sensors}</div>
            ${contradictionsHtml}
        </div>`;
    }).join('');

    container.innerHTML = summaryHtml + '<div class="fusion-overview-fields">' + fieldsHtml + '</div>';
}

// ── Batch Health Portfolio Grid ──
async function loadBatchHealth() {
    const container = document.getElementById('intel-batch-health');
    if (!container) return;

    // Fetch all farms to collect field IDs
    const farmsData = await fetchJSON('/api/farms');
    if (!farmsData) {
        container.innerHTML = '<div class="intel-empty">Sin datos de salud disponibles</div>';
        return;
    }
    const farms = Array.isArray(farmsData) ? farmsData : (farmsData.data || farmsData.farms || []);
    if (farms.length === 0) {
        container.innerHTML = '<div class="intel-empty">Sin datos de salud disponibles</div>';
        return;
    }

    // Fetch fields for each farm
    const fieldIds = [];
    for (const farm of farms) {
        const fields = await fetchJSON('/api/farms/' + farm.id + '/fields');
        if (fields && Array.isArray(fields)) {
            fields.forEach(f => fieldIds.push(f.id));
        }
    }

    if (fieldIds.length === 0) {
        container.innerHTML = '<div class="intel-empty">Sin datos de salud disponibles</div>';
        return;
    }

    // POST to batch-health
    const token = localStorage.getItem('cultivOS_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    let data;
    try {
        const resp = await fetch(API + '/batch-health', {
            method: 'POST',
            headers,
            body: JSON.stringify({ field_ids: fieldIds }),
        });
        if (!resp.ok) {
            container.innerHTML = '<div class="intel-empty">Sin datos de salud disponibles</div>';
            return;
        }
        data = await resp.json();
    } catch {
        container.innerHTML = '<div class="intel-empty">Sin datos de salud disponibles</div>';
        return;
    }

    const results = data.results || [];
    document.getElementById('intel-batch-count').textContent = results.length;

    if (results.length === 0) {
        container.innerHTML = '<div class="intel-empty">Sin datos de salud disponibles</div>';
        return;
    }

    const trendLabels = { improving: 'Mejorando', stable: 'Estable', declining: 'Declinando' };
    const trendIcons = { improving: '&#x25B2;', stable: '&#x25AC;', declining: '&#x25BC;' };

    container.innerHTML = '<div class="batch-health-grid">' + results.map(r => {
        const cls = healthClass(r.score);
        const scoreText = r.score != null ? Math.round(r.score) : '--';
        const trendText = r.trend ? (trendLabels[r.trend] || r.trend) : '';
        const trendIcon = r.trend ? (trendIcons[r.trend] || '') : '';
        const trendCls = r.trend === 'declining' ? 'critical' : (r.trend === 'improving' ? 'good' : '');
        return `
        <div class="batch-health-card ${cls}">
            <div class="batch-health-score health-badge ${cls}">${scoreText}</div>
            <div class="batch-health-field">${esc(r.field_name || 'Campo ' + r.field_id)}</div>
            <div class="batch-health-farm">${esc(r.farm_name || '')}</div>
            ${trendText ? `<div class="batch-health-trend ${trendCls}"><span>${trendIcon}</span> ${trendText}</div>` : ''}
            ${r.sources ? `<div class="batch-health-sources">${r.sources.map(s => `<span class="batch-health-source">${esc(s)}</span>`).join('')}</div>` : ''}
        </div>`;
    }).join('') + '</div>';
}

// ── Farm Comparison ──
async function loadFarmSelectOptions() {
    const select = document.getElementById('farm-compare-select');
    if (!select) return;
    const data = await fetchJSON('/api/farms');
    if (!data) return;
    const farms = Array.isArray(data) ? data : (data.data || data.farms || []);
    select.innerHTML = '';
    farms.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = f.name;
        select.appendChild(opt);
    });
    // Auto-select all if 5 or fewer farms
    if (farms.length <= 5) {
        Array.from(select.options).forEach(o => { o.selected = true; });
        loadFarmComparison();
    }
}

async function loadFarmComparison() {
    const container = document.getElementById('intel-farm-compare');
    const select = document.getElementById('farm-compare-select');
    if (!container || !select) return;

    const ids = Array.from(select.selectedOptions).map(o => o.value);
    if (ids.length === 0) {
        container.innerHTML = '<div class="intel-empty">Seleccione granjas para comparar</div>';
        return;
    }

    container.innerHTML = '<div class="loading"><div class="loading-spinner"></div>Cargando...</div>';
    const data = await fetchJSON(API + '/compare?farm_ids=' + ids.join(','));

    if (!data || !data.farms || data.farms.length === 0) {
        container.innerHTML = '<div class="intel-empty">Sin datos de comparacion</div>';
        return;
    }

    const maxYield = Math.max(...data.farms.map(f => f.yield_total_kg || 0), 1);

    container.innerHTML = `
        <div class="compare-table">
            <div class="compare-header-row">
                <span class="compare-cell compare-cell-name">Granja</span>
                <span class="compare-cell">Campos</span>
                <span class="compare-cell">Hectareas</span>
                <span class="compare-cell">Salud</span>
                <span class="compare-cell">Rendimiento (kg)</span>
                <span class="compare-cell">Tratamientos</span>
            </div>
            ${data.farms.map(f => {
                const cls = healthClass(f.avg_health);
                const healthVal = f.avg_health != null ? Math.round(f.avg_health) : '--';
                const yieldWidth = Math.min(100, Math.round((f.yield_total_kg || 0) / maxYield * 100));
                return `
                <div class="compare-row">
                    <span class="compare-cell compare-cell-name">${esc(f.farm_name)}</span>
                    <span class="compare-cell">${f.field_count}</span>
                    <span class="compare-cell">${f.total_hectares}</span>
                    <span class="compare-cell"><span class="health-badge ${cls}">${healthVal}</span></span>
                    <span class="compare-cell compare-cell-yield">
                        <div class="compare-yield-bar">
                            <div class="score-bar-fill good" style="width:${yieldWidth}%"></div>
                        </div>
                        <span>${Number(f.yield_total_kg || 0).toLocaleString('es-MX')}</span>
                    </span>
                    <span class="compare-cell">${f.treatment_count}</span>
                </div>`;
            }).join('')}
        </div>
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

// ── CSV Export ──
function exportIntelCSV() {
    const token = localStorage.getItem('cultivOS_token');
    const headers = {};
    if (token) headers['Authorization'] = 'Bearer ' + token;

    fetch('/api/intel/export', { headers })
        .then(resp => {
            if (!resp.ok) throw new Error('Export failed');
            return resp.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'cultivOS_intel_export.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        })
        .catch(() => {
            alert('Error al exportar datos');
        });
}

// ── Init ──
async function init() {
    applyRoleVisibility();
    await Promise.all([
        loadSummary(),
        loadAnomalies(),
        loadSoilTrends(),
        loadEconomics(),
        loadCarbon(),
        loadSensorFusion(),
        loadTEKValidation(),
        loadFarmSelectOptions(),
        loadBatchHealth(),
        loadCropTypeOptions().then(() => loadTreatmentReport()),
    ]);
}

init();
