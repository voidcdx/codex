/* Reliquary — relic browser */

const PAGE_SIZE = 50;
let allRelics   = [];
let activeTier  = 'all';
let activeVault = 'unvaulted';
let searchQuery = '';
let currentPage = 0;

// ---------------------------------------------------------------------------
// Data load
// ---------------------------------------------------------------------------
async function loadRelics() {
  try {
    const resp = await fetch('/api/relics');
    allRelics = await resp.json();
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
  document.querySelectorAll('#vault-pills .vault-seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeVault = btn.dataset.vault;
  currentPage = 0;
  renderGrid();
}

function clearSearch() {
  document.getElementById('relic-search').value = '';
  document.getElementById('relic-search-wrap').classList.remove('has-value');
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
  </div>`;
}

function renderPagination(page, total) {
  const el = document.getElementById('relic-pagination');
  if (!el) return;
  if (total <= 1) { el.innerHTML = ''; return; }
  el.innerHTML = `
    <button class="relic-page-btn" onclick="goToPage(${page - 1})" ${page === 0 ? 'disabled' : ''}>← Prev</button>
    <span class="relic-page-info">Page ${page + 1} of ${total}</span>
    <button class="relic-page-btn" onclick="goToPage(${page + 1})" ${page === total - 1 ? 'disabled' : ''}>Next →</button>
  `;
}

function goToPage(n) {
  currentPage = n;
  renderGrid();
  const wrap = document.querySelector('.factions-wrap');
  if (wrap) wrap.scrollTop = 0;
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

  const countEl = document.getElementById('relic-count');
  if (countEl) {
    const end = Math.min(start + PAGE_SIZE, filtered.length);
    if (filtered.length === 0) {
      countEl.textContent = '0 relics';
    } else if (totalPages === 1) {
      countEl.textContent = `${filtered.length} relics`;
    } else {
      countEl.textContent = `${start + 1}–${end} of ${filtered.length}`;
    }
  }

  const grid = document.getElementById('relic-grid');
  if (filtered.length === 0) {
    grid.innerHTML = '<div class="relic-empty">No relics match your filters.</div>';
    renderPagination(0, 0);
    return;
  }

  grid.innerHTML = pageItems.map(r => renderCard(r, q)).join('');
  renderPagination(currentPage, totalPages);
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

  const searchInput = document.getElementById('relic-search');
  const searchWrap  = document.getElementById('relic-search-wrap');
  searchInput.addEventListener('input', () => {
    searchQuery = searchInput.value;
    searchWrap.classList.toggle('has-value', searchQuery.length > 0);
    currentPage = 0;
    renderGrid();
  });
});
