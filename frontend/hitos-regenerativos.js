(function () {
  const MILESTONE_ICONS = {
    first_organic_treatment: "1",
    first_compost_application: "2",
    first_cover_crop: "3",
    first_carbon_baseline: "4",
    reached_regen_score_60: "5",
    reached_regen_score_80: "6",
    maintained_regen_score_70_for_6_months: "7",
  };

  async function loadFarms() {
    const sel = document.getElementById("hitos-farm-select");
    try {
      const res = await fetch("/api/farms");
      if (!res.ok) return;
      const farms = await res.json();
      farms.forEach(function (f) {
        const opt = document.createElement("option");
        opt.value = f.id;
        opt.textContent = f.name;
        sel.appendChild(opt);
      });
    } catch (_) {}
  }

  async function loadMilestones(farmId) {
    const grid = document.getElementById("hitos-milestones");
    const progressBar = document.getElementById("hitos-progress-bar");
    const progressLabel = document.getElementById("hitos-progress-label");
    const nextHint = document.getElementById("hitos-next-milestone");

    if (!farmId) {
      grid.innerHTML = '<div class="hitos-empty">Selecciona una finca para ver sus hitos regenerativos.</div>';
      progressBar.style.width = "0%";
      progressLabel.textContent = "Progreso: 0 / 7 hitos";
      nextHint.textContent = "";
      return;
    }

    try {
      const res = await fetch("/api/farms/" + farmId + "/regen-milestones");
      if (!res.ok) {
        grid.innerHTML = '<div class="hitos-empty">No se encontraron datos para esta finca.</div>';
        return;
      }
      const data = await res.json();
      var achieved = data.milestones_achieved_count || 0;
      var total = data.milestones ? data.milestones.length : 7;
      var pct = data.progress_to_next_pct || 0;

      progressLabel.textContent = "Progreso: " + achieved + " / " + total + " hitos";
      progressBar.style.width = (total > 0 ? (achieved / total) * 100 : 0) + "%";
      nextHint.textContent = data.next_milestone_es ? "Siguiente: " + data.next_milestone_es : "Todos los hitos alcanzados";

      grid.innerHTML = "";
      (data.milestones || []).forEach(function (m) {
        var card = document.createElement("div");
        card.className = "hitos-card " + (m.achieved ? "achieved" : "locked");
        var icon = MILESTONE_ICONS[m.name] || "?";
        var dateStr = "";
        if (m.achieved && m.achieved_at) {
          dateStr = '<div class="hitos-card-date">Alcanzado: ' + new Date(m.achieved_at).toLocaleDateString("es-MX") + "</div>";
        }
        card.innerHTML =
          '<div class="hitos-card-icon">' + icon + "</div>" +
          '<div class="hitos-card-name">' + (m.description_es || m.name) + "</div>" +
          '<span class="hitos-badge ' + (m.achieved ? "achieved" : "locked") + '">' + (m.achieved ? "Alcanzado" : "Pendiente") + "</span>" +
          dateStr;
        grid.appendChild(card);
      });
    } catch (_) {
      grid.innerHTML = '<div class="hitos-empty">Error al cargar los hitos.</div>';
    }
  }

  document.getElementById("hitos-farm-select").addEventListener("change", function () {
    loadMilestones(this.value);
  });

  loadFarms();
  loadMilestones(null);
})();
