/* Reporte Anual — farm annual report (#232)
   Consumes GET /api/farms/{farm_id}/annual-report?year= */

(function () {
    const farmSelect = document.getElementById("anual-farm-select");
    const yearSelect = document.getElementById("anual-year-select");
    const bestField = document.getElementById("anual-best-field");
    const mostImproved = document.getElementById("anual-most-improved");
    const co2e = document.getElementById("anual-co2e");
    const treatments = document.getElementById("anual-treatments");
    const tbody = document.querySelector("#anual-field-table tbody");

    // Populate year selector (current year and 2 prior)
    const currentYear = new Date().getFullYear();
    for (let y = currentYear; y >= currentYear - 2; y--) {
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = y;
        yearSelect.appendChild(opt);
    }
    yearSelect.value = currentYear;

    // Load farms
    fetch("/api/farms")
        .then(r => r.json())
        .then(farms => {
            (farms || []).forEach(f => {
                const opt = document.createElement("option");
                opt.value = f.id;
                opt.textContent = f.name || "Finca " + f.id;
                farmSelect.appendChild(opt);
            });
        })
        .catch(() => {});

    function loadReport() {
        const farmId = farmSelect.value;
        const year = yearSelect.value;
        if (!farmId || !year) return;

        fetch("/api/farms/" + farmId + "/annual-report?year=" + year)
            .then(r => r.json())
            .then(data => {
                bestField.textContent = data.best_field || "--";
                mostImproved.textContent = data.most_improved_field || "--";
                co2e.textContent = data.total_co2e_sequestered_t != null
                    ? data.total_co2e_sequestered_t.toFixed(2) : "--";
                treatments.textContent = data.treatments_applied_total != null
                    ? data.treatments_applied_total : "--";

                tbody.innerHTML = "";
                const fields = data.fields || [];
                if (fields.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No hay datos para este periodo.</td></tr>';
                    return;
                }
                fields.forEach(f => {
                    const tr = document.createElement("tr");
                    tr.innerHTML =
                        "<td>" + (f.field_name || "Campo " + f.field_id) + "</td>" +
                        "<td>" + fmtNum(f.avg_health) + "</td>" +
                        "<td>" + fmtNum(f.min_health) + "</td>" +
                        "<td>" + fmtNum(f.max_health) + "</td>" +
                        "<td>" + trendPill(f.ndvi_trend) + "</td>" +
                        "<td>" + fmtDelta(f.soil_ph_delta) + "</td>" +
                        "<td>" + fmtNum(f.regen_score) + "</td>";
                    tbody.appendChild(tr);
                });
            })
            .catch(() => {
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Error al cargar datos.</td></tr>';
            });
    }

    function fmtNum(v) {
        return v != null ? v.toFixed(1) : "--";
    }

    function fmtDelta(v) {
        if (v == null) return "--";
        var sign = v >= 0 ? "+" : "";
        return sign + v.toFixed(2);
    }

    function trendPill(ndvi_trend) {
        if (ndvi_trend == null) return '<span class="trend-pill stable">--</span>';
        var cls = ndvi_trend > 0 ? "up" : ndvi_trend < 0 ? "down" : "stable";
        var label = ndvi_trend > 0 ? "Subiendo" : ndvi_trend < 0 ? "Bajando" : "Estable";
        return '<span class="trend-pill ' + cls + '">' + label + "</span>";
    }

    farmSelect.addEventListener("change", loadReport);
    yearSelect.addEventListener("change", loadReport);
})();
