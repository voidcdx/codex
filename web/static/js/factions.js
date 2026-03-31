'use strict';

/* ── Data ─────────────────────────────────────────────── */

const ALL_DAMAGE_TYPES = [
  'impact', 'puncture', 'slash',
  'heat', 'cold', 'electricity', 'toxin',
  'blast', 'corrosive', 'gas', 'magnetic', 'radiation', 'viral',
];

const FACTION_NAMES = {
  grineer:         'Grineer',
  kuva_grineer:    'Kuva Grineer',
  corpus:          'Corpus',
  corpus_amalgam:  'Corpus Amalgam',
  infested:        'Infested',
  deimos_infested: 'Deimos Infested',
  corrupted:       'Corrupted',
  sentient:        'Sentient',
  narmer:          'Narmer',
  themurmur:       'The Murmur',
  scaldra:         'Scaldra',
  techrot:         'Techrot',
  anarchs:         'Anarchs',
};

const FACTION_KEYS = Object.keys(FACTION_NAMES);

const FACTION_GROUPS = {
  grineer:  ['grineer', 'kuva_grineer', 'scaldra', 'anarchs'],
  corpus:   ['corpus', 'corpus_amalgam', 'techrot'],
  infested: ['infested', 'deimos_infested'],
  other:    ['corrupted', 'sentient', 'narmer', 'themurmur'],
};

// Game-faction data colors — used for row borders and group tags only
const FACTION_GROUP_COLORS = {
  grineer:  '#c07020',
  corpus:   '#4090c0',
  infested: '#60a030',
  other:    '#9060c0',
};

function getFactionGroup(key) {
  for (const [group, keys] of Object.entries(FACTION_GROUPS)) {
    if (keys.includes(key)) return group;
  }
  return 'other';
}

/* ── State ────────────────────────────────────────────── */

let currentFilter = 'all';   // 'all' | 'weak' | 'resist'
let currentSearch = '';       // lowercase
let currentView   = 'matrix'; // 'matrix' | 'cards'
let currentGroup  = 'all';    // 'all' | 'grineer' | 'corpus' | 'infested' | 'other'

/* ── Helpers ──────────────────────────────────────────── */

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function elemIconSvg(type, cls) {
  const inner = (DMG_ICONS && DMG_ICONS[type]) || '';
  return `<svg class="${cls}" viewBox="0 0 16 16" aria-hidden="true">${inner}</svg>`;
}

function getEffectiveness(factionKey, dmgType) {
  const data = FACTION_EFFECTIVENESS[factionKey];
  if (!data) return 1.0;
  return data[dmgType] || 1.0;
}

/* ── Matrix render ────────────────────────────────────── */

function renderMatrix() {
  const matrix = document.getElementById('faction-matrix');
  if (!matrix) return;

  const cells = [];

  // Corner
  cells.push(`<div class="matrix-corner"><span class="matrix-corner-label">Faction / Damage</span></div>`);

  // Column headers
  ALL_DAMAGE_TYPES.forEach((dmgType, colIdx) => {
    cells.push(
      `<div class="matrix-col-header" data-dmg-type="${dmgType}" data-col-index="${colIdx}">` +
        elemIconSvg(dmgType, 'col-icon') +
        `<span class="col-name">${esc(dmgType)}</span>` +
      `</div>`
    );
  });

  // Rows
  FACTION_KEYS.forEach((factionKey, rowIdx) => {
    const group = getFactionGroup(factionKey);
    // Row label
    cells.push(
      `<div class="matrix-row-label" data-faction="${factionKey}" data-row-index="${rowIdx}" data-group="${group}">` +
        `<span class="faction-name">${esc(FACTION_NAMES[factionKey])}</span>` +
      `</div>`
    );

    // Data cells
    ALL_DAMAGE_TYPES.forEach((dmgType, colIdx) => {
      const eff = getEffectiveness(factionKey, dmgType);
      let cellClass = 'cell-neutral';
      let label = '';
      if (eff === 1.5) { cellClass = 'cell-weak';   label = '+50%'; }
      if (eff === 0.5) { cellClass = 'cell-resist'; label = '−50%'; }

      cells.push(
        `<div class="matrix-cell ${cellClass}" ` +
          `data-faction="${factionKey}" data-dmg-type="${dmgType}" ` +
          `data-row-index="${rowIdx}" data-col-index="${colIdx}">` +
          (label ? `<span class="cell-label">${label}</span>` : '') +
        `</div>`
      );
    });
  });

  matrix.innerHTML = cells.join('');

  // Apply element colors via CSS custom property (not inline style attrs)
  matrix.querySelectorAll('[data-dmg-type]').forEach(el => {
    const type = el.dataset.dmgType;
    const color = (ELEM_COLORS && ELEM_COLORS[type]) || '#888';
    el.style.setProperty('--elem-color', color);
  });

  // Apply faction group colors to row labels
  matrix.querySelectorAll('.matrix-row-label').forEach(el => {
    const color = FACTION_GROUP_COLORS[el.dataset.group] || '';
    if (color) el.style.setProperty('--faction-color', color);
  });

  attachMatrixHover();
}

