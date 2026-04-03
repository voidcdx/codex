/* Reliquary — Prime Sets browser */

let allSets    = {};    // { "Saryn Prime": { type, parts: { "Neuroptics Blueprint": [{ relic, tier, rarity }] } } }
let dropsMap   = {};    // from /api/drops
let weaponImages = {};  // { "Braton Prime": "BratonPrime.png", … }
let weaponStats  = {};  // { "Braton Prime": { slot, class, crit_chance, … }, … }

// Permanently unvaulted sets — always available via Railjack derelict caches
const EVERGREEN_SETS = new Set([
  'Nyx Prime', 'Valkyr Prime',
  'Braton Prime', 'Burston Prime', 'Cernos Prime', 'Paris Prime',
  'Akbronco Prime', 'Bronco Prime', 'Hikou Prime', 'Lex Prime',
  'Fang Prime', 'Orthos Prime', 'Scindo Prime', 'Venka Prime',
]);
let baroRelicNames = new Set();
let activeTab  = 'warframes'; // 'all' | 'warframes' | 'weapons'
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
    const [relicsResp, dropsResp, weaponsResp] = await Promise.all([
      fetch('/api/relics'),
      fetch('/api/drops'),
      fetch('/api/weapons'),
    ]);
    const relics = await relicsResp.json();
    try { dropsMap = await dropsResp.json(); } catch { dropsMap = {}; }
    try {
      const weapons = await weaponsResp.json();
      for (const w of weapons) {
        if (w.image) weaponImages[w.name] = w.image;
        if (w.name && w.name.includes('Prime')) {
          weaponStats[w.name] = w;
        }
      }
    } catch {}
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
  // Track which relics are baro-only
  baroRelicNames = new Set(relics.filter(r => r.is_baro).map(r => r.name));
  const baroRelics = baroRelicNames;
  for (const relic of relics) {
    if (relic.vaulted) continue;
    for (const rw of relic.rewards) {
      if (!rw.item.includes('Prime') || !rw.part) continue;
      if (!sets[rw.item]) sets[rw.item] = { parts: {}, baro: false };
      if (!sets[rw.item].parts[rw.part]) sets[rw.item].parts[rw.part] = [];
      sets[rw.item].parts[rw.part].push({
        relic: relic.name,
        tier: relic.tier,
        rarity: rw.rarity,
      });
    }
  }
  // Classify warframe vs weapon; flag baro-only sets
  for (const [name, set] of Object.entries(sets)) {
    const pn = Object.keys(set.parts);
    const isSentinel = pn.some(p => p.includes('Carapace') || p.includes('Cerebrum'));
    set.type = isSentinel ? 'sentinel'
      : pn.some(p => p.includes('Neuroptics') || p.includes('Chassis') || p.includes('Systems'))
        ? 'warframe' : 'weapon';
    // A set is baro-only if ALL its relics come from baro
    const allRelics = Object.values(set.parts).flat().map(r => r.relic);
    set.baro = allRelics.length > 0 && allRelics.every(r => baroRelics.has(r));
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
      if (activeTab === 'warframes' && set.type !== 'warframe' && set.type !== 'sentinel') return false;
      if (activeTab === 'weapons'   && set.type !== 'weapon')   return false;
      if (q && !name.toLowerCase().includes(q)) return false;
      return true;
    })
    .sort((a, b) => {
      if (a[1].baro !== b[1].baro) return a[1].baro ? 1 : -1;
      return a[0].localeCompare(b[0]);
    });
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
    const typeClass = set.type === 'weapon' ? ' rq-type-wp' : ' rq-type-wf';
    const inWl = wishlist.has(name);
    const wlClass = inWl ? ' rq-wl-active' : '';
    const wlIcon = inWl ? '−' : '+';
    const baroClass = set.baro ? ' rq-set-baro' : '';
    const baroTag = set.baro ? '<span class="rq-baro-tag">BARO</span>' : '';
    return `<button class="rq-set-item${active}${typeClass}${baroClass}" data-set="${esc(name)}" onclick="selectSet('${esc(name)}')">
      <span class="rq-set-name">${highlight(displayName(name), q)}${baroTag}</span>
      <span class="rq-set-count">${partCount}</span>
      <span class="rq-wl-btn${wlClass}" onclick="toggleWishlist('${esc(name)}', event)" title="${inWl ? 'Remove from goals' : 'Add to goals'}" aria-label="${inWl ? 'Remove from goals' : 'Add to goals'}">${wlIcon}</span>
    </button>`;
  }).join('');
}

