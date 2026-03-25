/* Kitchen Intelligence — PWA Dashboard */
/* globals: window, document, localStorage, fetch */

'use strict';

// ── CONFIG ──
const API = '/api';
const TOKEN_KEY = 'ki_token';
const USER_KEY = 'ki_user';

// ── STATE ──
const state = {
  user: null,
  locationId: null,
  token: null,
  currentView: null,
  cache: {},
};

// ── HELPERS ──
function $(sel, el) { return (el || document).querySelector(sel); }
function $$(sel, el) { return [...(el || document).querySelectorAll(sel)]; }
function html(el, h) { if (typeof el === 'string') el = $(el); if (el) el.innerHTML = h; }
function show(el) { if (typeof el === 'string') el = $(el); if (el) el.style.display = ''; }
function hide(el) { if (typeof el === 'string') el = $(el); if (el) el.style.display = 'none'; }

function decodeJWT(token) {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
  } catch { return null; }
}

function fmtDate(iso) {
  if (!iso) return '--';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function fmtTime(iso) {
  if (!iso) return '--';
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function fmtCurrency(n) {
  if (n == null) return '--';
  return '$' + Number(n).toFixed(2);
}

function fmtNum(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString();
}

function todayISO() {
  return new Date().toISOString().split('T')[0];
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

// ── TOAST ──
let toastTimer = null;
function toast(msg, type) {
  const prev = $('.toast');
  if (prev) prev.remove();
  const el = document.createElement('div');
  el.className = 'toast' + (type ? ' toast--' + type : '');
  el.textContent = msg;
  document.body.appendChild(el);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.remove(), 3000);
}

// ── API CLIENT ──
async function api(path, opts) {
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) headers['Authorization'] = 'Bearer ' + state.token;
  const res = await fetch(API + path, { ...opts, headers });
  if (res.status === 401) { logout(); return undefined; }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return null;
  return res.json();
}

function apiGet(path) { return api(path); }
function apiPost(path, body) { return api(path, { method: 'POST', body: JSON.stringify(body) }); }
function apiPatch(path, body) { return api(path, { method: 'PATCH', body: JSON.stringify(body) }); }

// ── AUTH ──
function loadAuth() {
  state.token = localStorage.getItem(TOKEN_KEY);
  try { state.user = JSON.parse(localStorage.getItem(USER_KEY)); } catch { state.user = null; }
  if (state.token) {
    const payload = decodeJWT(state.token);
    if (payload && payload.exp && payload.exp * 1000 < Date.now()) {
      logout();
      return false;
    }
    state.locationId = state.user ? state.user.location_id : (payload ? payload.location_id : null);
    return true;
  }
  return false;
}

function saveAuth(token, user) {
  state.token = token;
  state.user = user;
  state.locationId = user.location_id;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function logout() {
  state.token = null;
  state.user = null;
  state.locationId = null;
  state.cache = {};
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  navigate('login');
}

// ── SVG ICONS ──
const ICONS = {
  dashboard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
  recipes: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19h16M4 15h16M12 3v8m-4-4h8"/><circle cx="12" cy="11" r="4"/></svg>',
  production: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="9" y1="4" x2="9" y2="10"/><line x1="15" y1="4" x2="15" y2="10"/></svg>',
  waste: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/></svg>',
  dna: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 15c6.667-6 13.333 0 20-6M2 9c6.667 6 13.333 0 20 6"/><path d="M7 21V3M17 21V3"/></svg>',
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
  back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><polyline points="15,18 9,12 15,6"/></svg>',
  logout: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>',
  scale: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><path d="M12 3v18M3 12l3-3 3 3M15 9l3-3 3 3M3 12l3 3 3-3M15 15l3 3 3-3"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><polyline points="3,6 5,6 21,6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>',
};

// ── ROUTER ──
const ROUTES = ['login', 'dashboard', 'recipes', 'recipe', 'production', 'waste', 'kitchen-dna'];

function navigate(view, params) {
  const hash = params ? view + '?' + new URLSearchParams(params).toString() : view;
  window.location.hash = hash;
}

function parseHash() {
  const raw = window.location.hash.replace('#', '') || 'dashboard';
  const [view, qs] = raw.split('?');
  const params = qs ? Object.fromEntries(new URLSearchParams(qs)) : {};
  return { view, params };
}

function route() {
  const { view, params } = parseHash();
  if (view !== 'login' && !state.token) { navigate('login'); return; }
  if (view === 'login' && state.token) { navigate('dashboard'); return; }
  state.currentView = view;
  renderApp(view, params);
}

window.addEventListener('hashchange', route);

// ── APP SHELL ──
function renderApp(view, params) {
  const app = $('#app');
  if (view === 'login') {
    app.innerHTML = '';
    renderLogin(app);
    return;
  }

  const showTabs = view !== 'recipe';
  app.innerHTML = `
    <header class="topbar">
      <div>
        <div class="topbar-title">${escHtml(state.user ? state.user.name : 'Kitchen')}</div>
        <div class="topbar-subtitle">${escHtml(state.user ? state.user.role : '')}</div>
      </div>
      <button class="topbar-action" id="logout-btn" title="Logout">${ICONS.logout}</button>
    </header>
    <div class="main">
      <div class="view" id="view-content"></div>
    </div>
    ${showTabs ? renderTabBar(view) : ''}
  `;

  $('#logout-btn').addEventListener('click', logout);
  if (showTabs) bindTabs();

  const container = $('#view-content');
  switch (view) {
    case 'dashboard': renderDashboard(container); break;
    case 'recipes': renderRecipes(container); break;
    case 'recipe': renderRecipeDetail(container, params.id); break;
    case 'production': renderProduction(container); break;
    case 'waste': renderWaste(container); break;
    case 'kitchen-dna': renderKitchenDNA(container); break;
    default: navigate('dashboard');
  }
}

function renderTabBar(active) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: ICONS.dashboard },
    { id: 'recipes', label: 'Recipes', icon: ICONS.recipes },
    { id: 'production', label: 'Production', icon: ICONS.production },
    { id: 'waste', label: 'Waste', icon: ICONS.waste },
    { id: 'kitchen-dna', label: 'DNA', icon: ICONS.dna },
  ];
  return `<nav class="tabbar">${tabs.map(t =>
    `<a class="tab${t.id === active ? ' active' : ''}" href="#${t.id}" data-tab="${t.id}">${t.icon}<span>${t.label}</span></a>`
  ).join('')}</nav>`;
}

