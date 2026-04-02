/* Reliquary — relic browser */

const PAGE_SIZE = 50;
let allRelics   = [];
let dropsMap    = {};
let activeTier  = 'all';
let activeVault = 'unvaulted';
let searchQuery = '';
let currentPage = 0;

// ---------------------------------------------------------------------------
// Data load
// ---------------------------------------------------------------------------
async function loadRelics() {
  try {
    const [relicsResp, dropsResp] = await Promise.all([
      fetch('/api/relics'),
      fetch('/api/drops'),
    ]);
    allRelics = await relicsResp.json();
    try { dropsMap = await dropsResp.json(); } catch { dropsMap = {}; }
    renderGrid();
  } catch (e) {
    document.getElementById('relic-grid').innerHTML =
      '<div class="relic-empty">Failed to load relic data.</div>';
  }
}

// ---------------------------------------------------------------------------
// Filters
// ---------------------------------------------------------------------------
function setTier(btn) {
  document.querySelectorAll('#tier-pills .relic-tier-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeTier = btn.dataset.tier;
  currentPage = 0;
  renderGrid();
}

function setVault(btn) {
  document.querySelectorAll('#vault-menu .vault-drop-item').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeVault = btn.dataset.vault;
  // Accent the circle button when filter is active
  const vaultBtn = document.getElementById('vault-toggle');
  if (vaultBtn) {
    vaultBtn.classList.toggle('active',  activeVault === 'unvaulted');
    vaultBtn.classList.toggle('vaulted', activeVault === 'vaulted');
  }
  // Close dropdown
  document.getElementById('vault-wrap').classList.remove('open');
  currentPage = 0;
  renderGrid();
}

function clearSearch() {
  const input = document.getElementById('relic-search');
  const wrap  = document.getElementById('relic-search-wrap');
  input.value = '';
  wrap.classList.remove('has-value', 'open');
  searchQuery = '';
  currentPage = 0;
  renderGrid();
}

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function highlight(text, query) {
  if (!query) return esc(text);
  const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')})`, 'gi');
  return esc(text).replace(re, '<mark>$1</mark>');
}

function matchesSearch(relic, q) {
  if (!q) return true;
  const ql = q.toLowerCase();
  return relic.name.toLowerCase().includes(ql) ||
    relic.rewards.some(r =>
      r.item.toLowerCase().includes(ql) || r.part.toLowerCase().includes(ql)
    );
}

const DROPS_SHOW = 5;

function renderDropSection(relic) {
  const drops = dropsMap[relic.name];
  if (!drops || drops.length === 0) return '';

  const renderRow = d => {
    const rot = d.rotation
      ? `<span class="drop-rotation">Rot ${esc(d.rotation)}</span>`
      : '';
    const rarityClass = esc(d.rarity.replace(/\s+/g, '-'));
    const chance = Number(d.chance).toFixed(2);
    return `<div class="drop-row rarity-drop-${rarityClass}">
      <span class="drop-loc">${esc(d.location)}</span>
      <span class="drop-mission">${esc(d.mission_type)}</span>
      ${rot}
      <span class="drop-chance">${chance}%</span>
    </div>`;
  };

  const top5 = drops.slice(0, DROPS_SHOW);
  const id = `drops-${esc(relic.name.replace(/\s+/g, '-'))}`;

  return `<div class="relic-drops-section" id="${id}">
    <button class="relic-drops-toggle" onclick="toggleDrops(this)" type="button">
      Drop Locations<span class="drop-count">${drops.length}</span>
      <svg class="drop-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4,6 8,10 12,6"/></svg>
    </button>
    <div class="drop-list" hidden>
      ${top5.map(renderRow).join('')}
    </div>
  </div>`;
}

function toggleDrops(btn) {
  const list = btn.nextElementSibling;
  const open = list.hasAttribute('hidden');
  list.toggleAttribute('hidden', !open);
  btn.classList.toggle('open', open);
}

function renderCard(relic, query) {
  const rewardRows = relic.rewards.map(r => {
    return `<div class="reward-row rarity-${esc(r.rarity)}">
      <span class="reward-dot"></span>
      <span class="reward-name">${highlight(r.item, query)}${r.part ? ` <span class="reward-part">${highlight(r.part, query)}</span>` : ''}</span>
    </div>`;
  }).join('');

  const badges = [
    relic.vaulted  ? '<span class="relic-badge vaulted">Vaulted</span>' : '',
    relic.is_baro  ? '<span class="relic-badge baro">Baro</span>' : '',
  ].join('');

  return `<div class="relic-card" data-tier="${esc(relic.tier)}">
    <div class="relic-card-header">
      <div class="relic-tier-bar"></div>
      <span class="relic-tier-badge">${esc(relic.tier)}</span>
      <span class="relic-name">${highlight(relic.name.replace(/^(Lith|Meso|Neo|Axi|Requiem|Vanguard)\s+/i, ''), query)}</span>
      <div class="relic-badges">${badges}</div>
    </div>
    <div class="relic-rewards">${rewardRows}</div>
    ${renderDropSection(relic)}
  </div>`;
}

function renderPagination(page, total, countText) {
  const el = document.getElementById('relic-pagination');
  if (!el) return;
  const countRow = countText ? `<div class="relic-count">${countText}</div>` : '';
  if (total <= 1) { el.innerHTML = countRow; return; }
  el.innerHTML = `
    <div class="relic-page-controls">
      <button class="relic-page-btn" onclick="goToPage(${page - 1})" ${page === 0 ? 'disabled' : ''}>
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="10,3 5,8 10,13"/></svg>
        Prev
      </button>
      <span class="relic-page-info">Page ${page + 1} of ${total}</span>
      <button class="relic-page-btn" onclick="goToPage(${page + 1})" ${page === total - 1 ? 'disabled' : ''}>
        Next
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6,3 11,8 6,13"/></svg>
      </button>
    </div>
    ${countRow}
  `;
}

function goToPage(n) {
  currentPage = n;
  renderGrid();
  if (window.innerWidth <= 900) {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else {
    const wrap = document.querySelector('.factions-wrap');
    if (wrap) wrap.scrollTop = 0;
  }
}

function renderGrid() {
  const q = searchQuery.trim().toLowerCase();

  const filtered = allRelics.filter(r => {
    if (activeTier !== 'all' && r.tier !== activeTier) return false;
    if (activeVault === 'unvaulted' && r.vaulted) return false;
    if (activeVault === 'vaulted'   && !r.vaulted) return false;
    if (!matchesSearch(r, q)) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  currentPage = Math.min(currentPage, totalPages - 1);

  const start = currentPage * PAGE_SIZE;
  const pageItems = filtered.slice(start, start + PAGE_SIZE);

  const end = Math.min(start + PAGE_SIZE, filtered.length);
  const countText = filtered.length === 0 ? '0 relics'
    : totalPages === 1 ? `${filtered.length} relics`
    : `${start + 1}–${end} of ${filtered.length} relics`;

  const grid = document.getElementById('relic-grid');
  if (filtered.length === 0) {
    grid.innerHTML = '<div class="relic-empty">No relics match your filters.</div>';
    renderPagination(0, 0, countText);
    return;
  }

  grid.innerHTML = pageItems.map(r => renderCard(r, q)).join('');
  renderPagination(currentPage, totalPages, countText);
}

// ---------------------------------------------------------------------------
// Version + sidebar
// ---------------------------------------------------------------------------
function openGuide() {}  // stub — no guide modal on this page yet

function toggleDrawer() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const btn     = document.getElementById('burger-btn');
  const open    = sidebar.classList.toggle('open');
  if (overlay) overlay.classList.toggle('open', open);
  if (btn)     btn.classList.toggle('open', open);
}

async function loadVersion() {
  try {
    const v = await fetch('/api/version').then(r => r.json());
    const el = document.getElementById('nav-ver');
    if (el) el.textContent = `v${v.app}`;
  } catch {}
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  loadRelics();
  loadVersion();

  const searchInput  = document.getElementById('relic-search');
  const searchWrap   = document.getElementById('relic-search-wrap');
  const searchToggle = document.getElementById('search-toggle');

  function closePill() {
    searchWrap.classList.remove('open');
    searchInput.blur();
  }

  searchToggle.addEventListener('click', () => {
    const isOpen = searchWrap.classList.toggle('open');
    if (isOpen) searchInput.focus();
    else closePill();
  });

  document.getElementById('search-clear').addEventListener('click', clearSearch);

  const vaultWrap   = document.getElementById('vault-wrap');
  const vaultToggle = document.getElementById('vault-toggle');

  vaultToggle.addEventListener('click', () => {
    vaultWrap.classList.toggle('open');
  });

  document.addEventListener('click', e => {
    if (searchWrap.classList.contains('open') && !searchWrap.contains(e.target)) {
      closePill();
    }
    if (vaultWrap.classList.contains('open') && !vaultWrap.contains(e.target)) {
      vaultWrap.classList.remove('open');
    }
  });

  searchInput.addEventListener('keydown', e => {
    if (e.key === 'Escape') clearSearch();
    if (e.key === 'Enter') closePill();
  });

  searchInput.addEventListener('input', () => {
    searchQuery = searchInput.value;
    searchWrap.classList.toggle('has-value', searchQuery.length > 0);
    currentPage = 0;
    renderGrid();
  });
});
