(function () {
    const sel = document.getElementById("coop-progress-select");
    const content = document.getElementById("coop-progress-content");
    const empty = document.getElementById("coop-progress-empty");
    const trendEl = document.getElementById("coop-progress-trend");
    const tbody = document.getElementById("coop-progress-deltas");
    let chart = null;

    async function fetchJSON(url) {
        try {
            const r = await fetch(url);
            if (!r.ok) return null;
            return await r.json();
        } catch (e) {
            return null;
        }
    }

    function fmt(value, digits) {
        if (value === null || value === undefined) return "--";
        const n = Number(value);
        if (!isFinite(n)) return "--";
        return n.toFixed(digits == null ? 1 : digits);
    }

    function setTrend(level) {
        const value = (level || "stable").toLowerCase();
        const valid = ["improving", "stable", "declining"].includes(value) ? value : "stable";
        trendEl.className = "prog-pill " + valid;
        const labels = { improving: "Mejorando", stable: "Estable", declining: "En declive" };
        trendEl.textContent = "Tendencia: " + (labels[valid] || "Estable");
    }

    function deltaCell(value) {
        const n = Number(value);
        if (!isFinite(n) || n === 0) {
            return '<span class="prog-delta flat">0.0</span>';
        }
        if (n > 0) {
            return '<span class="prog-delta up">+' + n.toFixed(1) + '</span>';
        }
        return '<span class="prog-delta down">' + n.toFixed(1) + '</span>';
    }

    function renderChart(months) {
        const ctx = document.getElementById("coop-progress-chart").getContext("2d");
        if (chart) {
            chart.destroy();
            chart = null;
        }
        const labels = months.map(function (m) { return m.month; });
        const healthData = months.map(function (m) { return m.avg_health; });
        const regenData = months.map(function (m) { return m.regen_score_avg; });

        chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Salud Promedio",
                        data: healthData,
                        borderColor: "#4ade80",
                        backgroundColor: "rgba(74, 222, 128, 0.15)",
                        tension: 0.3,
                        fill: false
                    },
                    {
                        label: "Puntaje Regenerativo",
                        data: regenData,
                        borderColor: "#fbbf24",
                        backgroundColor: "rgba(251, 191, 36, 0.15)",
                        tension: 0.3,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, suggestedMax: 100 }
                },
                plugins: {
                    legend: { position: "bottom" }
                }
            }
        });
    }

    function renderTable(months) {
        tbody.innerHTML = "";
        months.forEach(function (m) {
            const row = document.createElement("tr");
            row.innerHTML =
                "<td>" + m.month + "</td>" +
                "<td>" + fmt(m.avg_health, 1) + "</td>" +
                "<td>" + fmt(m.regen_score_avg, 1) + "</td>" +
                "<td>" + deltaCell(m.mom_delta) + "</td>" +
                "<td>" + (m.total_treatments != null ? m.total_treatments : 0) + "</td>";
            tbody.appendChild(row);
        });
    }

    async function loadCoopList() {
        const data = await fetchJSON("/api/cooperatives");
        const rows = Array.isArray(data) ? data : (data && data.cooperatives) || [];
        sel.innerHTML = '<option value="">Seleccione una cooperativa...</option>';
        rows.forEach(function (c) {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.textContent = c.name || ("Cooperativa " + c.id);
            sel.appendChild(opt);
        });
    }

    async function loadProgress(coopId) {
        if (!coopId) {
            content.style.display = "none";
            empty.style.display = "block";
            empty.textContent = "Seleccione una cooperativa para ver el progreso mensual.";
            return;
        }
        const data = await fetchJSON("/api/cooperatives/" + coopId + "/monthly-progress?months=12");
        if (!data || !Array.isArray(data.months) || data.months.length === 0) {
            content.style.display = "none";
            empty.style.display = "block";
            empty.textContent = "No hay datos mensuales disponibles para esta cooperativa.";
            return;
        }

        setTrend(data.overall_trend);
        renderChart(data.months);
        renderTable(data.months);

        content.style.display = "block";
        empty.style.display = "none";
    }

    sel.addEventListener("change", function () { loadProgress(sel.value); });
    loadCoopList();
})();
