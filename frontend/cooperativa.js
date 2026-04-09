/* Cooperativa page — loads cooperative list with dashboard aggregates. */

(async function () {
    var listEl = document.getElementById("coopList");

    function fetchJSON(url) {
        return fetch(url).then(function (r) { return r.ok ? r.json() : null; });
    }

    function healthBadge(score) {
        if (score == null) return '<span class="health-badge" style="opacity:0.5">--</span>';
        var cls = "health-low";
        if (score >= 70) cls = "health-good";
        else if (score >= 50) cls = "health-mid";
        return '<span class="health-badge ' + cls + '">' + score.toFixed(1) + '</span>';
    }

    function esc(s) {
        var d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    var listData = await fetchJSON("/api/cooperatives");
    if (!listData || !listData.data || listData.data.length === 0) {
        listEl.innerHTML = '<div class="empty-state">No hay cooperativas registradas.</div>';
        return;
    }

    var coops = listData.data;
    document.getElementById("totalCoops").textContent = coops.length;

    var totalFarms = 0, totalHectares = 0, healthValues = [], cards = [];

    for (var i = 0; i < coops.length; i++) {
        var coop = coops[i];
        var dash = await fetchJSON("/api/cooperatives/" + coop.id + "/dashboard");
        if (!dash) continue;

        totalFarms += dash.total_farms;
        totalHectares += dash.total_hectares;
        if (dash.avg_health != null) healthValues.push(dash.avg_health);

        var farmItems = "";
        if (dash.farms && dash.farms.length > 0) {
            farmItems = dash.farms.map(function (f) {
                return '<li><span>' + esc(f.name) + ' (' + f.total_hectares.toFixed(1) + ' ha)</span>' + healthBadge(f.avg_health) + '</li>';
            }).join("");
        } else {
            farmItems = '<li style="color:var(--text-muted)">Sin granjas registradas</li>';
        }

        cards.push(
            '<div class="coop-card">' +
            '<h3>' + esc(coop.name) + '</h3>' +
            '<div class="meta">' + esc(coop.state || "") + (coop.contact_name ? " — " + esc(coop.contact_name) : "") + '</div>' +
            '<div style="margin-bottom:0.5rem"><strong>' + dash.total_farms + '</strong> granjas, <strong>' + dash.total_fields + '</strong> parcelas, <strong>' + dash.total_hectares.toFixed(1) + '</strong> ha</div>' +
            '<div style="margin-bottom:0.5rem">Salud promedio: ' + healthBadge(dash.avg_health) + '</div>' +
            '<ul class="farm-list">' + farmItems + '</ul>' +
            '</div>'
        );
    }

    document.getElementById("totalFarms").textContent = totalFarms;
    document.getElementById("totalHectares").textContent = totalHectares.toFixed(1);
    document.getElementById("avgHealth").textContent = healthValues.length > 0
        ? (healthValues.reduce(function (a, b) { return a + b; }, 0) / healthValues.length).toFixed(1)
        : "--";

    listEl.innerHTML = cards.length > 0 ? cards.join("") : '<div class="empty-state">No hay cooperativas registradas.</div>';
})();
