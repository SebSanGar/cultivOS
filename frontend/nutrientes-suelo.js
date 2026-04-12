(function () {
    const farmSel = document.getElementById("sn-farm-select");
    const fieldSel = document.getElementById("sn-field-select");
    const content = document.getElementById("sn-content");
    const empty = document.getElementById("sn-empty");
    const nTrend = document.getElementById("sn-nitrogen-trend");
    const pTrend = document.getElementById("sn-phosphorus-trend");
    const kTrend = document.getElementById("sn-potassium-trend");
    const omTrend = document.getElementById("sn-organic-trend");
    let chart = null;

    const TREND_LABEL = {
        improving: "Mejorando",
        stable: "Estable",
        declining: "Disminuyendo"
    };

    async function fetchJSON(url) {
        try {
            const r = await fetch(url);
            if (!r.ok) return null;
            return await r.json();
        } catch (e) {
            return null;
        }
    }

    function showEmpty(msg) {
        content.style.display = "none";
        empty.style.display = "block";
        empty.textContent = msg;
    }

    function setTrendPill(el, trend) {
        const key = trend || "stable";
        el.textContent = TREND_LABEL[key] || "--";
        el.className = "sn-pill-value " + key;
    }

    function renderChart(monthly) {
        const ctx = document.getElementById("sn-chart").getContext("2d");
        if (chart) {
            chart.destroy();
            chart = null;
        }
        const labels = monthly.map(function (m) { return m.month_label; });
        const n = monthly.map(function (m) { return m.avg_nitrogen_ppm; });
        const p = monthly.map(function (m) { return m.avg_phosphorus_ppm; });
        const k = monthly.map(function (m) { return m.avg_potassium_ppm; });
        const om = monthly.map(function (m) { return m.avg_organic_matter_pct; });

        chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    { label: "Nitrógeno (ppm)", data: n, borderColor: "#4ade80", backgroundColor: "rgba(74,222,128,0.15)", tension: 0.3, spanGaps: true },
                    { label: "Fósforo (ppm)", data: p, borderColor: "#fbbf24", backgroundColor: "rgba(251,191,36,0.15)", tension: 0.3, spanGaps: true },
                    { label: "Potasio (ppm)", data: k, borderColor: "#60a5fa", backgroundColor: "rgba(96,165,250,0.15)", tension: 0.3, spanGaps: true },
                    { label: "Materia Orgánica (%)", data: om, borderColor: "#f472b6", backgroundColor: "rgba(244,114,182,0.15)", tension: 0.3, spanGaps: true, yAxisID: "y1" }
                ]
            },
            options: {
                responsive: true,
                interaction: { mode: "index", intersect: false },
                scales: {
                    y: { beginAtZero: true, position: "left", title: { display: true, text: "ppm" } },
                    y1: { beginAtZero: true, position: "right", title: { display: true, text: "%" }, grid: { drawOnChartArea: false } }
                },
                plugins: {
                    legend: { display: true, position: "top" }
                }
            }
        });
    }

    async function loadFarms() {
        const data = await fetchJSON("/api/farms");
        const rows = Array.isArray(data) ? data : (data && data.farms) || [];
        farmSel.innerHTML = '<option value="">Seleccione una finca...</option>';
        rows.forEach(function (f) {
            const opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = f.name || ("Finca " + f.id);
            farmSel.appendChild(opt);
        });
    }

    async function loadFields(farmId) {
        fieldSel.innerHTML = '<option value="">Cargando parcelas...</option>';
        fieldSel.disabled = true;
        const data = await fetchJSON("/api/farms/" + farmId + "/fields");
        const rows = Array.isArray(data) ? data : [];
        fieldSel.innerHTML = '<option value="">Seleccione una parcela...</option>';
        if (rows.length === 0) {
            showEmpty("Esta finca no tiene parcelas registradas.");
            return;
        }
        rows.forEach(function (fld) {
            const opt = document.createElement("option");
            opt.value = fld.id;
            opt.textContent = fld.name || ("Parcela " + fld.id);
            fieldSel.appendChild(opt);
        });
        fieldSel.disabled = false;
    }

    async function loadTrajectory(farmId, fieldId) {
        const url = "/api/farms/" + farmId + "/fields/" + fieldId + "/soil-nutrients?months=12";
        const data = await fetchJSON(url);
        if (!data || !Array.isArray(data.months)) {
            showEmpty("No hay datos de nutrientes para esta parcela.");
            return;
        }
        if (data.months.length === 0) {
            showEmpty("No hay muestras de suelo registradas en los últimos 12 meses.");
            return;
        }

        setTrendPill(nTrend, data.nitrogen_trend);
        setTrendPill(pTrend, data.phosphorus_trend);
        setTrendPill(kTrend, data.potassium_trend);
        setTrendPill(omTrend, data.organic_matter_trend);

        renderChart(data.months);

        content.style.display = "block";
        empty.style.display = "none";
    }

    farmSel.addEventListener("change", function () {
        const farmId = farmSel.value;
        showEmpty("Seleccione una parcela para ver la trayectoria de nutrientes.");
        if (!farmId) {
            fieldSel.innerHTML = '<option value="">Seleccione primero una finca...</option>';
            fieldSel.disabled = true;
            return;
        }
        loadFields(farmId);
    });

    fieldSel.addEventListener("change", function () {
        const farmId = farmSel.value;
        const fieldId = fieldSel.value;
        if (!farmId || !fieldId) {
            showEmpty("Seleccione una parcela para ver la trayectoria de nutrientes.");
            return;
        }
        loadTrajectory(farmId, fieldId);
    });

    loadFarms();
})();