function bindTabs() {
  $$('.tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      navigate(tab.dataset.tab);
    });
  });
}

function loading() { return '<div class="loading"><div class="spinner"></div>Loading...</div>'; }

// ── LOGIN VIEW ──
function renderLogin(container) {
  let pin = '';
  let userId = '';
  let error = '';

  function render() {
    container.innerHTML = `
      <div class="login-screen">
        <div class="login-logo">Kitchen Intelligence</div>
        <div class="login-subtitle">Enter your credentials</div>
        <div class="login-user-select">
          <input class="input" id="login-uid" type="number" inputmode="numeric"
            placeholder="User ID" value="${escHtml(userId)}">
        </div>
        <div class="pin-dots">
          ${[0,1,2,3,4,5].map(i => `<div class="pin-dot${i < pin.length ? ' filled' : ''}"></div>`).join('')}
        </div>
        <div class="pin-pad">
          ${[1,2,3,4,5,6,7,8,9].map(n =>
            `<button class="pin-key" data-key="${n}">${n}</button>`
          ).join('')}
          <button class="pin-key pin-key--action" data-key="clear">CLR</button>
          <button class="pin-key" data-key="0">0</button>
          <button class="pin-key pin-key--action" data-key="enter">GO</button>
        </div>
        <div class="login-error" id="login-error">${escHtml(error)}</div>
      </div>
    `;

    $('#login-uid').addEventListener('input', (e) => { userId = e.target.value; });

    $$('.pin-key').forEach(btn => {
      btn.addEventListener('click', () => handleKey(btn.dataset.key));
    });
  }

  async function handleKey(key) {
    if (key === 'clear') { pin = ''; error = ''; render(); return; }
    if (key === 'enter') { await doLogin(); return; }
    if (pin.length < 6) {
      pin += key;
      $$('.pin-dot').forEach((dot, i) => {
        dot.classList.toggle('filled', i < pin.length);
      });
      if (pin.length >= 4) await doLogin();
    }
  }

  async function doLogin() {
    const uid = parseInt($('#login-uid').value);
    if (!uid) { error = 'Enter your User ID'; render(); return; }
    if (pin.length < 4) { error = 'PIN must be 4-6 digits'; render(); return; }
    try {
      const res = await fetch(API + '/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: uid, pin: pin }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        error = data.detail || 'Invalid credentials';
        pin = '';
        render();
        return;
      }
      const data = await res.json();
      saveAuth(data.access_token, data.user);
      navigate('dashboard');
    } catch (e) {
      error = 'Connection error';
      pin = '';
      render();
    }
  }

  render();
}

