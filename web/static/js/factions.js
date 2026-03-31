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

const FACTION_GROUP_COLORS = {
  grineer:  '#c07828',
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

let currentFilter = 'all';  // 'all' | 'weak' | 'resist'
let currentSearch = '';      // lowercase
let currentGroup  = 'all';  // 'all' | 'grineer' | 'corpus' | 'infested' | 'other'

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

/* ── Roster render ────────────────────────────────────── */

function renderRoster() {
  const roster = document.getElementById('faction-roster');
  if (!roster) return;

  const groupOrder = ['grineer', 'corpus', 'infested', 'other'];
  let html = '';

  groupOrder.forEach(group => {
    const factionKeysInGroup = FACTION_GROUPS[group] || [];
    const groupColor = FACTION_GROUP_COLORS[group] || '';

    html += `<div class="roster-group" data-group="${group}">`;
    html += `<div class="roster-group-label">${esc(group)}</div>`;

    factionKeysInGroup.forEach(factionKey => {
      if (!FACTION_NAMES[factionKey]) return;
      const data = FACTION_EFFECTIVENESS[factionKey] || {};
      const weakTypes   = ALL_DAMAGE_TYPES.filter(t => data[t] === 1.5);
      const resistTypes = ALL_DAMAGE_TYPES.filter(t => data[t] === 0.5);

      html += `<div class="roster-entry" data-faction="${factionKey}" data-group="${group}">`;
      html += `<div class="roster-info"><span class="roster-name">${esc(FACTION_NAMES[factionKey])}</span></div>`;
      html += `<div class="roster-dmg">`;

      weakTypes.forEach(t => {
        html += `<div class="dmg-item dmg-weak" data-dmg-type="${t}">`;
        html += elemIconSvg(t, 'dmg-item-icon');
        html += `<span class="dmg-item-name">${esc(t)}</span>`;
        html += `<span class="dmg-item-mult">×1.5</span>`;
        html += `</div>`;
      });

      if (weakTypes.length && resistTypes.length) {
        html += `<div class="dmg-sep"></div>`;
      }

      resistTypes.forEach(t => {
        html += `<div class="dmg-item dmg-resist" data-dmg-type="${t}">`;
        html += elemIconSvg(t, 'dmg-item-icon');
        html += `<span class="dmg-item-name">${esc(t)}</span>`;
        html += `<span class="dmg-item-mult">×0.5</span>`;
        html += `</div>`;
      });

      html += `</div></div>`; // .roster-dmg, .roster-entry
    });

    html += `</div>`; // .roster-group
  });

  roster.innerHTML = html;

  // Apply element colors
  roster.querySelectorAll('[data-dmg-type]').forEach(el => {
    const color = (ELEM_COLORS && ELEM_COLORS[el.dataset.dmgType]) || '#888';
    el.style.setProperty('--elem-color', color);
  });

  // Apply faction group colors
  roster.querySelectorAll('.roster-entry').forEach(el => {
    const color = FACTION_GROUP_COLORS[el.dataset.group] || '';
    if (color) el.style.setProperty('--faction-color', color);
  });

  roster.querySelectorAll('.roster-group-label').forEach(el => {
    const group = el.closest('.roster-group').dataset.group;
    const color = FACTION_GROUP_COLORS[group] || '';
    if (color) el.style.setProperty('--faction-color', color);
  });
}

/* ── Filter ───────────────────────────────────────────── */

function applyFilter() {
  const roster = document.getElementById('faction-roster');
  if (!roster) return;

  let anyVisible = false;

  roster.querySelectorAll('.roster-entry').forEach(entry => {
    const key       = entry.dataset.faction;
    const name      = (FACTION_NAMES[key] || key).toLowerCase();
    const searchMatch = !currentSearch || name.includes(currentSearch);
    const groupMatch  = currentGroup === 'all' || entry.dataset.group === currentGroup;

    const data      = FACTION_EFFECTIVENESS[key] || {};
    const hasWeak   = Object.values(data).some(v => v === 1.5);
    const hasResist = Object.values(data).some(v => v === 0.5);
    let typeMatch   = true;
    if (currentFilter === 'weak')   typeMatch = hasWeak;
    if (currentFilter === 'resist') typeMatch = hasResist;

    const show = searchMatch && groupMatch && typeMatch;
    entry.classList.toggle('entry-hidden', !show);
    if (show) anyVisible = true;
  });

  // Hide group sections that have no visible entries
  roster.querySelectorAll('.roster-group').forEach(group => {
    const hasVisible = group.querySelectorAll('.roster-entry:not(.entry-hidden)').length > 0;
    const groupKey   = group.dataset.group;
    const groupMatch = currentGroup === 'all' || groupKey === currentGroup;
    group.classList.toggle('group-hidden', !hasVisible || !groupMatch);
  });

  // Empty state
  let emptyEl = roster.querySelector('.factions-empty');
  if (!anyVisible) {
    if (!emptyEl) {
      emptyEl = document.createElement('div');
      emptyEl.className = 'factions-empty';
      roster.appendChild(emptyEl);
    }
    emptyEl.textContent = 'No factions match';
  } else if (emptyEl) {
    emptyEl.remove();
  }
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
  if (input) input.value = '';
  const wrap = document.getElementById('faction-search-wrap');
  if (wrap) wrap.classList.remove('has-value');
  currentSearch = '';
  applyFilter();
  if (input) input.focus();
}

/* ── Sidebar drawer ───────────────────────────────────── */

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
  renderRoster();
  applyFilter();

  const searchInput = document.getElementById('faction-search');
  const searchWrap  = document.getElementById('faction-search-wrap');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      currentSearch = searchInput.value.trim().toLowerCase();
      if (searchWrap) searchWrap.classList.toggle('has-value', currentSearch.length > 0);
      applyFilter();
    });
  }

  fetch('/api/version')
    .then(r => r.json())
    .then(d => {
      const el = document.getElementById('nav-ver');
      if (el) el.textContent = 'v' + d.app;
    })
    .catch(() => {});
});
