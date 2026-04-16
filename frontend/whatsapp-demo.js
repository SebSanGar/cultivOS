/* cultivOS WhatsApp Demo — live-data wire (D8).
   Farmer turns remain scripted (they simulate voice notes).
   AI turns pull live data from:
     GET /api/farms
     GET /api/farms/{farm_id}/fields
     GET /api/farms/{farm_id}/fields/{field_id}/intelligence
   The intelligence endpoint already embeds treatments, so one live call
   populates the field health summary AND the organic recommendations. */

(function () {
    "use strict";

    let demoRunning = false;
    let currentIndex = 0;
    let conversation = [];
    let liveContext = null; // {farm, field, intel} after fetch

    // ── helpers ──────────────────────────────────────────────────────────
    function esc(str) {
        if (str == null) return "";
        const d = document.createElement("div");
        d.textContent = String(str);
        return d.innerHTML;
    }

    function fmt(n, digits) {
        if (n == null || Number.isNaN(Number(n))) return "—";
        return Number(n).toFixed(digits == null ? 1 : digits);
    }

    async function fetchJSON(path) {
        try {
            const resp = await fetch(path);
            if (!resp.ok) return null;
            return await resp.json();
        } catch (_) {
            return null;
        }
    }

    function createVoiceWaveform() {
        let html = "";
        for (let i = 0; i < 20; i++) {
            const h = 4 + Math.floor(Math.random() * 18);
            html += '<div class="waveform-bar" style="height:' + h + 'px"></div>';
        }
        return html;
    }

    function addMessage(msg) {
        const container = document.getElementById("chat-messages");
        const typing = document.getElementById("typing-indicator");
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble " + (msg.sender === "farmer" ? "msg-farmer" : "msg-ai");

        let content = "";
        if (msg.type === "voice") {
            content += '<div class="voice-message">';
            content += '<button class="voice-play">&#9654;</button>';
            content += '<div class="voice-waveform">' + createVoiceWaveform() + "</div>";
            content += '<span class="voice-duration">' + esc(msg.voiceDuration) + "</span>";
            content += "</div>";
            if (msg.transcript) {
                content += '<div style="margin-top:6px;font-size:12px;color:rgba(255,255,255,0.5);font-style:italic;">';
                content += "Transcripcion: " + esc(msg.transcript);
                content += "</div>";
            }
        } else {
            content += '<div class="msg-text">' + esc(msg.text).replace(/\n/g, "<br>") + "</div>";
        }
        content += '<span class="msg-time">' + esc(msg.time) + "</span>";
        bubble.innerHTML = content;
        container.insertBefore(bubble, typing);
        container.scrollTop = container.scrollHeight;
    }

    function showTyping() {
        document.getElementById("typing-indicator").classList.add("visible");
        const container = document.getElementById("chat-messages");
        container.scrollTop = container.scrollHeight;
    }
    function hideTyping() {
        document.getElementById("typing-indicator").classList.remove("visible");
    }

    // ── live data → conversation script ──────────────────────────────────
    function t(offsetMin) {
        const d = new Date();
        d.setMinutes(d.getMinutes() + offsetMin);
        return d.toTimeString().slice(0, 5);
    }

    function healthReport(intel) {
        const health = intel.health || {};
        const ndvi = intel.ndvi || {};
        const thermal = intel.thermal || {};
        const weather = intel.weather || {};
        const lines = [];
        lines.push("Reporte de Salud — " + (intel.field_name || "campo"));
        if (health.score != null) lines.push("- Puntuacion: " + fmt(health.score, 0) + "/100");
        if (ndvi.ndvi_mean != null) lines.push("- NDVI promedio: " + fmt(ndvi.ndvi_mean, 2));
        if (thermal.temp_mean != null) lines.push("- Temperatura foliar: " + fmt(thermal.temp_mean, 1) + "C");
        if (thermal.stress_pct != null) lines.push("- Estres termico: " + fmt(thermal.stress_pct, 0) + "%");
        if (weather.humidity_pct != null) lines.push("- Humedad ambiente: " + fmt(weather.humidity_pct, 0) + "%");
        if (health.trend) lines.push("- Tendencia: " + health.trend);
        if (lines.length === 1) lines.push("- Sin sensores registrados aun para esta parcela.");
        return lines.join("\n");
    }

    function treatmentsReport(intel) {
        const treatments = Array.isArray(intel.treatments) ? intel.treatments.slice(0, 3) : [];
        if (!treatments.length) {
            return "Aun no tengo recomendaciones registradas para esta parcela. Registra una lectura de suelo o NDVI y las genero al instante.";
        }
        const lines = ["Recomendaciones organicas (100% regenerativo):"];
        treatments.forEach((tx, i) => {
            const name = tx.name || tx.recommendation || ("Tratamiento " + (i + 1));
            const why = tx.rationale || tx.reason || "";
            lines.push((i + 1) + ". " + name + (why ? " — " + why : ""));
        });
        return lines.join("\n");
    }

    function emptyStateScript(reason) {
        return [
            {
                type: "voice", sender: "farmer", voiceDuration: "0:11",
                transcript: "Queria ver un reporte de mi parcela pero todavia no conecto nada al sistema.",
                time: t(-4),
            },
            {
                type: "text", sender: "ai",
                text: "Hola. " + reason + "\n\nPara activar el demo en vivo:\n1. Registra al menos una finca (POST /api/farms)\n2. Anade un campo con cultivo y hectareas\n3. Sube una lectura NDVI o analisis de suelo\n\nEl asistente respondera con datos reales en cuanto exista una parcela.",
                time: t(-3),
            },
        ];
    }

    async function buildConversation() {
        const farms = await fetchJSON("/api/farms");
        const farmList = (farms && (farms.data || farms)) || [];
        const farm = Array.isArray(farmList) ? farmList[0] : null;
        if (!farm) return emptyStateScript("Aun no hay fincas registradas en la plataforma.");

        const fields = await fetchJSON("/api/farms/" + farm.id + "/fields");
        const fieldList = (fields && (fields.data || fields)) || [];
        const field = Array.isArray(fieldList) ? fieldList[0] : null;
        if (!field) return emptyStateScript("La finca '" + (farm.name || "#" + farm.id) + "' no tiene campos registrados.");

        const intel = await fetchJSON("/api/farms/" + farm.id + "/fields/" + field.id + "/intelligence");
        if (!intel) return emptyStateScript("No pude leer los datos de inteligencia del campo.");

        liveContext = { farm, field, intel };

        const farmerName = farm.owner_name || "productor";
        const fieldName = field.name || "la parcela";

        return [
            {
                type: "voice", sender: "farmer", voiceDuration: "0:23",
                transcript: "Necesito un reporte rapido del " + fieldName + ". Como la ve hoy?",
                time: t(-5),
            },
            {
                type: "text", sender: "ai",
                text: "Buenos dias, " + farmerName + ". Recibi su nota.\n\n" + healthReport(intel),
                time: t(-4),
            },
            {
                type: "text", sender: "farmer",
                text: "Y que le puedo echar? No quiero usar quimicos.",
                time: t(-3),
            },
            {
                type: "text", sender: "ai",
                text: "Entendido. Solo tratamientos organicos.\n\n" + treatmentsReport(intel),
                time: t(-2),
            },
            {
                type: "voice", sender: "farmer", voiceDuration: "0:08",
                transcript: "Perfecto, manana aplico lo primero.",
                time: t(-1),
            },
            {
                type: "text", sender: "ai",
                text: "Registrado. Programare un vuelo de seguimiento con el dron para validar el efecto en 5 dias. El reporte llega automatico a este chat.",
                time: t(0),
            },
        ];
    }

    // ── playback ─────────────────────────────────────────────────────────
    function playNextMessage() {
        if (currentIndex >= conversation.length) {
            demoRunning = false;
            const statusEl = document.getElementById("demo-status");
            if (statusEl) statusEl.textContent = "Conversacion completada. Presiona para repetir.";
            return;
        }
        const msg = conversation[currentIndex++];
        if (msg.sender === "ai") {
            showTyping();
            setTimeout(function () {
                hideTyping();
                addMessage(msg);
                setTimeout(playNextMessage, 800);
            }, 1200 + Math.random() * 800);
        } else {
            addMessage(msg);
            setTimeout(playNextMessage, 600);
        }
    }

    async function runDemo() {
        if (demoRunning) return;
        demoRunning = true;

        const container = document.getElementById("chat-messages");
        const typing = document.getElementById("typing-indicator");
        container.innerHTML = "";
        container.appendChild(typing);

        const statusEl = document.getElementById("demo-status");
        if (statusEl) statusEl.textContent = "Conectando con cultivOS...";

        conversation = await buildConversation();
        currentIndex = 0;

        if (statusEl) {
            statusEl.textContent = liveContext
                ? "Conversacion en curso — datos en vivo de " + (liveContext.field.name || "la parcela")
                : "Conversacion en curso (modo demo, sin datos vivos)";
        }
        playNextMessage();
    }

    // Expose for HTML onclick + give existing button code a hook
    window.runDemo = runDemo;
    window.startWhatsAppDemo = runDemo;
})();
