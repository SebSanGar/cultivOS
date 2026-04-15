(async function () {
    var farmSelect = document.getElementById("freshness-farm-select");
    var content = document.getElementById("freshness-content");
    var emptyMsg = document.getElementById("freshness-empty");
    var staleCount = document.getElementById("freshness-stale-count");
    var gridBody = document.getElementById("freshness-grid-body");

    async function fetchJSON(url) {
        var r = await fetch(url);
        if (!r.ok) return null;
        return r.json();
    }

    function freshnessClass(days) {
        if (days === null || days === undefined) return "fresh-red";
        if (days <= 7) return "fresh-green";
        if (days <= 30) return "fresh-amber";
        return "fresh-red";
    }

    function formatDays(days) {
        if (days === null || days === undefined) return "Sin datos";
        return days + "d";
    }

    function renderGrid(data) {
        gridBody.innerHTML = "";
        if (!data || !data.fields || data.fields.length === 0) {
            content.style.display = "none";
            emptyMsg.textContent = "No hay datos de sensores para esta finca.";
            emptyMsg.style.display = "block";
            return;
        }
        content.style.display = "block";
        emptyMsg.style.display = "none";

        var totalStale = 0;
        data.fields.forEach(function (f) {
            totalStale += f.stale_sensors.length;
        });
        staleCount.textContent = totalStale;

        data.fields.forEach(function (f) {
            var row = document.createElement("tr");
            row.innerHTML =
                "<td>Campo #" + f.field_id + "</td>" +
                "<td>" + f.crop_type + "</td>" +
                '<td class="' + freshnessClass(f.ndvi_days_ago) + '">' + formatDays(f.ndvi_days_ago) + "</td>" +
                '<td class="' + freshnessClass(f.soil_days_ago) + '">' + formatDays(f.soil_days_ago) + "</td>" +
                '<td class="' + freshnessClass(f.health_days_ago) + '">' + formatDays(f.health_days_ago) + "</td>" +
                '<td class="' + freshnessClass(f.weather_days_ago) + '">' + formatDays(f.weather_days_ago) + "</td>" +
                "<td>" + (f.stale_sensors.length > 0 ? '<span class="stale-badge">' + f.stale_sensors.length + "</span>" : "0") + "</td>";
            gridBody.appendChild(row);
        });
    }

    var farms = await fetchJSON("/api/farms");
    if (farms) {
        farms.forEach(function (f) {
            var opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = f.name;
            farmSelect.appendChild(opt);
        });
    }

    farmSelect.addEventListener("change", async function () {
        var farmId = farmSelect.value;
        if (!farmId) {
            content.style.display = "none";
            emptyMsg.textContent = "Seleccione una finca para ver la frescura de sensores.";
            emptyMsg.style.display = "block";
            return;
        }
        var data = await fetchJSON("/api/farms/" + farmId + "/sensor-freshness");
        renderGrid(data);
    });
})();