// ── DASHBOARD VIEW ──
function renderDashboard(container) {
  container.innerHTML = loading();
  const loc = state.locationId;
  const today = todayISO();

  Promise.allSettled([
    apiGet(`/production/needs?location_id=${loc}`),
    apiGet(`/batches/expiring?location_id=${loc}&hours=6`),
    apiGet(`/waste/summary?location_id=${loc}&date=${today}&period=daily`),
  ]).then(([needsR, batchesR, wasteR]) => {
    const needs = needsR.status === 'fulfilled' ? (needsR.value || []) : [];
    const batches = batchesR.status === 'fulfilled' ? (batchesR.value || []) : [];
    const waste = wasteR.status === 'fulfilled' ? wasteR.value : null;

    const needCount = needs.filter(n => n.needed > 0).length;
    const batchCount = batches.length;
    const wasteCost = waste ? Number(waste.total_waste_cost || 0) : 0;

    container.innerHTML = `
      <div class="metrics-row">
        <div class="metric metric--accent">
          <div class="metric-value">${needCount}</div>
          <div class="metric-label">To Produce</div>
        </div>
        <div class="metric metric--warning">
          <div class="metric-value">${batchCount}</div>
          <div class="metric-label">Expiring</div>
        </div>
        <div class="metric metric--danger">
          <div class="metric-value">${fmtCurrency(wasteCost)}</div>
          <div class="metric-label">Waste Today</div>
        </div>
      </div>

      <div class="quick-actions">
        <button class="quick-action" id="qa-waste">${ICONS.trash}<span>Log Waste</span></button>
        <button class="quick-action" id="qa-recipes">${ICONS.scale}<span>Scale Recipe</span></button>
      </div>

      ${batchCount > 0 ? `
        <div class="card">
          <div class="card-header"><span class="card-title">Expiring Soon</span>
            <span class="badge badge--warning">${batchCount}</span>
          </div>
          ${batches.slice(0, 8).map(b => `
            <div class="list-item">
              <div class="list-item-content">
                <div class="list-item-title">Recipe #${b.recipe_id}</div>
                <div class="list-item-sub">${b.quantity_remaining} remaining</div>
              </div>
              <div class="list-item-right">
                <div style="font-size:13px;color:var(--warning)">${fmtTime(b.expires_at)}</div>
                <span class="badge badge--${b.status === 'expired' ? 'danger' : 'warning'}">${b.status}</span>
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}

      ${needCount > 0 ? `
        <div class="card">
          <div class="card-header"><span class="card-title">Production Needs</span></div>
          ${needs.filter(n => n.needed > 0).slice(0, 10).map(n => `
            <div class="list-item" data-recipe="${n.recipe_id}" style="cursor:pointer">
              <div class="list-item-content">
                <div class="list-item-title">${escHtml(n.recipe_name || 'Recipe #' + n.recipe_id)}</div>
                <div class="list-item-sub">Par: ${n.effective_par} | Stock: ${n.current_stock}</div>
              </div>
              <div class="list-item-right">
                <span class="badge badge--accent">Need ${n.needed}</span>
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}

      ${waste && waste.by_category && Object.keys(waste.by_category).length > 0 ? `
        <div class="card">
          <div class="card-header"><span class="card-title">Waste by Category</span></div>
          <div class="bar-chart">
            ${renderBarChart(waste.by_category)}
          </div>
        </div>
      ` : ''}
    `;

    $('#qa-waste').addEventListener('click', () => navigate('waste'));
    $('#qa-recipes').addEventListener('click', () => navigate('recipes'));

    $$('[data-recipe]', container).forEach(el => {
      el.addEventListener('click', () => navigate('recipe', { id: el.dataset.recipe }));
    });
  });
}

function renderBarChart(data) {
  const entries = Object.entries(data);
  if (!entries.length) return '';
  const max = Math.max(...entries.map(([, v]) => Number(v)), 1);
  const colors = ['accent', 'warning', 'danger', 'info', 'accent', 'warning'];
  return entries.map(([label, value], i) => {
    const pct = (Number(value) / max * 100).toFixed(1);
    const color = colors[i % colors.length];
    return `<div class="bar-row">
      <span class="bar-label">${escHtml(label)}</span>
      <div class="bar-track"><div class="bar-fill bar-fill--${color}" style="width:${pct}%"></div></div>
      <span class="bar-value">${fmtCurrency(value)}</span>
    </div>`;
  }).join('');
}

// ── RECIPES VIEW ──
function renderRecipes(container) {
  container.innerHTML = loading();
  apiGet(`/recipes?location_id=${state.locationId}`).then(recipes => {
    if (!recipes) return;
    let filtered = recipes;

    function render(list) {
      container.innerHTML = `
        <div class="search-bar">
          ${ICONS.search}
          <input class="input" id="recipe-search" type="search" placeholder="Search recipes...">
        </div>
        ${list.length === 0 ? '<div class="empty-state"><div class="empty-state-text">No recipes found</div></div>' :
          list.map(r => `
            <div class="card list-item" data-id="${r.id}" style="cursor:pointer">
              <div class="list-item-content">
                <div class="list-item-title">${escHtml(r.name)}</div>
                <div class="list-item-sub">
                  ${r.category ? `<span class="badge badge--info">${escHtml(r.category)}</span> ` : ''}
                  Yield: ${r.base_yield}
                  ${r.total_time_minutes ? ` | ${r.total_time_minutes} min` : ''}
                </div>
              </div>
            </div>
          `).join('')}
      `;

      $('#recipe-search').addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase();
        filtered = recipes.filter(r =>
          r.name.toLowerCase().includes(q) ||
          (r.category || '').toLowerCase().includes(q) ||
          (r.tags || []).some(t => t.toLowerCase().includes(q))
        );
        render(filtered);
        const input = $('#recipe-search');
        if (input) { input.value = e.target.value; input.focus(); }
      });

      $$('[data-id]', container).forEach(el => {
        el.addEventListener('click', () => navigate('recipe', { id: el.dataset.id }));
      });
    }

    render(recipes);
  });
}

// ── RECIPE DETAIL VIEW ──
function renderRecipeDetail(container, recipeId) {
  if (!recipeId) { navigate('recipes'); return; }
  container.innerHTML = loading();

  apiGet(`/recipes/${recipeId}`).then(recipe => {
    if (!recipe) return;

    let scaleYield = recipe.base_yield;
    let scaledIngredients = null;

    function render() {
      const ings = scaledIngredients || recipe.ingredients || [];
      container.innerHTML = `
        <button class="back-btn" id="back-recipes">${ICONS.back} Recipes</button>
        <div class="recipe-header">
          <div class="recipe-name">${escHtml(recipe.name)}</div>
          <div class="recipe-meta">
            ${recipe.category ? `<span class="badge badge--info">${escHtml(recipe.category)}</span>` : ''}
            <span>Yield: ${recipe.base_yield}</span>
            ${recipe.prep_time_minutes ? `<span>${ICONS.clock} Prep ${recipe.prep_time_minutes}m</span>` : ''}
            ${recipe.cook_time_minutes ? `<span>${ICONS.clock} Cook ${recipe.cook_time_minutes}m</span>` : ''}
          </div>
        </div>

        <div class="scale-control">
          <label>Scale to:</label>
          <input class="input" type="number" id="scale-input" min="1"
            value="${scaleYield}" style="width:80px;text-align:center">
          <button class="btn btn--primary btn--sm" id="scale-btn">Scale</button>
        </div>

        <div class="recipe-section">
          <div class="recipe-section-title">Ingredients</div>
          ${ings.length === 0 ? '<div class="empty-state-text">No ingredients</div>' :
            ings.map(ing => `
              <div class="ingredient-row">
                <span>${escHtml(ing.ingredient_name || 'Ingredient #' + ing.ingredient_id)}</span>
                <span style="color:var(--text-muted)">
                  ${Number(ing.scaled_amount || ing.amount).toFixed(2)} ${escHtml(ing.unit)}
                </span>
              </div>
            `).join('')}
        </div>

        ${(recipe.steps || []).length > 0 ? `
          <div class="recipe-section">
            <div class="recipe-section-title">Steps</div>
            ${recipe.steps.sort((a,b) => a.step_order - b.step_order).map(s => `
              <div class="step-item">
                <div class="step-num">${s.step_order}</div>
                <div class="step-text">
                  ${escHtml(s.instruction)}
                  ${s.time_minutes ? `<span style="color:var(--text-dim)"> (${s.time_minutes}m)</span>` : ''}
                  ${s.temperature_c ? `<span style="color:var(--warning)"> ${s.temperature_c}C</span>` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        ` : ''}

        <div class="recipe-section" id="cost-section"></div>
        <div class="recipe-section" id="techniques-section"></div>
      `;

      $('#back-recipes').addEventListener('click', (e) => { e.preventDefault(); navigate('recipes'); });

      $('#scale-btn').addEventListener('click', async () => {
        const target = parseInt($('#scale-input').value);
        if (!target || target < 1) return;
        scaleYield = target;
        try {
          const scaled = await apiGet(`/recipes/${recipeId}/scale?target_yield=${target}`);
          if (scaled) {
            scaledIngredients = scaled.ingredients;
            render();
            toast('Scaled to ' + target, 'success');
          }
        } catch (e) { toast('Scale failed', 'error'); }
      });

      // Load cost
      apiGet(`/recipes/${recipeId}/cost`).then(cost => {
        if (!cost) return;
        const section = $('#cost-section');
        if (!section) return;
        section.innerHTML = `
          <div class="recipe-section-title">Cost Breakdown</div>
          <div style="display:flex;gap:16px;margin-bottom:12px">
            <div class="metric" style="flex:1">
              <div class="metric-value" style="font-size:20px">${fmtCurrency(cost.total_cost)}</div>
              <div class="metric-label">Total Cost</div>
            </div>
            <div class="metric" style="flex:1">
              <div class="metric-value" style="font-size:20px">${fmtCurrency(cost.cost_per_portion)}</div>
              <div class="metric-label">Per Portion</div>
            </div>
          </div>
        `;
      }).catch(() => {});

      // Load techniques
      apiGet(`/recipes/${recipeId}/techniques`).then(techs => {
        if (!techs || !techs.length) return;
        const section = $('#techniques-section');
        if (!section) return;
        section.innerHTML = `
          <div class="recipe-section-title">Techniques</div>
          ${techs.map(t => `
            <div class="list-item">
              <div class="list-item-content">
                <div class="list-item-title">${escHtml(t.technique_name || 'Technique #' + t.technique_id)}</div>
                ${t.step_order ? `<div class="list-item-sub">Step ${t.step_order}</div>` : ''}
              </div>
            </div>
          `).join('')}
        `;
      }).catch(() => {});
    }

    render();
  });
}

// ── PRODUCTION VIEW ──
function renderProduction(container) {
  container.innerHTML = loading();
  const loc = state.locationId;

  Promise.allSettled([
    apiGet(`/par-levels?location_id=${loc}`),
    apiGet(`/production/needs?location_id=${loc}`),
  ]).then(([parR, needsR]) => {
    const pars = parR.status === 'fulfilled' ? (parR.value || []) : [];
    const needs = needsR.status === 'fulfilled' ? (needsR.value || []) : [];

    container.innerHTML = `
      ${needs.length > 0 ? `
        <div class="card">
          <div class="card-header">
            <span class="card-title">Production Needs</span>
            <span class="badge badge--accent">${needs.filter(n => n.needed > 0).length}</span>
          </div>
          ${needs.filter(n => n.needed > 0).map(n => `
            <div class="list-item" data-recipe="${n.recipe_id}" style="cursor:pointer">
              <div class="list-item-content">
                <div class="list-item-title">${escHtml(n.recipe_name || 'Recipe #' + n.recipe_id)}</div>
                <div class="list-item-sub">Par: ${n.effective_par} | Stock: ${n.current_stock}</div>
              </div>
              <div class="list-item-right">
                <span class="badge badge--accent">Need ${n.needed}</span>
              </div>
            </div>
          `).join('')}
        </div>
      ` : '<div class="card"><div class="empty-state"><div class="empty-state-text">All production needs met</div></div></div>'}

      <div class="card">
        <div class="card-header">
          <span class="card-title">Par Levels</span>
          <span class="badge badge--muted">${pars.length}</span>
        </div>
        ${pars.length === 0 ? '<div class="empty-state-text">No par levels set</div>' :
          pars.map(p => `
            <div class="list-item">
              <div class="list-item-content">
                <div class="list-item-title">Recipe #${p.recipe_id}</div>
                <div class="list-item-sub">Base: ${p.base_par} | Buffer: ${p.safety_buffer}</div>
              </div>
              <div class="list-item-right">
                <div style="font-size:18px;font-weight:700;color:var(--accent)">${p.effective_par}</div>
                <div style="font-size:11px;color:var(--text-dim)">Effective</div>
              </div>
            </div>
          `).join('')}
      </div>
    `;

    $$('[data-recipe]', container).forEach(el => {
      el.addEventListener('click', () => navigate('recipe', { id: el.dataset.recipe }));
    });
  });
}

// ── WASTE VIEW ──
function renderWaste(container) {
  container.innerHTML = loading();
  const loc = state.locationId;
  const today = todayISO();

  // Load ingredients for the waste form dropdown
  Promise.allSettled([
    apiGet(`/waste/summary?location_id=${loc}&date=${today}&period=daily`),
    apiGet(`/waste/top-items?location_id=${loc}&days=7&limit=5`),
    apiGet(`/recipes?location_id=${loc}`),
    apiGet(`/ingredients?location_id=${loc}`),
  ]).then(([summaryR, topR, recipesR, ingredientsR]) => {
    const summary = summaryR.status === 'fulfilled' ? summaryR.value : null;
    const topItems = topR.status === 'fulfilled' ? (topR.value || []) : [];
    const recipes = recipesR.status === 'fulfilled' ? (recipesR.value || []) : [];
    const ingredients = ingredientsR.status === 'fulfilled' ? (ingredientsR.value || []) : [];

    container.innerHTML = `
      <div class="card">
        <div class="card-header"><span class="card-title">Log Waste</span></div>
        <form id="waste-form">
          <div class="form-group">
            <label class="form-label">Category</label>
            <select class="input" id="wf-category" required>
              <option value="">Select...</option>
              <option value="overproduction">Overproduction</option>
              <option value="spoilage">Spoilage</option>
              <option value="trim">Trim</option>
              <option value="plate">Plate Waste</option>
              <option value="cooking_loss">Cooking Loss</option>
              <option value="damaged">Damaged</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Item Type</label>
            <select class="input" id="wf-type">
              <option value="recipe">Recipe</option>
              <option value="ingredient">Ingredient</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Item</label>
            <select class="input" id="wf-item">
              ${recipes.map(r => `<option value="recipe:${r.id}">${escHtml(r.name)}</option>`).join('')}
            </select>
          </div>
          <div style="display:flex;gap:10px">
            <div class="form-group" style="flex:2">
              <label class="form-label">Quantity</label>
              <input class="input" type="number" id="wf-qty" step="0.01" min="0.01" required placeholder="0.00">
            </div>
            <div class="form-group" style="flex:1">
              <label class="form-label">Unit</label>
              <select class="input" id="wf-unit">
                <option value="kg">kg</option>
                <option value="g">g</option>
                <option value="L">L</option>
                <option value="units">units</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Reason (optional)</label>
            <input class="input" type="text" id="wf-reason" placeholder="Brief reason...">
          </div>
          <button class="btn btn--primary btn--full" type="submit">Log Waste</button>
        </form>
      </div>

      ${summary ? `
        <div class="card">
          <div class="card-header"><span class="card-title">Today's Summary</span></div>
          <div style="display:flex;gap:12px;margin-bottom:12px">
            <div class="metric" style="flex:1">
              <div class="metric-value metric--danger" style="font-size:20px;color:var(--danger)">${fmtCurrency(summary.total_waste_cost)}</div>
              <div class="metric-label">Total Cost</div>
            </div>
            <div class="metric" style="flex:1">
              <div class="metric-value" style="font-size:20px">${Number(summary.total_waste_kg || 0).toFixed(1)} kg</div>
              <div class="metric-label">Total Weight</div>
            </div>
          </div>
          ${summary.by_category && Object.keys(summary.by_category).length > 0 ? `
            <div class="bar-chart">${renderBarChart(summary.by_category)}</div>
          ` : ''}
        </div>
      ` : ''}

      ${topItems.length > 0 ? `
        <div class="card">
          <div class="card-header"><span class="card-title">Top Wasted (7 days)</span></div>
          ${topItems.map((item, i) => `
            <div class="list-item">
              <div style="width:24px;text-align:center;color:var(--text-dim);font-weight:600">${i + 1}</div>
              <div class="list-item-content">
                <div class="list-item-title">${escHtml(item.name || 'Unknown')}</div>
                <div class="list-item-sub">${item.occurrences} occurrences | ${Number(item.total_quantity).toFixed(1)} total</div>
              </div>
              <div class="list-item-right" style="color:var(--danger);font-weight:600">
                ${fmtCurrency(item.total_cost)}
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}
    `;

    // Toggle item dropdown between recipes and ingredients
    const typeSelect = $('#wf-type');
    const itemSelect = $('#wf-item');
    typeSelect.addEventListener('change', () => {
      if (typeSelect.value === 'ingredient') {
        itemSelect.innerHTML = ingredients.map(i =>
          `<option value="ingredient:${i.id}">${escHtml(i.name)}</option>`
        ).join('');
      } else {
        itemSelect.innerHTML = recipes.map(r =>
          `<option value="recipe:${r.id}">${escHtml(r.name)}</option>`
        ).join('');
      }
    });

    // Submit waste form
    $('#waste-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const [itemType, itemId] = ($('#wf-item').value || '').split(':');
      const body = {
        location_id: state.locationId,
        logged_by: state.user ? state.user.id : null,
        category: $('#wf-category').value,
        quantity: parseFloat($('#wf-qty').value),
        unit: $('#wf-unit').value,
        reason: $('#wf-reason').value || null,
      };
      if (itemType === 'recipe') body.recipe_id = parseInt(itemId);
      if (itemType === 'ingredient') body.ingredient_id = parseInt(itemId);

      try {
        await apiPost('/waste', body);
        toast('Waste logged', 'success');
        renderWaste(container); // refresh
      } catch (err) {
        toast('Failed to log waste', 'error');
      }
    });
  });
}

// ── KITCHEN DNA VIEW ──
function renderKitchenDNA(container) {
  container.innerHTML = loading();
  const loc = state.locationId;

  Promise.allSettled([
    apiGet(`/techniques/audit?location_id=${loc}`),
    apiGet(`/menu/dna-comparison?location_id=${loc}`),
  ]).then(([auditR, dnaR]) => {
    const audit = auditR.status === 'fulfilled' ? auditR.value : null;
    const dna = dnaR.status === 'fulfilled' ? dnaR.value : null;

    container.innerHTML = `
      ${audit ? `
        <div class="card" style="text-align:center">
          <div class="card-title" style="margin-bottom:12px">Technique Score</div>
          <div style="font-size:48px;font-weight:800;color:var(--accent)">${Number(audit.overall_score).toFixed(1)}</div>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:16px">
            ${audit.in_use_count} of ${audit.total_techniques} techniques in use
          </div>
          ${audit.by_category && Object.keys(audit.by_category).length > 0 ? `
            <div class="bar-chart" style="text-align:left">
              ${Object.entries(audit.by_category).map(([cat, score], i) => {
                const pct = (Number(score) / 10 * 100).toFixed(0);
                const colors = ['accent', 'info', 'warning', 'danger', 'accent', 'info', 'warning'];
                return `<div class="bar-row">
                  <span class="bar-label">${escHtml(cat)}</span>
                  <div class="bar-track"><div class="bar-fill bar-fill--${colors[i % colors.length]}" style="width:${pct}%"></div></div>
                  <span class="bar-value">${Number(score).toFixed(1)}</span>
                </div>`;
              }).join('')}
            </div>
          ` : ''}
        </div>

        ${audit.suggestions && audit.suggestions.length > 0 ? `
          <div class="card">
            <div class="card-header"><span class="card-title">Suggestions</span></div>
            ${audit.suggestions.map(s => `
              <div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:14px;color:var(--text-muted)">
                ${escHtml(s)}
              </div>
            `).join('')}
          </div>
        ` : ''}

        ${audit.underused && audit.underused.length > 0 ? `
          <div class="card">
            <div class="card-header"><span class="card-title">Underused Techniques</span></div>
            ${audit.underused.slice(0, 8).map(t => `
              <div class="list-item">
                <div class="list-item-content">
                  <div class="list-item-title">${escHtml(t.name)}</div>
                  <div class="list-item-sub">${escHtml(t.category)}${t.difficulty_level ? ' | Difficulty ' + t.difficulty_level : ''}</div>
                </div>
                <span class="badge badge--muted">Unused</span>
              </div>
            `).join('')}
          </div>
        ` : ''}
      ` : '<div class="card"><div class="empty-state"><div class="empty-state-text">No technique data available</div></div></div>'}

      ${dna && dna.pairs && dna.pairs.length > 0 ? `
        <div class="card">
          <div class="card-header"><span class="card-title">DNA Similarity</span></div>
          ${dna.pairs.sort((a, b) => b.similarity - a.similarity).slice(0, 15).map(p => {
            const sim = Number(p.similarity);
            const color = sim > 0.7 ? 'danger' : sim > 0.4 ? 'warning' : 'accent';
            return `<div class="list-item">
              <div class="list-item-content">
                <div class="list-item-title">${escHtml(p.recipe_a_name || '#' + p.recipe_a_id)} vs ${escHtml(p.recipe_b_name || '#' + p.recipe_b_id)}</div>
              </div>
              <span class="badge badge--${color}">${(sim * 100).toFixed(0)}%</span>
            </div>`;
          }).join('')}
        </div>
      ` : ''}
    `;
  });
}

// ── INIT ──
function init() {
  // Register service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }

  // Load auth state
  const authed = loadAuth();
  if (!authed && !window.location.hash.includes('login')) {
    navigate('login');
  } else {
    route();
  }
}

// Boot
document.addEventListener('DOMContentLoaded', init);

