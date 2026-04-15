(function () {
  var farms = [];

  async function loadFarms() {
    var sel = document.getElementById("cn-farm-select");
    try {
      var res = await fetch("/api/farms");
      if (!res.ok) return;
      farms = await res.json();
      farms.forEach(function (f) {
        var opt = document.createElement("option");
        opt.value = f.id;
        opt.textContent = f.name;
        sel.appendChild(opt);
      });
    } catch (e) { /* ignore */ }
  }

  async function loadFields(farmId) {
    var sel = document.getElementById("cn-field-select");
    sel.innerHTML = '<option value="">-- Seleccionar parcela --</option>';
    sel.disabled = true;
    if (!farmId) return;
    try {
      var res = await fetch("/api/farms/" + farmId + "/fields");
      if (!res.ok) return;
      var fields = await res.json();
      fields.forEach(function (f) {
        var opt = document.createElement("option");
        opt.value = f.id;
        opt.textContent = f.name;
        sel.appendChild(opt);
      });
      sel.disabled = false;
    } catch (e) { /* ignore */ }
  }

  function pillClass(strength) {
    var map = {
      strong: "cn-pill-strong",
      moderate: "cn-pill-moderate",
      weak: "cn-pill-weak",
      none: "cn-pill-none",
      insufficient_data: "cn-pill-insufficient"
    };
    return map[strength] || "cn-pill-none";
  }

  function strengthLabel(strength) {
    var map = {
      strong: "Fuerte",
      moderate: "Moderada",
      weak: "Debil",
      none: "Ninguna",
      insufficient_data: "Datos insuficientes"
    };
    return map[strength] || strength;
  }

  async function loadCorrelation(farmId, fieldId) {
    var rVal = document.getElementById("cn-r-value");
    var pill = document.getElementById("cn-strength-pill");
    var sampleEl = document.getElementById("cn-sample-size");
    var interp = document.getElementById("cn-interpretation");

    if (!farmId || !fieldId) {
      rVal.textContent = "--";
      pill.textContent = "--";
      pill.className = "cn-pill cn-pill-none";
      sampleEl.textContent = "--";
      interp.textContent = "Seleccione una finca y parcela para ver la correlacion NDVI-salud.";
      return;
    }

    try {
      var res = await fetch("/api/farms/" + farmId + "/fields/" + fieldId + "/ndvi-health-correlation?days=90");
      if (!res.ok) {
        interp.textContent = "Error al cargar datos.";
        return;
      }
      var data = await res.json();

      if (data.strength === "insufficient_data") {
        rVal.textContent = "--";
        pill.textContent = strengthLabel(data.strength);
        pill.className = "cn-pill " + pillClass(data.strength);
        sampleEl.textContent = data.sample_size;
        interp.textContent = data.interpretation_es;
        return;
      }

      rVal.textContent = data.correlation !== null ? data.correlation.toFixed(3) : "--";
      pill.textContent = strengthLabel(data.strength);
      pill.className = "cn-pill " + pillClass(data.strength);
      sampleEl.textContent = data.sample_size;
      interp.textContent = data.interpretation_es;
    } catch (e) {
      interp.textContent = "Error de conexion.";
    }
  }

  document.getElementById("cn-farm-select").addEventListener("change", function () {
    loadFields(this.value);
    loadCorrelation(null, null);
  });

  document.getElementById("cn-field-select").addEventListener("change", function () {
    var farmId = document.getElementById("cn-farm-select").value;
    loadCorrelation(farmId, this.value);
  });

  loadFarms();
})();
