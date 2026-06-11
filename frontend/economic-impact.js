/* -- cultivOS Economic Impact Report -- economic-impact.js -- */

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

function formatMXN(value) {
    return '$' + (value || 0).toLocaleString() + ' MXN';
}

let econChart = null;

async function initPage() {
    const resp = await fetchJSON('/api/farms?page_size=100');
    const farms = (resp && (resp.data || resp.items)) || (Array.isArray(resp) ? resp : []);
    const select = document.getElementById('econ-farm-select');
    if (farms.length > 0) {
        farms.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.id;
            opt.textContent = f.name;
            select.appendChild(opt);
        });
        select.value = farms[0].id;
        loadEconomicImpact();
    }
    setupNav();
}

function setupNav() {
    const token = localStorage.getItem('cultivOS_token');
    const userInfo = document.getElementById('nav-user-info');
    const username = document.getElementById('nav-username');
    const logout = document.getElementById('nav-logout');
    if (token && userInfo) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            username.textContent = payload.sub || '';
        } catch { /* ignore */ }
        userInfo.style.display = 'flex';
        logout.onclick = (e) => {
            e.preventDefault();
            localStorage.removeItem('cultivOS_token');
            window.location.href = '/login';
        };
    }
}

async function loadEconomicImpact() {
    const farmId = document.getElementById('econ-farm-select').value;
    const notaEl = document.getElementById('econ-nota');
    const skeleton = document.getElementById('econ-hero-skeleton');

    if (!farmId) {
        resetStats();
        notaEl.style.display = 'none';
        destroyChart();
        if (skeleton) skeleton.style.display = 'none';
        return;
    }

    if (skeleton) skeleton.style.display = 'block';

    const data = await fetchJSON(`/api/farms/${farmId}/economic-impact`);

    if (skeleton) skeleton.style.display = 'none';

    if (!data) {
        resetStats();
        notaEl.style.display = 'block';
        notaEl.textContent = 'Could not load economic impact data. Please try again.';
        destroyChart();
        return;
    }

    updateStats(data);
    updateCards(data);
    updateChart(data);
    updateNota(data.nota, notaEl);
    updateRoiHero(data);
    updatePaybackGauge(data);
    updateConfidenceBadges(data);
    updatePerHaTable(data);
    updateRiskAvoided(data);
    updateTreatmentRoiLeaderboard(farmId);
    updateCumulativeChart(farmId);
    updateDownloadReportLink(farmId);
    updateOntarioSoonBanner(data);
}

function resetStats() {
    document.getElementById('econ-total-savings').textContent = '--';
    document.getElementById('econ-hectares').textContent = '--';
    document.getElementById('econ-water').textContent = '--';
    document.getElementById('econ-fertilizer').textContent = '--';
    document.getElementById('econ-yield').textContent = '--';
    document.getElementById('econ-card-water').textContent = '$0 MXN';
    document.getElementById('econ-card-fertilizer').textContent = '$0 MXN';
    document.getElementById('econ-card-yield').textContent = '$0 MXN';
}

function updateStats(data) {
    document.getElementById('econ-total-savings').textContent = formatMXN(data.total_savings_mxn);
    document.getElementById('econ-hectares').textContent = (data.hectares || 0).toFixed(1) + ' ha';
    document.getElementById('econ-water').textContent = formatMXN(data.water_savings_mxn);
    document.getElementById('econ-fertilizer').textContent = formatMXN(data.fertilizer_savings_mxn);
    document.getElementById('econ-yield').textContent = formatMXN(data.yield_improvement_mxn);
}

function updateCards(data) {
    document.getElementById('econ-card-water').textContent = formatMXN(data.water_savings_mxn);
    document.getElementById('econ-card-fertilizer').textContent = formatMXN(data.fertilizer_savings_mxn);
    document.getElementById('econ-card-yield').textContent = formatMXN(data.yield_improvement_mxn);
}

function updateNota(nota, el) {
    if (nota) {
        el.style.display = 'block';
        el.textContent = nota;
    } else {
        el.style.display = 'none';
    }
}

function destroyChart() {
    if (econChart) {
        econChart.destroy();
        econChart = null;
    }
}