// ---------------------------------------------------------------------------
// Tab toggle
// ---------------------------------------------------------------------------
function toggleSeg(btn) {
  const wasActive = btn.classList.contains('active');
  document.querySelectorAll('.rq-seg-btn').forEach(b => b.classList.remove('active'));
  if (wasActive) {
    activeTab = 'all';
  } else {
    btn.classList.add('active');
    activeTab = btn.dataset.tab;
  }
  if (selectedSet && allSets[selectedSet]) {
    const t = allSets[selectedSet].type;
    if (activeTab === 'warframes' && t !== 'warframe') clearSelection();
    if (activeTab === 'weapons'   && t !== 'weapon')   clearSelection();
  }
  renderSidebar();
}

// ---------------------------------------------------------------------------
// Sliding search
// ---------------------------------------------------------------------------
function toggleSearch() {
  const wrap = document.getElementById('rq-search-wrap');
  const input = document.getElementById('rq-search');
  const isOpen = wrap.classList.toggle('open');
  if (isOpen) {
    input.focus();
  } else {
    collapseSearch(true);
  }
}

function collapseSearch(forceClear) {
  const wrap = document.getElementById('rq-search-wrap');
  const input = document.getElementById('rq-search');
  if (forceClear || !input.value) {
    // No query or explicit clear — fully collapse
    wrap.classList.remove('open', 'has-value');
    input.blur();
    if (input.value) {
      input.value = '';
      searchQuery = '';
      renderSidebar();
    }
  } else {
    // Has a query — keep the input open so filter persists
    input.blur();
  }
}

function onSearchInput(input) {
  searchQuery = input.value;
  const wrap = document.getElementById('rq-search-wrap');
  wrap.classList.toggle('has-value', !!input.value);
  renderSidebar();
}

