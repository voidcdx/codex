/* Reliquary — Prime Sets browser */

let allSets    = {};    // { "Saryn Prime": { type, parts: { "Neuroptics Blueprint": [{ relic, tier, rarity }] } } }
let dropsMap   = {};    // from /api/drops
let activeTab  = 'all'; // 'all' | 'warframes' | 'weapons'
let searchQuery = '';
let selectedSet  = null;
let selectedPart = null;

// Wishlist — persisted to localStorage
const WISHLIST_KEY = 'rq-wishlist';
let wishlist = new Set(JSON.parse(localStorage.getItem(WISHLIST_KEY) || '[]'));

// ---------------------------------------------------------------------------
// Data load + derivation
// ---------------------------------------------------------------------------
async function loadData() {
  try {
    const [relicsResp, dropsResp] = await Promise.all([
      fetch('/api/relics'),
      fetch('/api/drops'),
    ]);
    const relics = await relicsResp.json();
    try { dropsMap = await dropsResp.json(); } catch { dropsMap = {}; }
    allSets = buildPrimeSets(relics);
    renderGoals();
    renderSidebar();
  } catch (e) {
    document.getElementById('rq-set-list').innerHTML =
      '<div class="rq-empty">DATA UNAVAILABLE</div>';
  }
}

function buildPrimeSets(relics) {
  const sets = {};
  for (const relic of relics) {
    if (relic.vaulted) continue;
    for (const rw of relic.rewards) {
      if (!rw.item.includes('Prime') || !rw.part) continue;
      if (!sets[rw.item]) sets[rw.item] = { parts: {} };
      if (!sets[rw.item].parts[rw.part]) sets[rw.item].parts[rw.part] = [];
      sets[rw.item].parts[rw.part].push({
        relic: relic.name,
        tier: relic.tier,
        rarity: rw.rarity,
      });
    }
  }
  // Classify warframe vs weapon
  for (const [name, set] of Object.entries(sets)) {
    const pn = Object.keys(set.parts);
    set.type = pn.some(p =>
      p.includes('Neuroptics') || p.includes('Chassis') || p.includes('Systems')
    ) ? 'warframe' : 'weapon';
  }
  return sets;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function highlight(text, query) {
  if (!query) return esc(text);
  const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')})`, 'gi');
  return esc(text).replace(re, '<mark>$1</mark>');
}

/** Strip " Prime" suffix for display */
function displayName(name) {
  return name.replace(/ Prime$/, '');
}

// ---------------------------------------------------------------------------
// Wishlist
// ---------------------------------------------------------------------------
function saveWishlist() {
  localStorage.setItem(WISHLIST_KEY, JSON.stringify([...wishlist]));
}

function toggleWishlist(name, ev) {
  if (ev) ev.stopPropagation();
  if (wishlist.has(name)) wishlist.delete(name);
  else wishlist.add(name);
  saveWishlist();
  renderGoals();
  renderSidebar();
}

function removeGoal(name, ev) {
  if (ev) ev.stopPropagation();
  wishlist.delete(name);
  saveWishlist();
  renderGoals();
  renderSidebar();
}

/** Collect every relic needed by wishlisted sets */
function getGoalRelics() {
  const relics = new Set();
  for (const name of wishlist) {
    const set = allSets[name];
    if (!set) continue;
    for (const parts of Object.values(set.parts)) {
      for (const r of parts) relics.add(r.relic);
    }
  }
  return relics;
}

/**
 * Best Mission — rank missions by how many distinct goal-relics they drop.
 * Returns top 5 missions as [{ location, mission_type, relics: [name…], count }].
 */
function calcBestMissions() {
  const goalRelics = getGoalRelics();
  if (goalRelics.size === 0) return [];

  // missionKey → { location, mission_type, relics: Set }
  const missions = {};
  for (const relicName of goalRelics) {
    const drops = dropsMap[relicName];
    if (!drops) continue;
    for (const d of drops) {
      const key = `${d.location}|||${d.mission_type}`;
      if (!missions[key]) {
        missions[key] = { location: d.location, mission_type: d.mission_type, relics: new Set() };
      }
      missions[key].relics.add(relicName);
    }
  }

  return Object.values(missions)
    .map(m => ({ ...m, relics: [...m.relics], count: m.relics.size }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
}

// ---------------------------------------------------------------------------
// Goals section rendering
// ---------------------------------------------------------------------------
function renderGoals() {
  const container = document.getElementById('rq-goals');
  if (!container) return;

  if (wishlist.size === 0) {
    container.innerHTML = '';
    container.classList.add('rq-goals-empty');
    return;
  }
  container.classList.remove('rq-goals-empty');

  // Goal chips
  const chips = [...wishlist].filter(n => allSets[n]).map(name => {
    const set = allSets[name];
    const typeClass = set.type === 'warframe' ? 'rq-type-wf' : 'rq-type-wp';
    return `<button class="rq-goal-chip ${typeClass}" onclick="selectSet('${esc(name)}')">
      <span class="rq-goal-name">${esc(displayName(name))}</span>
      <span class="rq-goal-remove" onclick="removeGoal('${esc(name)}', event)" aria-label="Remove">&times;</span>
    </button>`;
  }).join('');

  // Best missions
  const best = calcBestMissions();
  let bestHtml = '';
  if (best.length > 0) {
    const rows = best.map(m => {
      const relicTags = m.relics.map(r =>
        `<span class="rq-best-relic">${esc(r)}</span>`
      ).join(' ');
      return `<div class="rq-best-row">
        <div class="rq-best-loc">
          <span class="rq-best-name">${esc(m.location)}</span>
          <span class="rq-best-type">${esc(m.mission_type)}</span>
        </div>
        <div class="rq-best-count">${m.count} relic${m.count !== 1 ? 's' : ''}</div>
        <div class="rq-best-relics">${relicTags}</div>
      </div>`;
    }).join('');

    bestHtml = `
      <div class="rq-best-section">
        <div class="rq-best-title">BEST MISSIONS</div>
        ${rows}
      </div>`;
  }

  container.innerHTML = `
    <div class="rq-goals-header">
      <span class="rq-goals-label">MY GOALS</span>
      <span class="rq-goals-count">${wishlist.size}</span>
    </div>
    <div class="rq-goal-chips">${chips}</div>
    ${bestHtml}
  `;
}

// ---------------------------------------------------------------------------
// Sidebar rendering
// ---------------------------------------------------------------------------
function getFilteredSets() {
  const q = searchQuery.trim().toLowerCase();
  return Object.entries(allSets)
    .filter(([name, set]) => {
      if (activeTab === 'warframes' && set.type !== 'warframe') return false;
      if (activeTab === 'weapons'   && set.type !== 'weapon')   return false;
      if (q && !name.toLowerCase().includes(q)) return false;
      return true;
    })
    .sort((a, b) => a[0].localeCompare(b[0]));
}

function renderSidebar() {
  const list = document.getElementById('rq-set-list');
  const filtered = getFilteredSets();

  if (filtered.length === 0) {
    list.innerHTML = '<div class="rq-empty">NO RESULTS</div>';
    return;
  }

  const q = searchQuery.trim().toLowerCase();
  list.innerHTML = filtered.map(([name, set]) => {
    const partCount = Object.keys(set.parts).length;
    const active = selectedSet === name ? ' active' : '';
    const typeClass = set.type === 'warframe' ? ' rq-type-wf' : ' rq-type-wp';
    const inWl = wishlist.has(name);
    const wlClass = inWl ? ' rq-wl-active' : '';
    const wlIcon = inWl ? '−' : '+';
    return `<button class="rq-set-item${active}${typeClass}" data-set="${esc(name)}" onclick="selectSet('${esc(name)}')">
      <span class="rq-set-name">${highlight(displayName(name), q)}</span>
      <span class="rq-set-count">${partCount}</span>
      <span class="rq-wl-btn${wlClass}" onclick="toggleWishlist('${esc(name)}', event)" title="${inWl ? 'Remove from goals' : 'Add to goals'}" aria-label="${inWl ? 'Remove from goals' : 'Add to goals'}">${wlIcon}</span>
    </button>`;
  }).join('');
}

// ---------------------------------------------------------------------------
// Tab + search
// ---------------------------------------------------------------------------
function setTab(btn) {
  document.querySelectorAll('.rq-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeTab = btn.dataset.tab;
  // If selected set is filtered out, clear it
  if (selectedSet && allSets[selectedSet]) {
    const t = allSets[selectedSet].type;
    if (activeTab === 'warframes' && t !== 'warframe') clearSelection();
    if (activeTab === 'weapons'   && t !== 'weapon')   clearSelection();
  }
  renderSidebar();
}

function onSearchInput(input) {
  searchQuery = input.value;
  renderSidebar();
}

function clearSearch() {
  const input = document.getElementById('rq-search');
  input.value = '';
  searchQuery = '';
  renderSidebar();
}

function clearSelection() {
  selectedSet = null;
  selectedPart = null;
  renderSidebar();
  renderDetail();
}

// ---------------------------------------------------------------------------
// Set selection → detail panel
// ---------------------------------------------------------------------------
function selectSet(name) {
  selectedSet = name;
  selectedPart = null;
  renderSidebar();
  renderDetail();

  // Mobile: scroll detail into view
  if (window.innerWidth <= 900) {
    const detail = document.getElementById('rq-detail');
    if (detail) detail.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function renderDetail() {
  const detail = document.getElementById('rq-detail');
  if (!selectedSet || !allSets[selectedSet]) {
    detail.innerHTML = '<div class="rq-empty-detail">SELECT A PRIME SET</div>';
    return;
  }

  const set = allSets[selectedSet];
  const typeBadge = set.type === 'warframe' ? 'Warframe' : 'Weapon';

  // Sort parts: Blueprint first, then alphabetical
  const partEntries = Object.entries(set.parts).sort((a, b) => {
    if (a[0] === 'Blueprint') return -1;
    if (b[0] === 'Blueprint') return 1;
    return a[0].localeCompare(b[0]);
  });

  const partsHtml = partEntries.map(([partName, relics]) => {
    const active = selectedPart === partName ? ' active' : '';
    // Best rarity across relics for this part
    const bestRarity = getBestRarity(relics);
    return `<button class="rq-part-card${active}" data-part="${esc(partName)}" onclick="selectPart('${esc(partName)}')">
      <span class="rq-part-name">${esc(cleanPartName(partName))}</span>
      <span class="rq-part-meta">
        <span class="rq-part-relic-count">${relics.length}</span>
        <span class="rq-rarity-dot rq-rarity-${esc(bestRarity)}" aria-hidden="true"></span>
      </span>
    </button>`;
  }).join('');

  const relicSection = selectedPart ? renderRelicSection() : '';

  detail.innerHTML = `
    <div class="rq-detail-header">
      <h2 class="rq-detail-title">${esc(displayName(selectedSet))}</h2>
      <span class="rq-type-badge rq-badge-${set.type}">${typeBadge}</span>
    </div>
    <div class="rq-parts-grid">${partsHtml}</div>
    ${relicSection}
  `;
}

function cleanPartName(part) {
  return part.replace(/ Blueprint$/, '');
}

function getBestRarity(relics) {
  const order = { 'Common': 0, 'Uncommon': 1, 'Rare': 2 };
  let best = 'Common';
  for (const r of relics) {
    if ((order[r.rarity] || 0) > (order[best] || 0)) best = r.rarity;
  }
  return best;
}

// ---------------------------------------------------------------------------
// Part selection → relic drill-down
// ---------------------------------------------------------------------------
function selectPart(partName) {
  selectedPart = selectedPart === partName ? null : partName;
  renderDetail();
}

function renderRelicSection() {
  if (!selectedSet || !selectedPart) return '';
  const relics = allSets[selectedSet].parts[selectedPart];
  if (!relics || relics.length === 0) return '';

  // Sort by rarity (Common first for easier farming), then tier
  const tierOrder = { 'Lith': 0, 'Meso': 1, 'Neo': 2, 'Axi': 3, 'Requiem': 4 };
  const sorted = [...relics].sort((a, b) => {
    const ta = tierOrder[a.tier] ?? 99;
    const tb = tierOrder[b.tier] ?? 99;
    return ta - tb;
  });

  const rows = sorted.map(r => {
    const drops = dropsMap[r.relic] || [];
    const top5 = [...drops].sort((a, b) => b.chance - a.chance).slice(0, 5);
    const dropHtml = top5.length > 0 ? `
      <div class="rq-drop-list">
        ${top5.map(d => {
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
        }).join('')}
      </div>` : '<div class="rq-no-drops">No drop locations found</div>';

    return `<div class="rq-relic-row">
      <div class="rq-relic-header">
        <span class="rq-relic-tier-badge" data-tier="${esc(r.tier)}">${esc(r.tier)}</span>
        <span class="rq-relic-name">${esc(r.relic)}</span>
        <span class="rq-relic-rarity rq-rarity-text-${esc(r.rarity)}">${esc(r.rarity)}</span>
      </div>
      ${dropHtml}
    </div>`;
  }).join('');

  return `<div class="rq-relic-section">
    <h3 class="rq-relic-section-title">${esc(cleanPartName(selectedPart))} — Drop Sources</h3>
    ${rows}
  </div>`;
}

// ---------------------------------------------------------------------------
// Version + sidebar nav
// ---------------------------------------------------------------------------
function openGuide() {}

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
  loadData();
  loadVersion();
});
