/* Benchmark Regional — /benchmark-regional (#235)
   Consumes GET /api/farms/{farm_id}/regional-benchmark */

(async function () {
    const farmSelect = document.getElementById("bench-farm-select");
    const content = document.getElementById("bench-content");
    const noData = document.getElementById("bench-no-data");

    // Load farms
    try {
        const res = await fetch("/api/farms");
        if (res.ok) {
            const farms = await res.json();
            farms.forEach(function (f) {
                const o = document.createElement("option");
                o.value = f.id;
                o.textContent = f.name;
                farmSelect.appendChild(o);
            });
        }
    } catch (_) { /* ignore */ }

    farmSelect.addEventListener("change", loadBenchmark);

    async function loadBenchmark() {
        const farmId = farmSelect.value;
        content.style.display = "none";
        noData.style.display = "none";

        if (!farmId) return;

        try {
            const res = await fetch("/api/farms/" + farmId + "/regional-benchmark");
            if (!res.ok) {
                noData.style.display = "block";
                return;
            }
            const d = await res.json();

            if (d.own_avg_health === null || d.peer_farm_count === 0) {
                noData.textContent = "Sin datos suficientes. Esta finca es la unica en su estado o no tiene datos de salud.";
                noData.style.display = "block";
                return;
            }

            // Percentile
            document.getElementById("bench-percentile").textContent = Math.round(d.percentile_rank);

            // Ring color
            const ring = document.getElementById("bench-percentile-ring");
            if (d.percentile_rank >= 70) ring.style.borderColor = "var(--green)";
            else if (d.percentile_rank >= 40) ring.style.borderColor = "var(--amber)";
            else ring.style.borderColor = "var(--red)";

            // Better than badge
            const badge = document.getElementById("bench-better-pct");
            badge.textContent = "Mejor que el " + Math.round(d.better_than_pct) + "% de fincas en el estado";
            badge.className = "badge";
            if (d.better_than_pct >= 70) badge.classList.add("badge-green");
            else if (d.better_than_pct >= 40) badge.classList.add("badge-amber");
            else badge.classList.add("badge-red");

            // Bars
            var own = d.own_avg_health != null ? d.own_avg_health : 0;
            var reg = d.state_avg_health != null ? d.state_avg_health : 0;

            document.getElementById("bench-own-bar").style.width = own + "%";
            document.getElementById("bench-own-value").textContent = own.toFixed(1);
            document.getElementById("bench-regional-bar").style.width = reg + "%";
            document.getElementById("bench-regional-value").textContent = reg.toFixed(1);

            // Info
            document.getElementById("bench-state").textContent = d.state || "--";
            document.getElementById("bench-peer-count").textContent = d.peer_farm_count;

            content.style.display = "block";
        } catch (_) {
            noData.style.display = "block";
        }
    }
})();
