/* -- cultivOS WhatsApp Demo Simulator — whatsapp-demo.js -- */

// Pre-scripted conversation: farmer <-> cultivOS AI assistant
const conversation = [
    {
        type: "voice",
        sender: "farmer",
        text: null,
        voiceDuration: "0:23",
        // Farmer sends a voice note describing field observations
        transcript: "Don Manuel reporta que el maiz en la parcela norte se ve amarillento desde hace tres dias, especialmente en las orillas.",
        time: "9:12"
    },
    {
        type: "text",
        sender: "ai",
        text: "Buenos dias, Don Manuel. Recibi su nota de voz.\n\nProcesando datos de su parcela norte...\n\nReporte de Salud:\n- NDVI promedio: 0.42 (bajo)\n- Temperatura foliar: 34.2C (estres hidrico detectado)\n- Puntuacion de salud: 58/100\n- Tendencia: descendente (-12 pts en 2 semanas)\n\nEl amarillamiento coincide con las zonas de mayor estres termico detectadas por el dron el lunes.",
        time: "9:13"
    },
    {
        type: "text",
        sender: "farmer",
        text: "Y que le puedo echar? No quiero usar quimicos.",
        time: "9:15"
    },
    {
        type: "text",
        sender: "ai",
        text: "Entendido, Don Manuel. Solo tratamientos organicos.\n\nRecomendacion:\n1. Riego profundo inmediato — el suelo esta a 18% humedad (necesita 25%+)\n2. Aplicar te de composta con micorrizas — mejora absorcion de nutrientes y retiene humedad\n3. Mulch de rastrojo en orillas — reduce evaporacion 30-40%\n\nEsto es consistente con el metodo ancestral de cobertura que usan en Valles Centrales. Los datos del dron muestran que las parcelas con mulch tienen +15 puntos de salud.\n\nPuedo programar un vuelo de seguimiento para el jueves?",
        time: "9:16"
    },
    {
        type: "voice",
        sender: "farmer",
        text: null,
        voiceDuration: "0:08",
        transcript: "Si, programa el vuelo. Voy a echar el te de composta manana temprano.",
        time: "9:18"
    },
    {
        type: "text",
        sender: "ai",
        text: "Perfecto. Vuelo programado:\n- Jueves 10:00 AM\n- Dron: Mavic 3 Multispectral\n- Cobertura: Parcela norte (12 ha)\n- Tipo: NDVI + termico\n\nLe envio el reporte automaticamente despues del vuelo. Buena suerte con el tratamiento!",
        time: "9:19"
    }
];

let demoRunning = false;
let currentIndex = 0;

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function createVoiceWaveform() {
    const bars = 20;
    let html = '';
    for (let i = 0; i < bars; i++) {
        const h = 4 + Math.floor(Math.random() * 18);
        html += '<div class="waveform-bar" style="height:' + h + 'px"></div>';
    }
    return html;
}

function addMessage(msg) {
    const container = document.getElementById('chat-messages');
    const typing = document.getElementById('typing-indicator');

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble ' + (msg.sender === 'farmer' ? 'msg-farmer' : 'msg-ai');

    let content = '';

    if (msg.type === 'voice') {
        content += '<div class="voice-message">';
        content += '<button class="voice-play">&#9654;</button>';
        content += '<div class="voice-waveform">' + createVoiceWaveform() + '</div>';
        content += '<span class="voice-duration">' + esc(msg.voiceDuration) + '</span>';
        content += '</div>';
        if (msg.transcript) {
            content += '<div style="margin-top:6px;font-size:12px;color:rgba(255,255,255,0.5);font-style:italic;">';
            content += 'Transcripcion: ' + esc(msg.transcript);
            content += '</div>';
        }
    } else {
        content += '<div class="msg-text">' + esc(msg.text).replace(/\n/g, '<br>') + '</div>';
    }

    content += '<span class="msg-time">' + esc(msg.time) + '</span>';
    bubble.innerHTML = content;

    // Insert before typing indicator
    container.insertBefore(bubble, typing);
    container.scrollTop = container.scrollHeight;
}

function showTyping() {
    const indicator = document.getElementById('typing-indicator');
    indicator.classList.add('visible');
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
}

function hideTyping() {
    const indicator = document.getElementById('typing-indicator');
    indicator.classList.remove('visible');
}

function runDemo() {
    if (demoRunning) return;
    demoRunning = true;

    // Clear existing messages
    const container = document.getElementById('chat-messages');
    const typing = document.getElementById('typing-indicator');
    container.innerHTML = '';
    container.appendChild(typing);

    currentIndex = 0;
    const statusEl = document.getElementById('demo-status');
    statusEl.textContent = 'Conversacion en curso...';

    playNextMessage();
}

function playNextMessage() {
    if (currentIndex >= conversation.length) {
        demoRunning = false;
        const statusEl = document.getElementById('demo-status');
        statusEl.textContent = 'Conversacion completada. Presiona para repetir.';
        return;
    }

    const msg = conversation[currentIndex];
    currentIndex++;

    if (msg.sender === 'ai') {
        // Show typing indicator before AI message
        showTyping();
        setTimeout(function() {
            hideTyping();
            addMessage(msg);
            setTimeout(playNextMessage, 800);
        }, 1200 + Math.random() * 800);
    } else {
        // Farmer messages appear immediately
        addMessage(msg);
        setTimeout(playNextMessage, 600);
    }
}
