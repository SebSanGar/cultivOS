/* -- cultivOS Farm/Field Management -- management.js -- */

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

async function fetchJSON(path) {
    try {
        const token = localStorage.getItem('cultivOS_token');
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const resp = await fetch(path, { headers });
        if (!resp.ok) return null;
        return await resp.json();
    } catch {
        return null;
    }
}

async function apiCall(method, path, body) {
    const token = localStorage.getItem('cultivOS_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const resp = await fetch(path, opts);
    return resp;
}

let selectedFarmId = null;
let pendingConfirmCallback = null;

// ── Farm CRUD ──────────────────────────────────────────────────

async function loadFarms() {
    const result = await fetchJSON('/api/farms');
    if (!result) return;
    const farms = result.data || result;
    const tbody = document.getElementById('mgmt-farms-tbody');
    const empty = document.getElementById('mgmt-farms-empty');

    if (!farms || farms.length === 0) {
        tbody.innerHTML = '';
        empty.style.display = '';
        return;
    }
    empty.style.display = 'none';

    tbody.innerHTML = farms.map(f => `
        <tr>
            <td>${f.id}</td>
            <td>${esc(f.name)}</td>
            <td>${esc(f.owner_name || '—')}</td>
            <td>${esc(f.state)}</td>
            <td>${esc(f.municipality || '—')}</td>
            <td>${f.total_hectares || 0}</td>
            <td class="mgmt-actions-cell">
                <button class="mgmt-btn-sm mgmt-btn-view" onclick="selectFarm(${f.id}, '${esc(f.name)}')">Parcelas</button>
                <button class="mgmt-btn-sm mgmt-btn-edit" onclick="editFarm(${f.id})">Editar</button>
                <button class="mgmt-btn-sm mgmt-btn-delete" onclick="confirmDeleteFarm(${f.id}, '${esc(f.name)}')">Eliminar</button>
            </td>
        </tr>
    `).join('');
}

async function createFarm() {
    const name = document.getElementById('mgmt-farm-name').value.trim();
    const errorEl = document.getElementById('mgmt-farm-error');
    if (!name) {
        errorEl.textContent = 'El nombre de la granja es obligatorio.';
        return;
    }
    errorEl.textContent = '';

    const body = {
        name,
        owner_name: document.getElementById('mgmt-farm-owner').value.trim() || null,
        state: document.getElementById('mgmt-farm-state').value.trim() || 'Jalisco',
        municipality: document.getElementById('mgmt-farm-municipality').value.trim() || null,
        total_hectares: parseFloat(document.getElementById('mgmt-farm-hectares').value) || 0,
        country: document.getElementById('mgmt-farm-country').value || 'MX',
    };

    const resp = await apiCall('POST', '/api/farms', body);
    if (resp.ok) {
        document.getElementById('mgmt-farm-name').value = '';
        document.getElementById('mgmt-farm-owner').value = '';
        document.getElementById('mgmt-farm-municipality').value = '';
        document.getElementById('mgmt-farm-hectares').value = '0';
        await loadFarms();
    } else {
        const err = await resp.json().catch(() => null);
        errorEl.textContent = err?.detail || err?.error?.message || 'Error al crear la granja.';
    }
}

async function editFarm(farmId) {
    const data = await fetchJSON(`/api/farms/${farmId}`);
    if (!data) return;

    document.getElementById('mgmt-edit-title').textContent = 'Editar Granja: ' + (data.name || '');
    document.getElementById('mgmt-edit-fields').innerHTML = `
        <div class="mgmt-form-group">
            <label>Nombre *</label>
            <input type="text" id="edit-farm-name" value="${esc(data.name)}">
        </div>
        <div class="mgmt-form-group">
            <label>Propietario</label>
            <input type="text" id="edit-farm-owner" value="${esc(data.owner_name || '')}">
        </div>
        <div class="mgmt-form-group">
            <label>Estado</label>
            <input type="text" id="edit-farm-state" value="${esc(data.state || '')}">
        </div>
        <div class="mgmt-form-group">
            <label>Municipio</label>
            <input type="text" id="edit-farm-municipality" value="${esc(data.municipality || '')}">
        </div>
        <div class="mgmt-form-group">
            <label>Hectareas</label>
            <input type="number" id="edit-farm-hectares" value="${data.total_hectares || 0}" min="0" step="0.1">
        </div>
    `;

    pendingConfirmCallback = async () => {
        const body = {
            name: document.getElementById('edit-farm-name').value.trim(),
            owner_name: document.getElementById('edit-farm-owner').value.trim() || null,
            state: document.getElementById('edit-farm-state').value.trim() || 'Jalisco',
            municipality: document.getElementById('edit-farm-municipality').value.trim() || null,
            total_hectares: parseFloat(document.getElementById('edit-farm-hectares').value) || 0,
        };
        if (!body.name) return;
        await apiCall('PUT', `/api/farms/${farmId}`, body);
        closeEdit();
        await loadFarms();
    };

    document.getElementById('mgmt-edit-dialog').style.display = '';
}

function confirmDeleteFarm(farmId, farmName) {
    document.getElementById('mgmt-confirm-message').textContent =
        `Eliminar granja "${farmName}"? Se eliminaran todas sus parcelas y datos asociados.`;
    pendingConfirmCallback = async () => {
        await apiCall('DELETE', `/api/farms/${farmId}`);
        closeConfirm();
        if (selectedFarmId === farmId) {
            selectedFarmId = null;
            document.getElementById('mgmt-fields-section').style.display = 'none';
        }
        await loadFarms();
    };
    document.getElementById('mgmt-confirm-dialog').style.display = '';
}

async function deleteFarm(farmId) {
    await apiCall('DELETE', `/api/farms/${farmId}`);
    await loadFarms();
}

// ── Field CRUD ─────────────────────────────────────────────────

async function selectFarm(farmId, farmName) {
    selectedFarmId = farmId;
    document.getElementById('mgmt-fields-farm-name').textContent = farmName;
    document.getElementById('mgmt-fields-section').style.display = '';
    await loadFields();
}

async function loadFields() {
    if (!selectedFarmId) return;
    const fields = await fetchJSON(`/api/farms/${selectedFarmId}/fields`);
    const tbody = document.getElementById('mgmt-fields-tbody');
    const empty = document.getElementById('mgmt-fields-empty');

    if (!fields || fields.length === 0) {
        tbody.innerHTML = '';
        empty.style.display = '';
        return;
    }
    empty.style.display = 'none';

    const cropLabels = {
        maize: 'Maiz', agave: 'Agave', avocado: 'Aguacate', berries: 'Berries',
        sugarcane: 'Cana', tomato: 'Tomate', chili: 'Chile', beans: 'Frijol',
        sorghum: 'Sorgo', wheat: 'Trigo', alfalfa: 'Alfalfa',
    };

    tbody.innerHTML = fields.map(f => `
        <tr>
            <td>${f.id}</td>
            <td>${esc(f.name)}</td>
            <td>${cropLabels[f.crop_type] || esc(f.crop_type || '—')}</td>
            <td>${f.hectares || 0}</td>
            <td>${f.created_at ? new Date(f.created_at).toLocaleDateString('es-MX') : '—'}</td>
            <td class="mgmt-actions-cell">
                <button class="mgmt-btn-sm mgmt-btn-edit" onclick="editField(${f.id})">Editar</button>
                <button class="mgmt-btn-sm mgmt-btn-delete" onclick="confirmDeleteField(${f.id}, '${esc(f.name)}')">Eliminar</button>
            </td>
        </tr>
    `).join('');
}

async function createField() {
    if (!selectedFarmId) return;
    const name = document.getElementById('mgmt-field-name').value.trim();
    const errorEl = document.getElementById('mgmt-field-error');
    if (!name) {
        errorEl.textContent = 'El nombre de la parcela es obligatorio.';
        return;
    }
    errorEl.textContent = '';

    const crop = document.getElementById('mgmt-field-crop').value;
    const body = {
        name,
        crop_type: crop || null,
        hectares: parseFloat(document.getElementById('mgmt-field-hectares').value) || 0,
    };

    const resp = await apiCall('POST', `/api/farms/${selectedFarmId}/fields`, body);
    if (resp.ok) {
        document.getElementById('mgmt-field-name').value = '';
        document.getElementById('mgmt-field-crop').value = '';
        document.getElementById('mgmt-field-hectares').value = '0';
        await loadFields();
    } else {
        const err = await resp.json().catch(() => null);
        errorEl.textContent = err?.detail || err?.error?.message || 'Error al crear la parcela.';
    }
}

async function editField(fieldId) {
    if (!selectedFarmId) return;
    const data = await fetchJSON(`/api/farms/${selectedFarmId}/fields/${fieldId}`);
    if (!data) return;

    document.getElementById('mgmt-edit-title').textContent = 'Editar Parcela: ' + (data.name || '');
    document.getElementById('mgmt-edit-fields').innerHTML = `
        <div class="mgmt-form-group">
            <label>Nombre *</label>
            <input type="text" id="edit-field-name" value="${esc(data.name)}">
        </div>
        <div class="mgmt-form-group">
            <label>Cultivo</label>
            <input type="text" id="edit-field-crop" value="${esc(data.crop_type || '')}">
        </div>
        <div class="mgmt-form-group">
            <label>Hectareas</label>
            <input type="number" id="edit-field-hectares" value="${data.hectares || 0}" min="0" step="0.1">
        </div>
    `;

    pendingConfirmCallback = async () => {
        const body = {
            name: document.getElementById('edit-field-name').value.trim(),
            crop_type: document.getElementById('edit-field-crop').value.trim() || null,
            hectares: parseFloat(document.getElementById('edit-field-hectares').value) || 0,
        };
        if (!body.name) return;
        await apiCall('PUT', `/api/farms/${selectedFarmId}/fields/${fieldId}`, body);
        closeEdit();
        await loadFields();
    };

    document.getElementById('mgmt-edit-dialog').style.display = '';
}

function confirmDeleteField(fieldId, fieldName) {
    document.getElementById('mgmt-confirm-message').textContent =
        `Eliminar parcela "${fieldName}"? Se eliminaran todos los datos asociados (vuelos, analisis, tratamientos).`;
    pendingConfirmCallback = async () => {
        await apiCall('DELETE', `/api/farms/${selectedFarmId}/fields/${fieldId}`);
        closeConfirm();
        await loadFields();
    };
    document.getElementById('mgmt-confirm-dialog').style.display = '';
}

async function deleteField(fieldId) {
    if (!selectedFarmId) return;
    await apiCall('DELETE', `/api/farms/${selectedFarmId}/fields/${fieldId}`);
    await loadFields();
}

// ── Dialogs ────────────────────────────────────────────────────

function confirmAction() {
    if (pendingConfirmCallback) pendingConfirmCallback();
}

function closeConfirm() {
    document.getElementById('mgmt-confirm-dialog').style.display = 'none';
    pendingConfirmCallback = null;
}

function saveEdit() {
    if (pendingConfirmCallback) pendingConfirmCallback();
}

function closeEdit() {
    document.getElementById('mgmt-edit-dialog').style.display = 'none';
    pendingConfirmCallback = null;
}

// ── Auth nav ───────────────────────────────────────────────────

function initNav() {
    const token = localStorage.getItem('cultivOS_token');
    const user = localStorage.getItem('cultivOS_user');
    if (user) {
        document.getElementById('nav-username').textContent = user;
    }
    document.getElementById('nav-logout').addEventListener('click', e => {
        e.preventDefault();
        localStorage.removeItem('cultivOS_token');
        localStorage.removeItem('cultivOS_user');
        window.location.href = '/login';
    });
}

// ── Init ───────────────────────────────────────────────────────

async function initPage() {
    initNav();
    await loadFarms();
}

document.addEventListener('DOMContentLoaded', initPage);
