/* /alertas-clima — Field weather alert history JS (#241)
   Consumes GET /api/farms/{farm_id}/fields/{field_id}/weather-alert-history?days= */

(async function () {
    const farmSel = document.getElementById("ac-farm-select");
    const fieldSel = document.getElementById("ac-field-select");
    const daysSel = document.getElementById("ac-days-select");
    const totalEl = document.getElementById("ac-total-alerts");
    const mostFreqEl = document.getElementById("ac-most-frequent");
    const trendPill = document.getElementById("ac-trend-pill");
    const perMonthEl = document.getElementById("ac-per-month");
    const canvas = document.getElementById("ac-chart");
    const noData = document.getElementById("ac-no-data");

    const TYPE_LABEL = {
        helada: "Helada",
        sequia: "Sequía",
        lluvia: "Lluvia",
        viento: "Viento",
        calor: "Calor",
    };

    const TREND_LABEL = {
        rising: "Creciente",
        falling: "Descendente",
        stable: "Estable",
        none: "Sin datos",
    };

    let chart = null;

    async function fetchJSON(url) {
        try {
            const r = await fetch(url);
            if (!r.ok) return null;
            return await r.json();
        } catch (_) {
            return null;
        }
    }

    // Load farms
    const farms = await fetchJSON("/api/farms");
    if (!farms || !farms.length) {
        farmSel.innerHTML = '<option value="">Sin fincas</option>';
        return;
    }
    farmSel.innerHTML = '<option value="">Seleccionar finca...</option>' +
        farms.map(f => `<option value="${f.id}">${esc(f.name)}</option>`).join("");

    farmSel.addEventListener("change", async () => {
        const fid = farmSel.value;
        fieldSel.innerHTML = '<option value="">Cargando...</option>';
        resetKPIs();
        if (!fid) {
            fieldSel.innerHTML = '<option value="">Seleccionar campo...</option>';
            return;
        }
        const fields = await fetchJSON(`/api/farms/${fid}/fields`);
        if (!fields || !fields.length) {
            fieldSel.innerHTML = '<option value="">Sin campos</option>';
            return;
        }
        fieldSel.innerHTML = '<option value="">Seleccionar campo...</option>' +
            fields.map(f => `<option value="${f.id}">${esc(f.name || "Campo " + f.id)}</option>`).join("");
    });

    fieldSel.addEventListener("change", loadHistory);
    daysSel.addEventListener("change", loadHistory);

    async function loadHistory() {
        const fid = farmSel.value;
        const flid = fieldSel.value;
        const days = daysSel.value || "90";
        if (!fid || !flid) return;

        const data = await fetchJSON(`/api/farms/${fid}/fields/${flid}/weather-alert-history?days=${days}`);
        if (!data) {
            resetKPIs();
            noData.textContent = "Sin datos de alertas climáticas para este campo.";
            noData.style.display = "block";
            return;
        }
        noData.style.display = "none";

        totalEl.textContent = data.total_alerts;
        mostFreqEl.textContent = data.most_frequent_type ? (TYPE_LABEL[data.most_frequent_type] || data.most_frequent_type) : "—";
        perMonthEl.textContent = (data.alerts_per_month_avg || 0).toFixed(1);

        const trend = data.trend || "stable";
        trendPill.textContent = TREND_LABEL[trend] || trend;
        trendPill.className = "pill " + trend;

        renderChart(data.by_type || []);
    }

    function renderChart(rows) {
        const labels = rows.map(r => TYPE_LABEL[r.alert_type] || r.alert_type);
        const counts = rows.map(r => r.count);
        const colors = rows.map(r => r.dominant_severity === "critica" ? "#ef4444" : "#f59e0b");

        if (chart) chart.destroy();
        chart = new Chart(canvas.getContext("2d"), {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Alertas",
                    data: counts,
                    backgroundColor: colors,
                    borderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#9ca3af" }, grid: { display: false } },
                    y: { beginAtZero: true, ticks: { color: "#9ca3af", stepSize: 1 }, grid: { color: "#2a2d3a" } },
                },
            },
        });
    }

    function resetKPIs() {
        totalEl.textContent = "--";
        mostFreqEl.textContent = "--";
        perMonthEl.textContent = "--";
        trendPill.textContent = "--";
        trendPill.className = "pill stable";
        if (chart) { chart.destroy(); chart = null; }
    }

    function esc(s) {
        if (s == null) return "";
        const d = document.createElement("div");
        d.textContent = String(s);
        return d.innerHTML;
    }
})();
