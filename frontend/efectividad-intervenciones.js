(async function () {
    const farmSelect = document.getElementById("ei-farm-select");
    const fieldSelect = document.getElementById("ei-field-select");
    let donutChart = null;

    async function fetchJSON(url) {
        const r = await fetch(url);
        if (!r.ok) return null;
        return r.json();
    }

    async function loadFarms() {
        const farms = await fetchJSON("/api/farms");
        if (!farms) return;
        farms.forEach(function (f) {
            const opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = f.name;
            farmSelect.appendChild(opt);
        });
    }

    farmSelect.addEventListener("change", async function () {
        fieldSelect.innerHTML = '<option value="">-- Seleccionar parcela --</option>';
        fieldSelect.disabled = true;
        clearDisplay();
        const farmId = farmSelect.value;
        if (!farmId) return;
        const fields = await fetchJSON("/api/farms/" + farmId + "/fields");
        if (!fields) return;
        fields.forEach(function (f) {
            const opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = f.name;
            fieldSelect.appendChild(opt);
        });
        fieldSelect.disabled = false;
    });

    fieldSelect.addEventListener("change", async function () {
        const farmId = farmSelect.value;
        const fieldId = fieldSelect.value;
        if (!farmId || !fieldId) { clearDisplay(); return; }
        const data = await fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/intervention-effectiveness?days=180");
        if (!data) { clearDisplay(); return; }
        renderData(data);
    });

    function clearDisplay() {
        document.getElementById("ei-effectiveness-rate").textContent = "--";
        document.getElementById("ei-treatments-evaluated").textContent = "--";
        document.getElementById("ei-best-name").textContent = "--";
        document.getElementById("ei-best-delta").textContent = "";
        document.getElementById("ei-worst-name").textContent = "--";
        document.getElementById("ei-worst-delta").textContent = "";
        document.getElementById("ei-recommendation").textContent = "Seleccione una finca y parcela para ver la efectividad de intervenciones.";
        if (donutChart) { donutChart.destroy(); donutChart = null; }
    }

    function renderData(d) {
        document.getElementById("ei-effectiveness-rate").textContent = d.effectiveness_rate_pct.toFixed(1) + "%";
        document.getElementById("ei-treatments-evaluated").textContent = d.treatments_evaluated;

        if (d.best_treatment) {
            document.getElementById("ei-best-name").textContent = d.best_treatment.name;
            document.getElementById("ei-best-delta").textContent = "+" + d.best_treatment.avg_delta.toFixed(1) + " salud";
        } else {
            document.getElementById("ei-best-name").textContent = "Sin datos";
        }

        if (d.worst_treatment) {
            document.getElementById("ei-worst-name").textContent = d.worst_treatment.name;
            document.getElementById("ei-worst-delta").textContent = d.worst_treatment.avg_delta.toFixed(1) + " salud";
        } else {
            document.getElementById("ei-worst-name").textContent = "Sin datos";
        }

        document.getElementById("ei-recommendation").textContent = d.recommendation_es;

        if (donutChart) { donutChart.destroy(); donutChart = null; }
        var ctx = document.getElementById("ei-donut").getContext("2d");
        donutChart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["Efectivo", "Neutral", "Contraproducente"],
                datasets: [{
                    data: [d.effective_count, d.neutral_count, d.counterproductive_count],
                    backgroundColor: ["#4caf50", "#ff9800", "#f44336"]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { labels: { color: "#e0e0e0" } }
                }
            }
        });
    }

    await loadFarms();
})();