function clearSearch() {
  collapseSearch(true);
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

  // Scroll detail panel content to top
  const detail = document.getElementById('rq-detail');
  if (detail) {
    detail.scrollTop = 0;
    if (window.innerWidth <= 900) {
      detail.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}

function renderDetail() {
  const detail = document.getElementById('rq-detail');
  if (!selectedSet || !allSets[selectedSet]) {
    detail.innerHTML = '<div class="rq-empty-detail">SELECT A PRIME SET</div>';
    return;
  }

  const set = allSets[selectedSet];
  const typeLabels = { warframe: 'Warframe', sentinel: 'Sentinel', weapon: 'Weapon' };
  const typeBadge = typeLabels[set.type] || 'Weapon';

  // Sort parts: Blueprint first, then alphabetical
  const partEntries = Object.entries(set.parts).sort((a, b) => {
    if (a[0] === 'Blueprint') return -1;
    if (b[0] === 'Blueprint') return 1;
    return a[0].localeCompare(b[0]);
  });

  const tierOrder = ['Lith', 'Meso', 'Neo', 'Axi', 'Requiem'];

  // Weapon stats
  const ws = weaponStats[selectedSet];
  let statsHtml = '';
  if (ws) {
    const atk = ws.attacks && ws.attacks[0];
    const totalDmg = atk ? Object.values(atk.base_damage || {}).reduce((s, v) => s + v, 0) : 0;
    const stats = [
      { label: 'DAMAGE', value: totalDmg.toFixed(1), bar: Math.min(totalDmg / 100, 1), color: 'var(--accent2)' },
      { label: 'CRIT',   value: (ws.crit_chance * 100).toFixed(0) + '%', bar: ws.crit_chance, color: 'var(--rarity-rare)' },
      { label: 'CRIT DMG', value: ws.crit_multiplier.toFixed(1) + 'x', bar: Math.min(ws.crit_multiplier / 5, 1), color: 'var(--tier-axi)' },
      { label: 'STATUS', value: (ws.status_chance * 100).toFixed(0) + '%', bar: ws.status_chance, color: 'var(--tier-meso)' },
      { label: 'FIRE RATE', value: ws.fire_rate.toFixed(1), bar: Math.min(ws.fire_rate / 15, 1), color: 'var(--tier-neo)' },
      { label: 'RIVEN', value: ws.riven_disposition.toFixed(2), bar: ws.riven_disposition / 5, color: 'var(--tier-requiem)' },
    ];
    statsHtml = `<div class="rq-hero-stats">${stats.map(s => {
      const pct = Math.round(s.bar * 100);
      return `<div class="rq-stat-row">
        <span class="rq-stat-label">${s.label}</span>
        <span class="rq-stat-value">${s.value}</span>
        <div class="rq-stat-bar"><div class="rq-stat-fill" style="width:${pct}%;background:${s.color}"></div></div>
      </div>`;
    }).join('')}</div>`;
  }

  // Weapon sub-info line
  let subInfo = '';
  if (ws) {
    const parts = [ws.slot, ws.class, ws.trigger].filter(Boolean);
    subInfo = `<div class="rq-hero-sub">${parts.map(p => esc(p)).join(' · ')}</div>`;
  }

  // Components — each part shows its relics inline
  const partsHtml = partEntries.map(([partName, relics]) => {
    const sorted = [...relics].sort((a, b) =>
      (tierOrder.indexOf(a.tier)) - (tierOrder.indexOf(b.tier))
    );

    const relicRows = sorted.map(r => {
      return `<div class="rq-comp-relic open">
        <div class="rq-comp-relic-row">
          <span class="rq-relic-tier-badge" data-tier="${esc(r.tier)}">${esc(r.tier)}</span>
          <span class="rq-comp-relic-name">${esc(r.relic)}</span>
          <span class="rq-relic-rarity rq-rarity-text-${esc(r.rarity)}">${esc(r.rarity)}</span>
        </div>
        ${renderDropList(r.relic)}
      </div>`;
    }).join('');

    return `<div class="rq-comp">
      <div class="rq-comp-header">
        <span class="rq-comp-name">${esc(cleanPartName(partName))}</span>
        <span class="rq-comp-count">${relics.length}</span>
      </div>
      <div class="rq-comp-relics">${relicRows}</div>
    </div>`;
  }).join('');

  // Hero image — weapon from data, warframe/sentinel by name convention
  let heroImgHtml = '';
  let heroImgClass = '';
  const imgFile = weaponImages[selectedSet];
  if (imgFile) {
    heroImgHtml = `<div class="rq-hero-img"><img src="/static/images/weapons/${esc(imgFile)}" alt="" onerror="this.parentElement.style.display='none'"></div>`;
    heroImgClass = ' rq-hero--has-img';
  } else {
    const folder = set.type === 'sentinel' ? 'sentinels' : 'warframes';
    const convName = selectedSet.replace(/ /g, '-') + '.png';
    heroImgHtml = `<div class="rq-hero-img"><img src="/static/images/${esc(folder)}/${esc(convName)}" alt="" onerror="this.parentElement.style.display='none'"></div>`;
    heroImgClass = ' rq-hero--has-img';
  }

  detail.innerHTML = `
    <div class="rq-hero${heroImgClass}">
      ${heroImgHtml}
      <div class="rq-hero-top">
        <div class="rq-hero-info">
          <div class="rq-hero-type-row">
            <span class="rq-type-badge rq-badge-${set.type}">${typeBadge}</span>
          </div>
          <h2 class="rq-hero-title">${esc(displayName(selectedSet))}</h2>
          ${subInfo}
          ${EVERGREEN_SETS.has(selectedSet) ? '<div class="rq-evergreen-note">Always available — never vaulted</div>' : ''}
        </div>
      </div>
      ${statsHtml}
      <div class="rq-hero-divider"></div>
      <div class="rq-hero-section-label">COMPONENTS</div>
      <div class="rq-comp-grid">${partsHtml}</div>
    </div>
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
function renderDropList(relicName) {
  const drops = dropsMap[relicName] || [];
  const top5 = [...drops].sort((a, b) => b.chance - a.chance).slice(0, 5);
  if (top5.length === 0) {
    if (baroRelicNames.has(relicName)) {
      return '<div class="rq-no-drops rq-baro-note">Available from Baro Ki\'Teer\'s Void Trader rotation — inventory changes each visit and this relic is not guaranteed to appear.</div>';
    }
    return '<div class="rq-no-drops">No drop locations found</div>';
  }
  return `<div class="rq-drop-list">
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

  // Click-away collapses the search
  document.addEventListener('click', (e) => {
    const wrap = document.getElementById('rq-search-wrap');
    if (wrap && wrap.classList.contains('open') && !wrap.contains(e.target)) {
      collapseSearch();
    }
  });
});
