(function () {
    const sel = document.getElementById("diversity-coop-select");
    const content = document.getElementById("diversity-content");
    const empty = document.getElementById("diversity-empty");
    let barChart = null;

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
        return n.toFixed(digits == null ? 2 : digits);
    }

    async function loadCoops() {
        const data = await fetchJSON("/api/cooperatives");
        if (!data) return;
        const list = Array.isArray(data) ? data : data.cooperatives || [];
        list.forEach(function (c) {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.textContent = c.name || "Cooperativa " + c.id;
            sel.appendChild(opt);
        });
    }

    async function loadDiversity(coopId) {
        const data = await fetchJSON("/api/cooperatives/" + coopId + "/crop-diversity");
        if (!data) {
            content.style.display = "none";
            empty.style.display = "";
            empty.textContent = "Sin datos de diversidad para esta cooperativa.";
            return;
        }

        content.style.display = "";
        empty.style.display = "none";

        document.getElementById("diversity-shannon").textContent = fmt(data.shannon_index);

        renderBarChart(data.top_crops || []);
        renderFarmTable(data.farms || []);
    }

    function renderBarChart(topCrops) {
        const ctx = document.getElementById("diversity-bar-chart");
        if (barChart) barChart.destroy();

        const labels = topCrops.map(function (c) { return c.crop_type; });
        const values = topCrops.map(function (c) { return c.hectares; });
        const pcts = topCrops.map(function (c) { return c.pct; });

        barChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Hectareas",
                    data: values,
                    backgroundColor: ["#4ade80", "#60a5fa", "#fbbf24", "#f87171", "#a78bfa"],
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function (item) {
                                var p = pcts[item.dataIndex];
                                return item.formattedValue + " ha (" + (p != null ? p.toFixed(1) : "?") + "%)";
                            }
                        }
                    },
                    legend: { display: false }
                },
                scales: {
                    x: { title: { display: true, text: "Hectareas" } }
                }
            }
        });
    }

    function renderFarmTable(farms) {
        var tbody = document.getElementById("diversity-farm-table");
        tbody.innerHTML = "";
        farms.forEach(function (f) {
            var tr = document.createElement("tr");
            tr.innerHTML =
                "<td>" + (f.farm_name || "Finca " + f.farm_id) + "</td>" +
                "<td>" + f.distinct_crops + "</td>" +
                "<td>" + (f.crop_types || []).join(", ") + "</td>";
            tbody.appendChild(tr);
        });
    }

    sel.addEventListener("change", function () {
        if (!sel.value) {
            content.style.display = "none";
            empty.style.display = "";
            empty.textContent = "Seleccione una cooperativa para ver la diversidad de cultivos.";
            return;
        }
        loadDiversity(sel.value);
    });

    loadCoops();
})();
