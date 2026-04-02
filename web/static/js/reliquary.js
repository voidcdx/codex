/* Reliquary — Prime Sets browser */

let allSets    = {};    // { "Saryn Prime": { type, parts: { "Neuroptics Blueprint": [{ relic, tier, rarity }] } } }
let dropsMap   = {};    // from /api/drops
let activeTab  = 'all'; // 'all' | 'warframes' | 'weapons'
let searchQuery = '';
let selectedSet  = null;
let selectedPart = null;

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
    renderSidebar();
  } catch (e) {
    document.getElementById('rq-set-list').innerHTML =
      '<div class="rq-empty">Failed to load relic data.</div>';
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
    list.innerHTML = '<div class="rq-empty">No sets match your search.</div>';
    return;
  }

  const q = searchQuery.trim().toLowerCase();
  list.innerHTML = filtered.map(([name, set]) => {
    const partCount = Object.keys(set.parts).length;
    const active = selectedSet === name ? ' active' : '';
    const typeClass = set.type === 'warframe' ? ' rq-type-wf' : ' rq-type-wp';
    return `<button class="rq-set-item${active}${typeClass}" data-set="${esc(name)}" onclick="selectSet('${esc(name)}')">
      <span class="rq-set-name">${highlight(displayName(name), q)}</span>
      <span class="rq-set-count">${partCount}</span>
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
    detail.innerHTML = '<div class="rq-empty-detail">Select a Prime set from the list.</div>';
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
        <span class="rq-part-relic-count">${relics.length} relic${relics.length !== 1 ? 's' : ''}</span>
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