function updateChart(data) {
    destroyChart();
    const canvas = document.getElementById('econ-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const waterPotential = data.water_potential_mxn || 0;
    const fertPotential = data.fertilizer_potential_mxn || 0;
    const yieldPotential = data.yield_potential_mxn || 0;

    const waterEst = data.water_savings_mxn || 0;
    const fertEst = data.fertilizer_savings_mxn || 0;
    const yieldEst = data.yield_improvement_mxn || 0;

    const waterConservative = Math.round(waterEst * 0.6);
    const fertConservative = Math.round(fertEst * 0.6);
    const yieldConservative = Math.round(yieldEst * 0.6);

    econChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Water', 'Fertilizer', 'Yield'],
            datasets: [
                {
                    label: 'Baseline (without cultivOS)',
                    data: [waterPotential, fertPotential, yieldPotential],
                    backgroundColor: ['rgba(180,180,180,0.25)', 'rgba(180,180,180,0.25)', 'rgba(180,180,180,0.25)'],
                    borderColor: ['rgba(180,180,180,0.5)', 'rgba(180,180,180,0.5)', 'rgba(180,180,180,0.5)'],
                    borderWidth: 1,
                    borderRadius: 4,
                },
                {
                    label: 'With cultivOS — estimated',
                    data: [waterEst, fertEst, yieldEst],
                    backgroundColor: ['#4da6ff', '#00c896', '#f0b429'],
                    borderColor: ['#4da6ff', '#00c896', '#f0b429'],
                    borderWidth: 1,
                    borderRadius: 4,
                },
                {
                    label: 'With cultivOS — conservative',
                    data: [waterConservative, fertConservative, yieldConservative],
                    backgroundColor: ['rgba(77,166,255,0.4)', 'rgba(0,200,150,0.4)', 'rgba(240,180,41,0.4)'],
                    borderColor: ['rgba(77,166,255,0.7)', 'rgba(0,200,150,0.7)', 'rgba(240,180,41,0.7)'],
                    borderWidth: 1,
                    borderRadius: 4,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: { color: '#aaa', padding: 16, boxWidth: 12 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + (context.raw || 0).toLocaleString();
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#aaa',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                x: {
                    ticks: { color: '#aaa' },
                    grid: { display: false }
                }
            }
        }
    });
}

function updateRoiHero(data) {
    const hero = document.getElementById('econ-roi-hero');
    const forward = document.getElementById('econ-roi-forward');
    if (!hero || !forward) return;

    if (data.roi_multiple !== null && data.roi_multiple !== undefined) {
        hero.style.display = 'block';
        forward.style.display = 'none';
        const net = data.net_savings_mxn || 0;
        document.getElementById('econ-roi-net').textContent = 'about $' + net.toLocaleString();
        document.getElementById('econ-roi-multiple').textContent = data.roi_multiple + 'x';
        const payback = data.payback_months;
        document.getElementById('econ-roi-payback').textContent = payback ? '~' + payback + ' mo' : '—';
        const cost = data.subscription_cost_mxn;
        document.getElementById('econ-roi-cost').textContent = cost ? '$' + cost.toLocaleString() + '/yr' : '—';
    } else {
        hero.style.display = 'none';
        forward.style.display = 'block';
    }
}

function updateConfidenceBadges(data) {
    const label = data.confidence_label || "Estimado";
    const modifierMap = {
        "Estimado": "",
        "Medido": "estimate-badge--measured",
        "Confirmado": "estimate-badge--confirmed",
    };
    const modifier = modifierMap[label] || "";
    const badgeIds = ["econ-confidence-badge-total", "econ-confidence-badge-hero"];
    badgeIds.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = label;
        el.classList.remove("estimate-badge--measured", "estimate-badge--confirmed");
        if (modifier) el.classList.add(modifier);
    });
}

function updatePaybackGauge(data) {
    const section = document.getElementById('payback-gauge-section');
    const ring = document.getElementById('payback-ring');
    const valueEl = document.getElementById('payback-ring-value');
    if (!section || !ring || !valueEl) return;

    const payback = data.payback_months;
    if (payback === null || payback === undefined) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    valueEl.textContent = payback;

    ring.classList.remove('payback-ring--green', 'payback-ring--amber', 'payback-ring--red');
    if (payback < 6) {
        ring.classList.add('payback-ring--green');
    } else if (payback <= 12) {
        ring.classList.add('payback-ring--amber');
    } else if (payback > 12) {
        ring.classList.add('payback-ring--red');
    }
}

function formatPerHa(value) {
    if (value === null || value === undefined) return '—';
    return '$' + value.toLocaleString() + '/ha';
}

function updatePerHaTable(data) {
    const section = document.getElementById('econ-per-ha-table');
    if (!section) return;

    const perHa = data.savings_per_ha_mxn;
    if (perHa === null || perHa === undefined) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';

    const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    set('econ-per-ha-water', formatPerHa(data.water_savings_per_ha_mxn));
    set('econ-total-water', formatMXN(data.water_savings_mxn));
    set('econ-per-ha-fertilizer', formatPerHa(data.fertilizer_savings_per_ha_mxn));
    set('econ-total-fertilizer', formatMXN(data.fertilizer_savings_mxn));
    set('econ-per-ha-yield', formatPerHa(data.yield_improvement_per_ha_mxn));
    set('econ-total-yield', formatMXN(data.yield_improvement_mxn));
    set('econ-per-ha-total', formatPerHa(perHa));
    set('econ-grand-total', formatMXN(data.total_savings_mxn));
}

