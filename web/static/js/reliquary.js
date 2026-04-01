/* Reliquary — relic browser with Prime item index */

let allRelics     = [];
let activeTier    = 'all';
let activeVault   = 'all';
let activeItem    = null;   // null = all relics
let itemsFilter   = '';     // left panel search

// ---------------------------------------------------------------------------
// Data load
// ---------------------------------------------------------------------------
async function loadRelics() {
  try {
    const resp = await fetch('/api/relics');
    allRelics = await resp.json();
    buildItemIndex();
    renderGrid();
  } catch (e) {
    document.getElementById('relic-grid').innerHTML =
      '<div class="relic-empty">Failed to load relic data.</div>';
  }
}

// ---------------------------------------------------------------------------
// Left panel: Prime item index
// ---------------------------------------------------------------------------

// Build sorted list of unique Prime items from rewards
function buildItemIndex() {
  const counts = {};  // item → number of relics containing it
  for (const relic of allRelics) {
    const seen = new Set();
    for (const r of relic.rewards) {
      if (!seen.has(r.item)) {
        seen.add(r.item);
        counts[r.item] = (counts[r.item] || 0) + 1;
      }
    }
  }

  // Separate Prime/special items from misc (Forma, Kuva, etc.)
  const primes  = [];
  const special = [];
  for (const name of Object.keys(counts).sort()) {
    if (name.toLowerCase().includes('prime') || name === 'Forma') {
      primes.push(name);
    } else {
      special.push(name);
    }
  }

  renderItemList(primes, special, counts, '');
}

function renderItemList(primes, special, counts, filter) {
  const list = document.getElementById('relic-items-list');
  const q = filter.toLowerCase();

  const filteredPrimes  = primes.filter(n  => n.toLowerCase().includes(q));
  const filteredSpecial = special.filter(n => n.toLowerCase().includes(q));

  let html = '';

  // "All" entry
  if (!q) {
    html += `<button class="relic-item-btn${activeItem === null ? ' active' : ''}"
      onclick="selectItem(null)">
      All Relics
      <span class="relic-item-count">${allRelics.length}</span>
    </button>`;
    html += '<div class="items-divider"></div>';
  }

  if (filteredPrimes.length) {
    if (!q) html += '<div class="items-section-label">Prime</div>';
    for (const name of filteredPrimes) {
      html += itemBtn(name, counts[name]);
    }
  }

  if (filteredSpecial.length) {
    html += '<div class="items-divider"></div>';
    if (!q) html += '<div class="items-section-label">Other</div>';
    for (const name of filteredSpecial) {
      html += itemBtn(name, counts[name]);
    }
  }

  if (!html) html = '<div class="relic-empty" style="padding:16px;font-size:0.8rem">No matches</div>';

  list.innerHTML = html;

  // Cache for re-renders (after filter changes don't need to reparse)
  list._primes  = primes;
  list._special = special;
  list._counts  = counts;
}

function itemBtn(name, count) {
  const isActive = activeItem === name;
  return `<button class="relic-item-btn${isActive ? ' active' : ''}"
    onclick="selectItem(${JSON.stringify(name)})">
    <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(name)}</span>
    <span class="relic-item-count">${count}</span>
  </button>`;
}

function selectItem(name) {
  activeItem = name;
  // Re-render left panel to update active state
  const list = document.getElementById('relic-items-list');
  if (list._primes) {
    renderItemList(list._primes, list._special, list._counts, itemsFilter);
  }
  renderGrid();
}

// ---------------------------------------------------------------------------
// Top filters
// ---------------------------------------------------------------------------
function setTier(btn) {
  document.querySelectorAll('#tier-pills .filter-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeTier = btn.dataset.tier;
  renderGrid();
}

function setVault(btn) {
  document.querySelectorAll('#vault-pills .filter-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeVault = btn.dataset.vault;
  renderGrid();
}

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------
function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderCard(relic) {
  const rewardRows = relic.rewards.map(r =>
    `<div class="reward-row rarity-${esc(r.rarity)}">
      <span class="reward-dot"></span>
      <span class="reward-name">${esc(r.item)}${r.part
        ? ` <span class="reward-part">${esc(r.part)}</span>` : ''}</span>
    </div>`
  ).join('');

  const badges = [
    relic.vaulted ? '<span class="relic-badge vaulted">Vaulted</span>' : '',
    relic.is_baro ? '<span class="relic-badge baro">Baro</span>'       : '',
  ].join('');

  const shortName = relic.name.replace(/^(Lith|Meso|Neo|Axi|Requiem|Vanguard)\s+/i, '');

  return `<div class="relic-card" data-tier="${esc(relic.tier)}">
    <div class="relic-card-header">
      <div class="relic-tier-bar"></div>
      <span class="relic-tier-badge">${esc(relic.tier)}</span>
      <span class="relic-name">${esc(shortName)}</span>
      <div class="relic-badges">${badges}</div>
    </div>
    <div class="relic-rewards">${rewardRows}</div>
  </div>`;
}

function renderGrid() {
  const filtered = allRelics.filter(r => {
    if (activeTier !== 'all' && r.tier !== activeTier)   return false;
    if (activeVault === 'unvaulted' && r.vaulted)         return false;
    if (activeVault === 'vaulted'   && !r.vaulted)        return false;
    if (activeItem !== null && !r.rewards.some(rw => rw.item === activeItem)) return false;
    return true;
  });

  const countEl = document.getElementById('relic-count');
  countEl.textContent = filtered.length === allRelics.length
    ? `${allRelics.length} relics`
    : `${filtered.length} of ${allRelics.length}`;

  const grid = document.getElementById('relic-grid');
  grid.innerHTML = filtered.length
    ? filtered.map(renderCard).join('')
    : '<div class="relic-empty">No relics match your filters.</div>';
}

// ---------------------------------------------------------------------------
// Sidebar / version
// ---------------------------------------------------------------------------
function openGuide() {}

function toggleDrawer() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('sidebar-overlay').classList.toggle('visible');
  document.getElementById('burger-btn').classList.toggle('open');
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

  document.getElementById('items-search').addEventListener('input', e => {
    itemsFilter = e.target.value;
    const list = document.getElementById('relic-items-list');
    if (list._primes) {
      renderItemList(list._primes, list._special, list._counts, itemsFilter);
    }
  });
});
