/* -- cultivOS Soil CSV Import -- soil-import.js -- */

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

let selectedFarmId = null;
let selectedFieldId = null;
let parsedRows = [];
let parsedHeaders = [];

// ── Farm/Field selectors ──────────────────────────────────────

async function loadFarms() {
    const result = await fetchJSON('/api/farms');
    if (!result) return;
    const farms = result.data || result;
    const sel = document.getElementById('si-farm-select');
    sel.innerHTML = '<option value="">-- Seleccionar granja --</option>';
    if (!farms || !farms.length) return;
    farms.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = f.name;
        sel.appendChild(opt);
    });
}

async function loadFields(farmId) {
    const fieldSel = document.getElementById('si-field-select');
    fieldSel.innerHTML = '<option value="">-- Seleccionar parcela --</option>';
    fieldSel.disabled = true;
    selectedFieldId = null;
    updateImportBtn();

    if (!farmId) return;
    const result = await fetchJSON('/api/farms/' + farmId + '/fields');
    if (!result) return;
    const fields = result.data || result;
    if (!fields || !fields.length) return;
    fieldSel.disabled = false;
    fields.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = f.name + (f.crop_type ? ' (' + esc(f.crop_type) + ')' : '');
        fieldSel.appendChild(opt);
    });
}

// ── CSV preview parsing (client-side) ─────────────────────────

function parseCSVPreview(text) {
    const lines = text.trim().split('\n');
    if (lines.length < 2) return { headers: [], rows: [] };
    const headers = lines[0].split(',').map(h => h.trim());
    const rows = [];
    const maxPreview = 10;
    for (let i = 1; i < Math.min(lines.length, maxPreview + 1); i++) {
        const vals = lines[i].split(',').map(v => v.trim());
        rows.push(vals);
    }
    return { headers, rows, totalRows: lines.length - 1 };
}

function renderPreview(headers, rows, totalRows) {
    const section = document.getElementById('si-preview-section');
    const thead = document.getElementById('si-preview-thead');
    const tbody = document.getElementById('si-preview-tbody');
    const countEl = document.getElementById('si-preview-count');

    thead.innerHTML = '<tr>' + headers.map(h => '<th class="mgmt-th">' + esc(h) + '</th>').join('') + '</tr>';
    tbody.innerHTML = rows.map(r =>
        '<tr>' + r.map(v => '<td class="mgmt-td">' + esc(v) + '</td>').join('') + '</tr>'
    ).join('');

    const shownCount = rows.length;
    countEl.textContent = 'Mostrando ' + shownCount + ' de ' + totalRows + ' filas';
    section.style.display = '';
    document.getElementById('si-action-section').style.display = '';
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Reset results
    document.getElementById('si-results').style.display = 'none';
    document.getElementById('si-errors').style.display = 'none';
    document.getElementById('si-import-status').textContent = '';

    const reader = new FileReader();
    reader.onload = function(ev) {
        const text = ev.target.result;
        const parsed = parseCSVPreview(text);
        parsedHeaders = parsed.headers;
        parsedRows = parsed.rows;
        renderPreview(parsed.headers, parsed.rows, parsed.totalRows);
        updateImportBtn();
    };
    reader.readAsText(file);
}

// ── Import ────────────────────────────────────────────────────

function updateImportBtn() {
    const btn = document.getElementById('si-import-btn');
    const fileInput = document.getElementById('si-file-input');
    btn.disabled = !(selectedFarmId && selectedFieldId && fileInput.files.length > 0);
}

async function doImport() {
    const btn = document.getElementById('si-import-btn');
    const status = document.getElementById('si-import-status');
    const fileInput = document.getElementById('si-file-input');

    if (!selectedFarmId || !selectedFieldId || !fileInput.files.length) return;

    btn.disabled = true;
    status.textContent = 'Importando...';

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const token = localStorage.getItem('cultivOS_token');
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;

        const resp = await fetch(
            '/api/farms/' + selectedFarmId + '/fields/' + selectedFieldId + '/soil/import-csv',
            { method: 'POST', body: formData, headers }
        );

        if (!resp.ok) {
            const err = await resp.json();
            const detail = err.detail || err.error?.message || 'Error desconocido';
            status.textContent = 'Error: ' + detail;
            btn.disabled = false;
            return;
        }

        const data = await resp.json();
        showResults(data);
        status.textContent = '';
    } catch (err) {
        status.textContent = 'Error de red: ' + err.message;
    }
    btn.disabled = false;
}

function showResults(data) {
    document.getElementById('si-count-imported').textContent = data.imported || 0;
    document.getElementById('si-count-skipped').textContent = data.skipped || 0;
    document.getElementById('si-count-errors').textContent = (data.errors || []).length;
    document.getElementById('si-results').style.display = '';

    const errorSection = document.getElementById('si-errors');
    const errorList = document.getElementById('si-error-list');
    if (data.errors && data.errors.length > 0) {
        errorList.innerHTML = data.errors.map(e =>
            '<div class="si-error-row">Fila ' + esc(String(e.row)) + ': ' + esc(e.detail) + '</div>'
        ).join('');
        errorSection.style.display = '';
    } else {
        errorSection.style.display = 'none';
    }
}

// ── Init ──────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
    loadFarms();

    document.getElementById('si-farm-select').addEventListener('change', function() {
        selectedFarmId = this.value || null;
        loadFields(selectedFarmId);
    });

    document.getElementById('si-field-select').addEventListener('change', function() {
        selectedFieldId = this.value || null;
        updateImportBtn();
    });

    document.getElementById('si-file-input').addEventListener('change', handleFileSelect);
    document.getElementById('si-import-btn').addEventListener('click', doImport);

    // Auth nav
    const token = localStorage.getItem('cultivOS_token');
    const username = localStorage.getItem('cultivOS_username');
    if (token && username) {
        const el = document.getElementById('nav-username');
        if (el) el.textContent = username;
    }
    const logoutBtn = document.getElementById('nav-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('cultivOS_token');
            localStorage.removeItem('cultivOS_username');
            window.location.href = '/login';
        });
    }
});