function updateDownloadReportLink(farmId) {
    const section = document.getElementById('econ-download-section');
    const link = document.getElementById('econ-download-report');
    if (!section || !link) return;
    if (!farmId) {
        section.style.display = 'none';
        return;
    }
    link.href = `/api/farms/${farmId}/season-report-pdf`;
    section.style.display = 'block';
}

let cumulativeChart = null;

async function updateCumulativeChart(farmId) {
    const section = document.getElementById('econ-cumulative-section');
    const canvas = document.getElementById('econ-cumulative-chart');
    const beLabel = document.getElementById('econ-breakeven-label');
    if (!section || !canvas) return;

    if (!farmId) {
        section.style.display = 'none';
        return;
    }

    const data = await fetchJSON(`/api/farms/${farmId}/cumulative-savings`);
    if (!data || !data.data_points || data.data_points.length === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';

    if (cumulativeChart) {
        cumulativeChart.destroy();
        cumulativeChart = null;
    }

    const labels = data.data_points.map(p => 'Month ' + p.month);
    const values = data.data_points.map(p => p.cumulative_savings_mxn);
    const subCost = data.subscription_cost_mxn;
    const beMonth = data.breakeven_month;

    if (beLabel) {
        if (beMonth) {
            beLabel.textContent = 'Breakeven reached at month ' + beMonth + ' — subscription pays for itself after that.';
        } else if (subCost) {
            beLabel.textContent = 'Breakeven not yet reached — more data needed.';
        } else {
            beLabel.textContent = '';
        }
    }

    const datasets = [
        {
            label: 'Cumulative savings',
            data: values,
            borderColor: '#2d6a2d',
            backgroundColor: 'rgba(45,106,45,0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.3,
            pointRadius: 4,
        },
    ];

    if (subCost) {
        datasets.push({
            label: 'Subscription cost',
            data: Array(labels.length).fill(subCost),
            borderColor: 'rgba(240,180,41,0.8)',
            borderWidth: 1,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
        });
    }

    cumulativeChart = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'bottom', labels: { color: '#aaa', padding: 16 } },
                annotation: beMonth ? {
                    annotations: {
                        breakeven: {
                            type: 'line',
                            xMin: beMonth - 1,
                            xMax: beMonth - 1,
                            borderColor: 'rgba(0,200,150,0.8)',
                            borderWidth: 2,
                            label: { content: 'Breakeven', enabled: true, position: 'top' },
                        }
                    }
                } : {},
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#aaa', callback: v => '$' + v.toLocaleString() },
                    grid: { color: 'rgba(255,255,255,0.05)' },
                },
                x: { ticks: { color: '#aaa' }, grid: { display: false } },
            },
        },
    });
}

async function updateTreatmentRoiLeaderboard(farmId) {
    const section = document.getElementById('econ-treatment-roi-section');
    const emptyEl = document.getElementById('econ-treatment-roi-empty');
    const table = document.getElementById('econ-treatment-roi-table');
    const tbody = document.getElementById('econ-treatment-roi-tbody');
    if (!section || !emptyEl || !table || !tbody) return;

    if (!farmId) {
        section.style.display = 'none';
        return;
    }

    const roi = await fetchJSON(`/api/farms/${farmId}/treatment-roi`);
    section.style.display = 'block';

    if (!roi || !roi.treatments || roi.treatments.length === 0) {
        emptyEl.style.display = 'block';
        table.style.display = 'none';
        return;
    }

    emptyEl.style.display = 'none';
    table.style.display = 'table';
    tbody.innerHTML = '';

    const top5 = roi.treatments.slice(0, 5);
    top5.forEach((item, idx) => {
        const tr = document.createElement('tr');
        const delta = item.avg_health_delta !== null ? (item.avg_health_delta > 0 ? '+' : '') + item.avg_health_delta.toFixed(1) : '—';
        const cpp = item.cost_per_health_point !== null ? '$' + item.cost_per_health_point.toFixed(0) : '—';
        const name = esc(item.treatment_type || '').slice(0, 40);
        tr.innerHTML = `<td>${idx + 1}</td><td>${name}</td><td>${item.count}</td><td>${delta}</td><td>${cpp}</td>`;
        tbody.appendChild(tr);
    });
}

function updateRiskAvoided(data) {
    const section = document.getElementById('econ-risk-avoided-section');
    const valueEl = document.getElementById('econ-risk-avoided-value');
    if (!section || !valueEl) return;

    const risk = data.risk_avoided_mxn;
    if (risk === null || risk === undefined) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    valueEl.textContent = 'about $' + risk.toLocaleString();
}

document.addEventListener('DOMContentLoaded', initPage);