/* ── Cards render ─────────────────────────────────────── */

function renderCards() {
  const wrap = document.getElementById('faction-view-cards');
  if (!wrap) return;

  const cards = FACTION_KEYS.map(factionKey => {
    const data = FACTION_EFFECTIVENESS[factionKey] || {};
    const group = getFactionGroup(factionKey);

    let html = `<div class="panel faction-card" data-faction="${factionKey}" data-group="${group}">`;

    // Header
    html += `<div class="card-faction-header">`;
    html += `<span class="card-faction-name">${esc(FACTION_NAMES[factionKey])}</span>`;
    html += `<span class="card-faction-group">${esc(group)}</span>`;
    html += `</div>`;

    // Damage profile strip — all 13 types in one row
    html += `<div class="card-dmg-strip">`;
    ALL_DAMAGE_TYPES.forEach(t => {
      const eff = data[t] || 1.0;
      let mod = '';
      if (eff === 1.5) mod = 'strip-item--weak';
      if (eff === 0.5) mod = 'strip-item--resist';

      html += `<div class="strip-item ${mod}" data-dmg-type="${t}">`;
      html += elemIconSvg(t, 'strip-icon');
      if (eff !== 1.0) {
        html += `<span class="strip-mult">${eff === 1.5 ? '+50' : '−50'}</span>`;
      }
      html += `</div>`;
    });
    html += `</div>`;

    html += `</div>`;
    return html;
  });

  wrap.innerHTML = cards.join('');

  // Apply element colors
  wrap.querySelectorAll('[data-dmg-type]').forEach(el => {
    const type = el.dataset.dmgType;
    const color = (ELEM_COLORS && ELEM_COLORS[type]) || '#888';
    el.style.setProperty('--elem-color', color);
  });

  // Apply faction group + element colors
  wrap.querySelectorAll('.faction-card').forEach(card => {
    const color = FACTION_GROUP_COLORS[card.dataset.group] || '';
    if (color) {
      card.style.setProperty('--faction-color', color);
    }
  });
}

/* ── Filter ───────────────────────────────────────────── */

function applyFilter() {
  // ── Matrix ──
  const matrixEl = document.getElementById('faction-matrix');
  if (matrixEl) {
    const rowLabels = matrixEl.querySelectorAll('.matrix-row-label');
    rowLabels.forEach(label => {
      const key  = label.dataset.faction;
      const name = (FACTION_NAMES[key] || key).toLowerCase();
      const searchMatch = !currentSearch || name.includes(currentSearch);
      const groupMatch  = currentGroup === 'all' || label.dataset.group === currentGroup;
      label.classList.toggle('hidden', !searchMatch || !groupMatch);
    });

    const cells = matrixEl.querySelectorAll('.matrix-cell');
    cells.forEach(cell => {
      const key       = cell.dataset.faction;
      const name      = (FACTION_NAMES[key] || key).toLowerCase();
      const searchMatch = !currentSearch || name.includes(currentSearch);
      const rowLabel  = matrixEl.querySelector(`.matrix-row-label[data-faction="${key}"]`);
      const groupMatch  = currentGroup === 'all' || (rowLabel && rowLabel.dataset.group === currentGroup);
      if (!searchMatch || !groupMatch) { cell.classList.add('hidden'); return; }

      const isWeak   = cell.classList.contains('cell-weak');
      const isResist = cell.classList.contains('cell-resist');

      let show = true;
      if (currentFilter === 'weak')   show = isWeak;
      if (currentFilter === 'resist') show = isResist;
      cell.classList.toggle('hidden', !show);
    });

    // Hide column headers if every visible row's cell is hidden
    const colHeaders = matrixEl.querySelectorAll('.matrix-col-header');
    colHeaders.forEach(hdr => {
      const dmgType = hdr.dataset.dmgType;
      const visibleCells = matrixEl.querySelectorAll(
        `.matrix-cell[data-dmg-type="${dmgType}"]:not(.hidden)`
      );
      // Also check if those cells are for visible rows
      let anyVisible = false;
      visibleCells.forEach(c => {
        const rowLabel = matrixEl.querySelector(`.matrix-row-label[data-faction="${c.dataset.faction}"]`);
        if (rowLabel && !rowLabel.classList.contains('hidden')) anyVisible = true;
      });
      hdr.classList.toggle('hidden', !anyVisible && currentFilter !== 'all');
    });
  }

  // ── Cards ──
  const cardsWrap = document.getElementById('faction-view-cards');
  if (cardsWrap) {
    cardsWrap.querySelectorAll('.faction-card').forEach(card => {
      const key  = card.dataset.faction;
      const name = (FACTION_NAMES[key] || key).toLowerCase();
      const searchMatch = !currentSearch || name.includes(currentSearch);
      const groupMatch  = currentGroup === 'all' || card.dataset.group === currentGroup;

      if (!searchMatch || !groupMatch) { card.classList.add('card-hidden'); return; }

      const data       = FACTION_EFFECTIVENESS[key] || {};
      const hasWeak    = Object.values(data).some(v => v === 1.5);
      const hasResist  = Object.values(data).some(v => v === 0.5);

      let show = true;
      if (currentFilter === 'weak')   show = hasWeak;
      if (currentFilter === 'resist') show = hasResist;
      card.classList.toggle('card-hidden', !show);
    });

    // Empty state
    const anyVisible = cardsWrap.querySelectorAll('.faction-card:not(.card-hidden)').length;
    let emptyEl = cardsWrap.querySelector('.factions-empty');
    if (!anyVisible) {
      if (!emptyEl) {
        emptyEl = document.createElement('div');
        emptyEl.className = 'factions-empty';
        cardsWrap.appendChild(emptyEl);
      }
      emptyEl.textContent = 'No factions match';
    } else if (emptyEl) {
      emptyEl.remove();
    }
  }
}

