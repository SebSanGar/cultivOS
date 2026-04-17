/* /calendario-campo — field crop calendar page JS (#242) */

(async function () {
    const farmSel = document.getElementById("cal-farm-select");
    const fieldSel = document.getElementById("cal-field-select");
    const yearSel = document.getElementById("cal-year-select");
    const totalEl = document.getElementById("cal-total-events");
    const busiestEl = document.getElementById("cal-busiest-month");
    const gridEl = document.getElementById("cal-grid");
    const expandEl = document.getElementById("cal-expand");

    const MONTH_NAMES_ES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ];

    const currentYear = new Date().getFullYear();
    const yearOptions = [];
    for (let y = currentYear; y >= currentYear - 4; y--) yearOptions.push(y);
    yearSel.innerHTML = yearOptions.map(y => `<option value="${y}">${y}</option>`).join("");
    yearSel.value = String(currentYear);

    async function fetchJSON(url) {
        const r = await fetch(url);
        if (!r.ok) return null;
        return r.json();
    }

    function heatClass(count) {
        if (count <= 0) return "heat-0";
        if (count <= 2) return "heat-1";
        if (count <= 5) return "heat-2";
        if (count <= 10) return "heat-3";
        return "heat-4";
    }

    function resetView() {
        totalEl.textContent = "--";
        busiestEl.textContent = "--";
        gridEl.innerHTML = "";
        expandEl.innerHTML = "";
    }

    const farms = await fetchJSON("/api/farms");
    if (!farms || !farms.length) {
        farmSel.innerHTML = '<option value="">Sin datos</option>';
        return;
    }
    farmSel.innerHTML = '<option value="">Seleccione finca</option>' +
        farms.map(f => `<option value="${f.id}">${esc(f.name)}</option>`).join("");

    farmSel.addEventListener("change", async () => {
        resetView();
        const fid = farmSel.value;
        fieldSel.innerHTML = '<option value="">Cargando...</option>';
        if (!fid) { fieldSel.innerHTML = '<option value="">Seleccione finca</option>'; return; }
        const fields = await fetchJSON(`/api/farms/${fid}/fields`);
        if (!fields || !fields.length) {
            fieldSel.innerHTML = '<option value="">Sin campos</option>';
            return;
        }
        fieldSel.innerHTML = '<option value="">Seleccione campo</option>' +
            fields.map(f => `<option value="${f.id}">${esc(f.name || "Campo " + f.id)}</option>`).join("");
    });

    async function loadCalendar() {
        const fid = farmSel.value;
        const flid = fieldSel.value;
        const year = yearSel.value;
        if (!fid || !flid) { resetView(); return; }

        const data = await fetchJSON(`/api/farms/${fid}/fields/${flid}/calendar?year=${year}`);
        if (!data) {
            resetView();
            gridEl.innerHTML = '<div class="no-data-msg">Sin datos de calendario para este campo y año.</div>';
            return;
        }

        totalEl.textContent = data.total_events;
        busiestEl.textContent = data.busiest_month
            ? MONTH_NAMES_ES[data.busiest_month - 1]
            : "Sin eventos";

        gridEl.innerHTML = data.months.map(m => {
            const cls = heatClass(m.total_events);
            const busiestCls = (data.busiest_month === m.month && m.total_events > 0) ? " busiest" : "";
            return `<div class="month-cell ${cls}${busiestCls}" data-month="${m.month}">
                <div class="name">${esc(m.month_name_es)}</div>
                <div class="count">${m.total_events}</div>
            </div>`;
        }).join("");

        expandEl.innerHTML = "";

        gridEl.querySelectorAll(".month-cell").forEach(cell => {
            cell.addEventListener("click", () => {
                const monthNum = parseInt(cell.dataset.month, 10);
                const m = data.months.find(x => x.month === monthNum);
                if (!m) return;
                expandEl.innerHTML = `<div class="expand-panel">
                    <h3>${esc(m.month_name_es)} — Desglose</h3>
                    <div class="breakdown-row"><span>Salud (HealthScore)</span><span>${m.health_scores}</span></div>
                    <div class="breakdown-row"><span>Tratamientos</span><span>${m.treatments}</span></div>
                    <div class="breakdown-row"><span>Observaciones</span><span>${m.observations}</span></div>
                    <div class="breakdown-row"><span>Prácticas TEK</span><span>${m.tek_practices}</span></div>
                </div>`;
            });
        });
    }

    fieldSel.addEventListener("change", loadCalendar);
    yearSel.addEventListener("change", loadCalendar);

    function esc(s) {
        if (s === null || s === undefined) return "";
        const d = document.createElement("div");
        d.textContent = String(s);
        return d.innerHTML;
    }
})();
