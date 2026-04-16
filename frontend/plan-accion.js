/* Plan de Accion Semanal — /plan-accion (#239)
   Consumes GET /api/farms/{farm_id}/fields/{field_id}/action-plan?days=7
*/

(function () {
  const farmSel = document.getElementById("accion-farm-select");
  const fieldSel = document.getElementById("accion-field-select");
  const countEl = document.getElementById("accion-count");
  const cardsEl = document.getElementById("accion-cards");

  async function fetchJSON(url) {
    const r = await fetch(url);
    if (!r.ok) return null;
    return r.json();
  }

  async function loadFarms() {
    const farms = await fetchJSON("/api/farms");
    if (!farms) return;
    farms.forEach(function (f) {
      const o = document.createElement("option");
      o.value = f.id;
      o.textContent = f.name;
      farmSel.appendChild(o);
    });
  }

  async function loadFields(farmId) {
    fieldSel.innerHTML = '<option value="">Seleccionar Campo...</option>';
    fieldSel.disabled = true;
    if (!farmId) return;
    const fields = await fetchJSON("/api/farms/" + farmId + "/fields");
    if (!fields) return;
    fields.forEach(function (f) {
      const o = document.createElement("option");
      o.value = f.id;
      o.textContent = f.name || "Campo " + f.id;
      fieldSel.appendChild(o);
    });
    fieldSel.disabled = false;
  }

  function priorityOrder(p) {
    if (p === "high") return 0;
    if (p === "medium") return 1;
    return 2;
  }

  function renderActions(data) {
    if (!data || !data.actions || data.actions.length === 0) {
      countEl.textContent = "0";
      cardsEl.innerHTML = '<div class="empty-state">No hay acciones pendientes para este campo.</div>';
      return;
    }
    const actions = data.actions.slice().sort(function (a, b) {
      return priorityOrder(a.priority) - priorityOrder(b.priority);
    });
    countEl.textContent = actions.length;
    cardsEl.innerHTML = "";
    actions.forEach(function (item) {
      const card = document.createElement("div");
      card.className = "action-card " + item.priority;

      const badge = document.createElement("span");
      badge.className = "priority-badge " + item.priority;
      badge.textContent = item.priority === "high" ? "Alta" : item.priority === "medium" ? "Media" : "Baja";

      const body = document.createElement("div");
      body.className = "action-body";

      const text = document.createElement("p");
      text.className = "action-text";
      text.textContent = item.action_es;

      const source = document.createElement("span");
      source.className = "action-source";
      source.textContent = item.source_es + " ";

      const catBadge = document.createElement("span");
      catBadge.className = "source-badge " + item.category;
      catBadge.textContent = item.category === "stress" ? "Estres" : item.category === "treatment" ? "Tratamiento" : "TEK";

      source.appendChild(catBadge);
      body.appendChild(text);
      body.appendChild(source);
      card.appendChild(badge);
      card.appendChild(body);
      cardsEl.appendChild(card);
    });
  }

  async function loadActionPlan(farmId, fieldId) {
    cardsEl.innerHTML = '<div class="empty-state">Cargando...</div>';
    const data = await fetchJSON("/api/farms/" + farmId + "/fields/" + fieldId + "/action-plan?days=7");
    renderActions(data);
  }

  farmSel.addEventListener("change", function () {
    loadFields(farmSel.value);
    countEl.textContent = "--";
    cardsEl.innerHTML = '<div class="empty-state">Selecciona un campo para ver el plan de accion.</div>';
  });

  fieldSel.addEventListener("change", function () {
    if (farmSel.value && fieldSel.value) {
      loadActionPlan(farmSel.value, fieldSel.value);
    }
  });

  loadFarms();
})();
