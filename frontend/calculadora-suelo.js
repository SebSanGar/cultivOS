/* Calculadora de enmiendas de suelo — calls POST /api/intel/soil-amendment */

function esc(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

async function calcular() {
    var btn = document.getElementById("btnCalc");
    btn.disabled = true;
    btn.textContent = "Calculando...";

    var body = {
        current_ph: parseFloat(document.getElementById("currentPh").value),
        target_ph: parseFloat(document.getElementById("targetPh").value),
        current_om_pct: parseFloat(document.getElementById("currentOm").value),
        target_om_pct: parseFloat(document.getElementById("targetOm").value),
        current_n_ppm: parseFloat(document.getElementById("currentN").value),
        target_n_ppm: parseFloat(document.getElementById("targetN").value),
        current_p_ppm: parseFloat(document.getElementById("currentP").value),
        target_p_ppm: parseFloat(document.getElementById("targetP").value),
        current_k_ppm: parseFloat(document.getElementById("currentK").value),
        target_k_ppm: parseFloat(document.getElementById("targetK").value),
    };

    try {
        var resp = await fetch("/api/intel/soil-amendment", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body),
        });
        if (!resp.ok) {
            alert("Error: " + resp.status);
            return;
        }
        var data = await resp.json();
        renderResults(data);
    } catch (e) {
        alert("Error de conexion: " + e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = "Calcular Enmiendas";
    }
}

function renderResults(data) {
    var container = document.getElementById("resultados");
    container.style.display = "block";

    document.getElementById("summaryBox").innerHTML = "<strong>" + esc(data.summary_es) + "</strong>";

    var listEl = document.getElementById("amendmentList");
    if (data.amendments.length === 0) {
        listEl.innerHTML = '<div class="no-amendments">El suelo esta en optimas condiciones.</div>';
    } else {
        listEl.innerHTML = data.amendments.map(function (a) {
            return '<div class="amendment-card">' +
                '<h4>' + esc(a.name) + '</h4>' +
                '<div class="qty">' + a.kg_per_ha.toLocaleString() + ' kg/ha</div>' +
                '<div class="meta">' + esc(a.reason_es) + '</div>' +
                '<div class="meta">Costo estimado: $' + a.cost_mxn_per_ha.toLocaleString() + ' MXN/ha</div>' +
                '</div>';
        }).join("");
    }

    document.getElementById("costTotal").innerHTML =
        '<div>Costo total estimado</div><div class="amount">$' +
        data.total_cost_mxn_per_ha.toLocaleString() + ' MXN/ha</div>';
}