/* ── View toggle ──────────────────────────────────────── */

function setView(v) {
  currentView = v;
  const matrixWrap = document.getElementById('faction-view-matrix');
  const cardsWrap  = document.getElementById('faction-view-cards');
  const btn        = document.getElementById('view-toggle');

  if (matrixWrap) matrixWrap.classList.toggle('hidden', v !== 'matrix');
  if (cardsWrap)  cardsWrap.classList.toggle('hidden',  v !== 'cards');
  if (btn) btn.textContent = v === 'matrix' ? 'Cards' : 'Matrix';
}

function cycleView() {
  setView(currentView === 'matrix' ? 'cards' : 'matrix');
}

/* ── Hover highlighting ───────────────────────────────── */

function attachMatrixHover() {
  const matrix = document.getElementById('faction-matrix');
  if (!matrix) return;

  matrix.querySelectorAll('.matrix-row-label').forEach(label => {
    const rowIdx = label.dataset.rowIndex;
    const cells  = matrix.querySelectorAll(`.matrix-cell[data-row-index="${rowIdx}"]`);
    label.addEventListener('mouseenter', () => {
      label.classList.add('row-hovered');
      cells.forEach(c => c.classList.add('row-hovered'));
    });
    label.addEventListener('mouseleave', () => {
      label.classList.remove('row-hovered');
      cells.forEach(c => c.classList.remove('row-hovered'));
    });
  });

  matrix.querySelectorAll('.matrix-col-header').forEach(hdr => {
    const dmgType = hdr.dataset.dmgType;
    const cells   = matrix.querySelectorAll(`.matrix-cell[data-dmg-type="${dmgType}"]`);
    hdr.addEventListener('mouseenter', () => {
      hdr.classList.add('col-hovered');
      cells.forEach(c => c.classList.add('col-hovered'));
    });
    hdr.addEventListener('mouseleave', () => {
      hdr.classList.remove('col-hovered');
      cells.forEach(c => c.classList.remove('col-hovered'));
    });
  });
}

/* ── Event handlers ───────────────────────────────────── */

function setFilter(btn) {
  document.querySelectorAll('#type-pills .filter-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentFilter = btn.dataset.filter;
  applyFilter();
}

function setGroup(btn) {
  document.querySelectorAll('#group-pills .filter-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentGroup = btn.dataset.group;
  applyFilter();
}

function clearSearch() {
  const input = document.getElementById('faction-search');
  if (input) { input.value = ''; }
  const wrap = document.getElementById('faction-search-wrap');
  if (wrap) wrap.classList.remove('has-value');
  currentSearch = '';
  applyFilter();
  if (input) input.focus();
}

/* ── Sidebar drawer (same pattern as live.html) ───────── */

function toggleDrawer() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const btn     = document.getElementById('burger-btn');
  const open    = sidebar.classList.toggle('open');
  overlay.classList.toggle('open', open);
  btn.classList.toggle('open', open);
}

function openGuide() {}

/* ── Init ─────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  renderMatrix();
  renderCards();

  // Default to cards on mobile
  if (window.innerWidth <= 768) {
    setView('cards');
  }

  applyFilter();

  // Search
  const searchInput = document.getElementById('faction-search');
  const searchWrap  = document.getElementById('faction-search-wrap');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      currentSearch = searchInput.value.trim().toLowerCase();
      if (searchWrap) searchWrap.classList.toggle('has-value', currentSearch.length > 0);
      applyFilter();
    });
  }

  // Version badge
  fetch('/api/version')
    .then(r => r.json())
    .then(d => {
      const el = document.getElementById('nav-ver');
      if (el) el.textContent = 'v' + d.app;
    })
    .catch(() => {});
});
