/* Farmer Impact Summary — /impacto-agricultor */

(async function () {
    const farmSelect = document.getElementById("farmSelect");
    const fieldCards = document.getElementById("field-cards");
    const fieldCardsEmpty = document.getElementById("field-cards-empty");

    async function fetchJSON(url) {
        try {
            const r = await fetch(url);
            if (!r.ok) return null;
            return await r.json();
        } catch { return null; }
    }

    function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

    // Load farms
    const farms = await fetchJSON("/api/farms?page_size=100");
    if (farms && farms.items) {
        farms.items.forEach(f => {
            const opt = document.createElement("option");
            opt.value = f.id;
            opt.textContent = f.name;
            farmSelect.appendChild(opt);
        });
    }

    farmSelect.addEventListener("change", async () => {
        const fid = farmSelect.value;
        if (!fid) { resetUI(); return; }
        await loadImpact(fid);
    });

    async function loadImpact(farmId) {
        const data = await fetchJSON("/api/farms/" + farmId + "/farmer-impact");
        if (!data) { resetUI(); return; }

        document.getElementById("stat-dias").textContent = data.days_since_onboard;
        document.getElementById("stat-campos").textContent = data.total_fields;
        document.getElementById("stat-hectareas").textContent = data.total_hectares;
        document.getElementById("stat-recomendaciones").textContent = data.recommendations_received;
        document.getElementById("stat-aplicados").textContent = data.treatments_applied;
        document.getElementById("stat-feedback").textContent = data.feedback_given;
        document.getElementById("stat-mejora").textContent =
            data.avg_health_improvement_pct != null
                ? (data.avg_health_improvement_pct > 0 ? "+" : "") + data.avg_health_improvement_pct + " pts"
                : "Sin datos";
        document.getElementById("stat-ahorro").textContent =
            "$" + data.estimated_savings_mxn.toLocaleString("es-MX");

        renderFieldCards(data.fields);
    }

    function renderFieldCards(fields) {
        fieldCards.innerHTML = "";
        if (!fields || fields.length === 0) {
            fieldCards.innerHTML = '<p style="color:var(--text-secondary);">Sin campos registrados.</p>';
            return;
        }
        fields.forEach(f => {
            const deltaColor = f.health_delta > 0 ? "#22c55e" : f.health_delta < 0 ? "#ef4444" : "#a3a3a3";
            const deltaText = f.health_delta != null
                ? (f.health_delta > 0 ? "+" : "") + f.health_delta + " pts"
                : "Sin datos";
            const card = document.createElement("div");
            card.className = "intel-card";
            card.style.cssText = "padding:1.25rem;border-radius:12px;background:var(--card-bg);border:1px solid var(--border-color);";
            card.innerHTML = [
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">',
                '  <h3 style="margin:0;font-size:1.1rem;color:var(--text-primary);">' + esc(f.field_name) + '</h3>',
                '  <span style="font-size:0.8rem;padding:0.2rem 0.6rem;border-radius:6px;background:var(--bg-secondary);color:var(--text-secondary);">' + esc(f.crop_type || "—") + '</span>',
                '</div>',
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;font-size:0.9rem;">',
                '  <div><span style="color:var(--text-secondary);">Salud inicial:</span> <strong>' + (f.first_score != null ? f.first_score : "—") + '</strong></div>',
                '  <div><span style="color:var(--text-secondary);">Salud actual:</span> <strong>' + (f.latest_score != null ? f.latest_score : "—") + '</strong></div>',
                '  <div><span style="color:var(--text-secondary);">Cambio:</span> <strong style="color:' + deltaColor + ';">' + deltaText + '</strong></div>',
                '  <div><span style="color:var(--text-secondary);">Tratamientos:</span> <strong>' + f.treatments_applied + '</strong></div>',
                '</div>',
            ].join("\n");
            fieldCards.appendChild(card);
        });
    }

    function resetUI() {
        ["stat-dias", "stat-campos", "stat-hectareas", "stat-recomendaciones",
         "stat-aplicados", "stat-feedback", "stat-mejora", "stat-ahorro"
        ].forEach(id => { document.getElementById(id).textContent = "--"; });
        fieldCards.innerHTML = '<p id="field-cards-empty" style="color:var(--text-secondary);">Selecciona una granja para ver el impacto por campo.</p>';
    }
})();
