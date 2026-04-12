(function () {
    const farmSel = document.getElementById("dh-farm-select");
    const fieldSel = document.getElementById("dh-field-select");
    const content = document.getElementById("dh-content");
    const empty = document.getElementById("dh-empty");
    const freeCounter = document.getElementById("dh-free-counter");
    const topDisease = document.getElementById("dh-top-disease");
    const recurrenceFlag = document.getElementById("dh-recurrence-flag");
    const recurringList = document.getElementById("dh-recurring");
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

    function showEmpty(msg) {
        content.style.display = "none";
        empty.style.display = "block";
        empty.textContent = msg;
    }

    function renderChart(monthly) {
        const ctx = document.getElementById("dh-chart").getContext("2d");
        if (chart) {
            chart.destroy();
            chart = null;
        }
        const labels = monthly.map(function (m) { return m.month; });
        const counts = monthly.map(function (m) { return m.disease_count || 0; });
        const colors = counts.map(function (c) {
            if (c === 0) return "#4ade80";
            if (c === 1) return "#fbbf24";
            return "#f87171";
        });

        chart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Enfermedades por mes",
                    data: counts,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            afterLabel: function (ctx) {
                                const m = monthly[ctx.dataIndex];
                                if (!m || !m.diseases || m.diseases.length === 0) return "Sin enfermedades";
                                return "Diagnósticos: " + m.diseases.join(", ");
                            }
                        }
                    }
                }
            }
        });
    }

    function renderRecurring(recurring) {
        recurringList.innerHTML = "";
        if (!recurring || recurring.length === 0) {
            const li = document.createElement("li");
            li.className = "empty";
            li.textContent = "Sin enfermedades recurrentes detectadas en este periodo.";
            recurringList.appendChild(li);
            return;
        }
        recurring.forEach(function (name) {
            const li = document.createElement("li");
            li.textContent = name;
            recurringList.appendChild(li);
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

    async function loadHistory(farmId, fieldId) {
        const url = "/api/farms/" + farmId + "/fields/" + fieldId + "/disease-history?months=12";
        const data = await fetchJSON(url);
        if (!data || !Array.isArray(data.monthly)) {
            showEmpty("No hay datos de historial para esta parcela.");
            return;
        }

        freeCounter.textContent = data.months_disease_free != null ? data.months_disease_free : "--";
        const totalMonths = data.total_months_analyzed || 12;
        if (data.months_disease_free === totalMonths) {
            freeCounter.className = "dh-kpi-value";
        } else if (data.months_disease_free >= totalMonths / 2) {
            freeCounter.className = "dh-kpi-value warn";
        } else {
            freeCounter.className = "dh-kpi-value danger";
        }

        topDisease.textContent = data.most_common_disease || "Ninguna";
        recurrenceFlag.textContent = data.recurrence_detected ? "Sí" : "No";
        recurrenceFlag.className = "dh-kpi-value" + (data.recurrence_detected ? " danger" : "");

        renderChart(data.monthly);
        renderRecurring(data.recurring_diseases);

        content.style.display = "block";
        empty.style.display = "none";
    }

    farmSel.addEventListener("change", function () {
        const farmId = farmSel.value;
        showEmpty("Seleccione una parcela para ver el historial.");
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
            showEmpty("Seleccione una parcela para ver el historial.");
            return;
        }
        loadHistory(farmId, fieldId);
    });

    loadFarms();
})();
