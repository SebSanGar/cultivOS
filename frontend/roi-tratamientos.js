(function () {
    const farmSel = document.getElementById("roi-farm-select");
    const content = document.getElementById("roi-content");
    const empty = document.getElementById("roi-empty");
    const bestEl = document.getElementById("roi-best-treatment");
    const worstEl = document.getElementById("roi-worst-treatment");
    const pillEl = document.getElementById("roi-recommendation-pill");
    const tbody = document.getElementById("roi-table-body");

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

    function pillClassFor(recommendationEs) {
        const t = (recommendationEs || "").toLowerCase();
        if (t.indexOf("excelente") !== -1) return "excelente";
        if (t.indexOf("buena") !== -1) return "buena";
        if (t.indexOf("cuestionable") !== -1) return "cuestionable";
        if (t.indexOf("sin mejora") !== -1 || t.indexOf("sin-mejora") !== -1) return "sin-mejora";
        return "cuestionable";
    }

    function fmtNumber(n, digits) {
        if (n === null || n === undefined) return "—";
        return Number(n).toFixed(digits);
    }

    function fmtCost(n) {
        if (n === null || n === undefined) return "—";
        return "$" + Number(n).toLocaleString("es-MX");
    }

    function dominantRecommendation(items) {
        // Pick the recommendation of the best_roi item when available,
        // otherwise fall back to the most positive tier among items.
        const priority = { excelente: 4, buena: 3, cuestionable: 2, "sin-mejora": 1 };
        let bestCls = "cuestionable";
        let bestText = "Sin datos";
        for (const it of items) {
            const cls = pillClassFor(it.recommendation_es);
            if (priority[cls] > priority[bestCls]) {
                bestCls = cls;
                bestText = it.recommendation_es;
            }
        }
        return { cls: bestCls, text: bestText };
    }

    function renderTable(items) {
        tbody.innerHTML = "";
        items.forEach(function (it) {
            const tr = document.createElement("tr");
            const cls = pillClassFor(it.recommendation_es);
            tr.innerHTML =
                "<td>" + (it.treatment_type || "—") + "</td>" +
                "<td>" + (it.count || 0) + "</td>" +
                "<td>" + fmtCost(it.total_cost_mxn) + "</td>" +
                "<td>" + fmtNumber(it.avg_health_delta, 2) + "</td>" +
                "<td>" + fmtNumber(it.cost_per_health_point, 1) + "</td>" +
                '<td><span class="roi-pill ' + cls + '">' + (it.recommendation_es || "—") + "</span></td>";
            tbody.appendChild(tr);
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

    async function loadRoi(farmId) {
        const data = await fetchJSON("/api/farms/" + farmId + "/treatment-roi?days=90");
        if (!data || !Array.isArray(data.treatments)) {
            showEmpty("No hay datos de ROI para esta finca.");
            return;
        }
        if (data.treatments.length === 0) {
            showEmpty("No se registraron tratamientos en los últimos 90 días.");
            return;
        }

        bestEl.textContent = data.best_roi_treatment || "—";
        worstEl.textContent = data.worst_roi_treatment || "—";

        const dom = dominantRecommendation(data.treatments);
        pillEl.textContent = dom.text;
        pillEl.className = "roi-pill " + dom.cls;

        renderTable(data.treatments);

        content.style.display = "block";
        empty.style.display = "none";
    }

    farmSel.addEventListener("change", function () {
        const farmId = farmSel.value;
        if (!farmId) {
            showEmpty("Seleccione una finca para ver el ROI por tratamiento.");
            return;
        }
        loadRoi(farmId);
    });

    loadFarms();
})();
