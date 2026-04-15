(async function () {
    const farmSelect = document.getElementById("escalation-farm-select");
    const kpiStrip = document.getElementById("escalation-kpi-strip");
    const tableContainer = document.getElementById("escalation-table-container");
    const tbody = document.getElementById("escalation-tbody");
    const totalEl = document.getElementById("escalation-total");
    const criticalEl = document.getElementById("escalation-critical-count");
    const emptyState = document.getElementById("escalation-empty");

    async function fetchJSON(url) {
        const r = await fetch(url);
        if (!r.ok) return null;
        return r.json();
    }

    const farms = await fetchJSON("/api/farms");
    if (farms && farms.length) {
        farms.forEach(function (f) {
            const opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = f.name;
            farmSelect.appendChild(opt);
        });
    }

    farmSelect.addEventListener("change", async function () {
        const farmId = farmSelect.value;
        if (!farmId) {
            kpiStrip.style.display = "none";
            tableContainer.style.display = "none";
            emptyState.style.display = "block";
            return;
        }

        const data = await fetchJSON("/api/farms/" + farmId + "/alert-escalations?days=30");
        if (!data || !data.escalations) {
            kpiStrip.style.display = "none";
            tableContainer.style.display = "none";
            emptyState.style.display = "block";
            emptyState.textContent = "No se encontraron escalaciones.";
            return;
        }

        const escalations = data.escalations;
        totalEl.textContent = data.total || escalations.length;

        let criticalCount = 0;
        escalations.forEach(function (e) {
            if (e.severity === "critical") criticalCount++;
        });
        criticalEl.textContent = criticalCount;

        tbody.innerHTML = "";
        escalations.forEach(function (e) {
            const tr = document.createElement("tr");

            var severityClass = "severity-medium";
            if (e.severity === "critical") severityClass = "severity-critical";
            else if (e.severity === "high") severityClass = "severity-high";

            tr.innerHTML =
                "<td>" + (e.field_name || "") + "</td>" +
                "<td>" + (e.alert_type || "") + "</td>" +
                '<td><span class="severity-pill ' + severityClass + '">' + (e.severity || "") + "</span></td>" +
                "<td>" + (e.days_pending != null ? e.days_pending : "") + "</td>" +
                "<td>" + (e.recommended_action_es || "") + "</td>";
            tbody.appendChild(tr);
        });

        emptyState.style.display = "none";
        kpiStrip.style.display = "flex";
        tableContainer.style.display = escalations.length ? "block" : "none";
        if (!escalations.length) {
            emptyState.style.display = "block";
            emptyState.textContent = "No hay escalaciones pendientes.";
        }
    });
})();
