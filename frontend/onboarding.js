/**
 * cultivOS — Onboarding wizard JS
 * Multi-step farm creation: farm info → add fields → confirm → create
 */

let _currentStep = 1;
let _fields = [];
let _cropTypes = [];

// ── Initialization ──────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadCropTypes();
    showStep(1);
});

async function loadCropTypes() {
    try {
        const resp = await fetch('/api/knowledge/crops');
        if (resp.ok) {
            const data = await resp.json();
            _cropTypes = Array.isArray(data) ? data : [];
        }
    } catch (e) {
        _cropTypes = [];
    }
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

// ── Step Navigation ─────────────────────────────────────────────────

function showStep(n) {
    for (let i = 1; i <= 3; i++) {
        const el = document.getElementById('wizard-step-' + i);
        if (el) el.style.display = (i === n) ? '' : 'none';

        const prog = document.getElementById('wizard-prog-' + i);
        if (prog) {
            prog.classList.remove('active', 'done');
            if (i < n) prog.classList.add('done');
            if (i === n) prog.classList.add('active');
        }
    }
    _currentStep = n;

    if (n === 3) renderSummary();
}

function nextStep() {
    if (_currentStep === 1) {
        const name = document.getElementById('wizard-farm-name').value.trim();
        if (!name) {
            showError('Ingrese el nombre de la granja');
            return;
        }
        clearError();
    }
    if (_currentStep < 3) showStep(_currentStep + 1);
}

function prevStep() {
    if (_currentStep > 1) showStep(_currentStep - 1);
}

// ── Field Management ────────────────────────────────────────────────

function addField() {
    const idx = _fields.length;
    _fields.push({ name: '', crop_type: '', hectares: 0 });
    renderFields();
}

function removeField(idx) {
    _fields.splice(idx, 1);
    renderFields();
}

function updateField(idx, key, value) {
    if (_fields[idx]) {
        _fields[idx][key] = key === 'hectares' ? parseFloat(value) || 0 : value;
    }
}

function renderFields() {
    const container = document.getElementById('wizard-fields');
    const emptyMsg = document.getElementById('wizard-no-fields');

    if (_fields.length === 0) {
        container.innerHTML = '';
        if (emptyMsg) emptyMsg.style.display = '';
        return;
    }

    if (emptyMsg) emptyMsg.style.display = 'none';

    const cropOptions = _cropTypes.map(c => {
        const name = c.name || c.nombre || '';
        return '<option value="' + esc(name) + '">' + esc(name) + '</option>';
    }).join('');

    container.innerHTML = _fields.map((f, i) => {
        return '<div class="wizard-field-row">' +
            '<div class="wizard-form-group">' +
                '<label>Nombre *</label>' +
                '<input type="text" value="' + esc(f.name) + '" placeholder="Ej: Parcela Norte" onchange="updateField(' + i + ',\'name\',this.value)">' +
            '</div>' +
            '<div class="wizard-form-group">' +
                '<label>Cultivo</label>' +
                '<select onchange="updateField(' + i + ',\'crop_type\',this.value)">' +
                    '<option value="">-- Seleccionar --</option>' +
                    cropOptions +
                '</select>' +
            '</div>' +
            '<div class="wizard-form-group">' +
                '<label>Hectareas</label>' +
                '<input type="number" value="' + f.hectares + '" min="0" step="0.1" onchange="updateField(' + i + ',\'hectares\',this.value)">' +
            '</div>' +
            '<button class="wizard-field-remove" onclick="removeField(' + i + ')" title="Eliminar parcela">X</button>' +
        '</div>';
    }).join('');
}

// ── Summary ─────────────────────────────────────────────────────────

function renderSummary() {
    const name = document.getElementById('wizard-farm-name').value.trim();
    const owner = document.getElementById('wizard-farm-owner').value.trim();
    const state = document.getElementById('wizard-farm-state').value.trim();
    const muni = document.getElementById('wizard-farm-municipality').value.trim();
    const hectares = parseFloat(document.getElementById('wizard-farm-hectares').value) || 0;

    const summary = document.getElementById('wizard-summary');
    if (!summary) return;

    let html = '<div class="wizard-summary-section">' +
        '<h3>Granja</h3>' +
        '<div class="wizard-summary-row"><span>Nombre:</span> <strong>' + esc(name) + '</strong></div>';
    if (owner) html += '<div class="wizard-summary-row"><span>Propietario:</span> ' + esc(owner) + '</div>';
    html += '<div class="wizard-summary-row"><span>Ubicacion:</span> ' + esc(muni ? muni + ', ' : '') + esc(state) + '</div>' +
        '<div class="wizard-summary-row"><span>Hectareas:</span> ' + hectares + '</div>' +
        '</div>';

    if (_fields.length > 0) {
        html += '<div class="wizard-summary-section"><h3>Parcelas (' + _fields.length + ')</h3>';
        _fields.forEach(f => {
            html += '<div class="wizard-summary-row"><span>' + esc(f.name || 'Sin nombre') + '</span> — ' +
                esc(f.crop_type || 'Sin cultivo') + ' — ' + f.hectares + ' ha</div>';
        });
        html += '</div>';
    } else {
        html += '<div class="wizard-summary-section"><p class="intel-muted">Sin parcelas agregadas</p></div>';
    }

    summary.innerHTML = html;
}

// ── Submit ───────────────────────────────────────────────────────────

async function finishWizard() {
    const btn = document.getElementById('wiz-finish-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Creando...'; }

    const farmData = {
        name: document.getElementById('wizard-farm-name').value.trim(),
        owner_name: document.getElementById('wizard-farm-owner').value.trim() || null,
        state: document.getElementById('wizard-farm-state').value.trim() || 'Jalisco',
        municipality: document.getElementById('wizard-farm-municipality').value.trim() || null,
        total_hectares: parseFloat(document.getElementById('wizard-farm-hectares').value) || 0,
    };

    if (!farmData.name) {
        showError('El nombre de la granja es obligatorio');
        if (btn) { btn.disabled = false; btn.textContent = 'Finalizar'; }
        return;
    }

    try {
        const token = localStorage.getItem('cultivosToken') || '';
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = 'Bearer ' + token;

        const farmResp = await fetch('/api/farms', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(farmData),
        });

        if (!farmResp.ok) {
            const err = await farmResp.json().catch(() => ({}));
            throw new Error(err.detail || err.error?.message || 'Error al crear la granja');
        }

        const farm = await farmResp.json();

        let fieldsCreated = 0;
        for (const f of _fields) {
            if (!f.name.trim()) continue;
            const fieldResp = await fetch('/api/farms/' + farm.id + '/fields', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    name: f.name.trim(),
                    crop_type: f.crop_type || null,
                    hectares: f.hectares || 0,
                }),
            });
            if (fieldResp.ok) fieldsCreated++;
        }

        document.getElementById('wizard-step-3').style.display = 'none';
        const success = document.getElementById('wizard-success');
        if (success) success.style.display = '';
        const msg = document.getElementById('wizard-success-msg');
        if (msg) {
            msg.textContent = '"' + farm.name + '" creada con ' + fieldsCreated + ' parcela(s).';
        }
    } catch (e) {
        showError(e.message || 'Error inesperado al crear la granja');
        if (btn) { btn.disabled = false; btn.textContent = 'Finalizar'; }
    }
}

// ── Error handling ──────────────────────────────────────────────────

function showError(msg) {
    const el = document.getElementById('wizard-error');
    if (el) {
        el.textContent = msg;
        el.style.display = '';
    }
}

function clearError() {
    const el = document.getElementById('wizard-error');
    if (el) el.style.display = 'none';
}
