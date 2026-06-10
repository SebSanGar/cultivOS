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
    const farms = await fetchJSON('/api/farms');
    const select = document.getElementById('econ-farm-select');
    if (farms && farms.length > 0) {
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

    if (!farmId) {
        resetStats();
        notaEl.style.display = 'none';
        destroyChart();
        return;
    }

    const data = await fetchJSON(`/api/farms/${farmId}/economic-impact`);

    if (!data) {
        resetStats();
        notaEl.style.display = 'block';
        notaEl.textContent = 'No se pudo obtener el impacto economico. Intente de nuevo.';
        destroyChart();
        return;
    }

    updateStats(data);
    updateCards(data);
    updateChart(data);
    updateNota(data.nota, notaEl);
    updateRoiHero(data);
    updatePaybackGauge(data);
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

    econChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Agua', 'Fertilizante', 'Rendimiento'],
            datasets: [{
                label: 'Ahorro estimado (MXN/ano)',
                data: [
                    data.water_savings_mxn || 0,
                    data.fertilizer_savings_mxn || 0,
                    data.yield_improvement_mxn || 0,
                ],
                backgroundColor: ['#4da6ff', '#00c896', '#f0b429'],
                borderColor: ['#4da6ff', '#00c896', '#f0b429'],
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '$' + (context.raw || 0).toLocaleString() + ' MXN';
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

document.addEventListener('DOMContentLoaded', initPage);
