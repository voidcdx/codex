// ═══════════════════════════════════════════════════════
// Void Codex — Modals: Alchemy, Riven, Guide, Changelog, Buffs
// ═══════════════════════════════════════════════════════

function openAlchemyMixer() {
  alchSelected = null;
  document.getElementById('alchemy-mixer-overlay').classList.add('active');
  renderAlchPalette();
  document.getElementById('alchemy-suggestions').innerHTML =
    '<p style="color:var(--text-dim);font-size:12px;text-align:center;padding:24px 0">Select an element above to see mods</p>';
}

function closeAlchemyMixer() {
  document.getElementById('alchemy-mixer-overlay').classList.remove('active');
}

function renderAlchPalette() {
  const el = document.getElementById('alchemy-palette');
  const mkRow = (elems, label) => {
    const pills = elems.map(e => {
      const color = ELEM_COLORS[e] || '#fff';
      const active = alchSelected === e;
      return `<button class="alchemy-elem-pill${active ? ' active' : ''}"
        style="color:${color};border-color:${active ? color : 'rgba(255,255,255,0.1)'}"
        onclick="selectAlchElem('${e}')">${e}</button>`;
    }).join('');
    return `<div class="alchemy-palette-label">${label}</div><div class="alchemy-palette-row">${pills}</div>`;
  };
  el.innerHTML = mkRow(ALCH_PRIMARY, 'Primary') + mkRow(ALCH_COMBINED, 'Combined');
}

function selectAlchElem(elem) {
  alchSelected = elem;
  renderAlchPalette();
  renderAlchSuggestions(elem);
}

function alchModRow(mod, elemField) {
  const pct = mod[elemField] || 0;
  const pctStr = pct ? `+${Math.round(pct * 100)}` : '';
  const elemName = elemField.replace('_pct', '');
  const color = ELEM_COLORS[elemName] || '#fff';

  const badge = mod.name.startsWith('Galvanized ')
    ? '<span class="alch-tier-badge alch-tier-galv">GALV</span>' : '';

  const statPills = (mod.effect || '')
    .replace(/<[^>]+>/g, '')
    .split(/[\r\n]+/)
    .map(s => s.trim())
    .filter(Boolean)
    .map(line => `<span class="alch-stat-pill">${esc(line)}</span>`)
    .join('');

  const equipped = modSlots.includes(mod.name);
  const noSlots = modSlots.indexOf('') === -1;
  let btnHtml;
  if (equipped) {
    btnHtml = `<button class="alch-add-btn alch-remove-btn" data-mod="${esc(mod.name)}" onclick="removeAlchMod(this.dataset.mod)">−</button>`;
  } else {
    const dis = noSlots ? 'disabled title="No empty slots"' : '';
    btnHtml = `<button class="alch-add-btn" ${dis} data-mod="${esc(mod.name)}" onclick="addAlchMod(this.dataset.mod)">+</button>`;
  }

  return `<div class="alch-mod-row" style="--elem-color:${color}">
    <div class="alch-mod-row-main">
      ${dmgIcon(elemName, 10)}
      <span class="alch-mod-name">${esc(mod.name)}</span>
      ${badge}
      <span class="alch-mod-pct" style="color:${color}">${pctStr}</span>
      ${btnHtml}
    </div>
    ${statPills ? `<div class="alch-stat-strip">${statPills}</div>` : ''}
  </div>`;
}

function renderAlchSuggestions(elem) {
  const el = document.getElementById('alchemy-suggestions');
  const compatible = getCompatibleModTypes(getCurrentWeapon());
  const isPrimary = ALCH_PRIMARY.includes(elem);
  const elemField = ALCH_ELEM_PCT_FIELD[elem];
  const color = ELEM_COLORS[elem] || '#fff';

  if (isPrimary) {
    const mods = allMods
      .filter(m => m.primary_element === elem && compatible.has(m.type))
      .sort((a, b) => (b[elemField] || 0) - (a[elemField] || 0));
    if (!mods.length) {
      el.innerHTML = `<p style="color:var(--text-dim);font-size:12px;text-align:center;padding:20px 0">No ${elem} mods for this weapon type</p>`;
      return;
    }
    const cap = elem.charAt(0).toUpperCase() + elem.slice(1);
    el.innerHTML = `<div class="alch-section-label" style="border-top:none;margin-top:0">${dmgIcon(elem, 10)} ${cap} Mods</div>` +
      mods.map(m => alchModRow(m, elemField)).join('');
  } else {
    const [recipeA, recipeB] = ALCH_RECIPES[elem];
    const fieldA = ALCH_ELEM_PCT_FIELD[recipeA];
    const fieldB = ALCH_ELEM_PCT_FIELD[recipeB];
    const colorA = ELEM_COLORS[recipeA] || '#fff';
    const colorB = ELEM_COLORS[recipeB] || '#fff';

    const directMods = allMods
      .filter(m => (m[elemField] || 0) > 0 && compatible.has(m.type))
      .sort((a, b) => (b[elemField] || 0) - (a[elemField] || 0));

    const modsA = allMods
      .filter(m => m.primary_element === recipeA && compatible.has(m.type))
      .sort((a, b) => (b[fieldA] || 0) - (a[fieldA] || 0));
    const modsB = allMods
      .filter(m => m.primary_element === recipeB && compatible.has(m.type))
      .sort((a, b) => (b[fieldB] || 0) - (a[fieldB] || 0));

    let html = '';

    if (directMods.length) {
      const cap = elem.charAt(0).toUpperCase() + elem.slice(1);
      html += `<div class="alch-section-label" style="border-top:none;margin-top:0">${dmgIcon(elem, 10)} Direct ${cap} Mods</div>`;
      html += directMods.map(m => alchModRow(m, elemField)).join('');
    }

    html += `<div class="alch-section-label${directMods.length ? '' : ' alch-section-first'}">
      Build with ${dmgIcon(recipeA, 10)}<span style="color:${colorA}">${recipeA}</span>
      + ${dmgIcon(recipeB, 10)}<span style="color:${colorB}">${recipeB}</span>
    </div>`;

    if (!modsA.length && !modsB.length) {
      html += `<p style="color:var(--text-dim);font-size:12px;text-align:center;padding:12px 0">No primary mods for this weapon type</p>`;
    } else {
      const colA = `<div>
        <div class="alch-col-header" style="color:${colorA}">${dmgIcon(recipeA, 9)} ${recipeA}</div>
        ${modsA.length ? modsA.map(m => alchModRow(m, fieldA)).join('') : '<span style="color:var(--text-dim);font-size:11px">—</span>'}
      </div>`;
      const colB = `<div>
        <div class="alch-col-header" style="color:${colorB}">${dmgIcon(recipeB, 9)} ${recipeB}</div>
        ${modsB.length ? modsB.map(m => alchModRow(m, fieldB)).join('') : '<span style="color:var(--text-dim);font-size:11px">—</span>'}
      </div>`;
      html += `<div class="alch-pair-cols">${colA}${colB}</div>`;
    }

    el.innerHTML = html;
  }
}

function addAlchMod(modName) {
  const slot = modSlots.indexOf('');
  if (slot < 0) return;
  modSlots[slot] = modName;
  renderModCards();
  initSortable();
  updateModdedStats();
  if (alchSelected) renderAlchSuggestions(alchSelected);
}

function removeAlchMod(modName) {
  const slot = modSlots.indexOf(modName);
  if (slot < 0) return;
  modSlots[slot] = '';
  renderModCards();
  initSortable();
  updateModdedStats();
  if (alchSelected) renderAlchSuggestions(alchSelected);
}

function clearAlchMods() {
  const alchNames = new Set(allMods.filter(m => m.primary_element).map(m => m.name));
  modSlots = modSlots.map(slot => alchNames.has(slot) ? '' : slot);
  renderModCards();
  initSortable();
  updateModdedStats();
  if (alchSelected) renderAlchSuggestions(alchSelected);
}

function openRivenBuilder() {
  rivenDraft = Array.from({length: 4}, (_, i) =>
    rivenApplied && rivenApplied[i] ? {...rivenApplied[i]} : {stat: '', pct: 0}
  );
  renderRivenRows();
document.getElementById('riven-picker-overlay').classList.add('active');
}

function closeRivenBuilder() {
  document.getElementById('riven-picker-overlay').classList.remove('active');
}

function applyRiven() {
  const valid = rivenDraft.filter(s => s.stat);
  rivenApplied = valid.length ? valid : null;
  closeRivenBuilder();
  if (rivenApplied) {
    const existing = modSlots.indexOf('__riven__');
    if (existing < 0) {
      const empty = modSlots.indexOf('');
      if (empty >= 0) modSlots[empty] = '__riven__';
      else { alert('No empty mod slot — remove a mod first.'); return; }
    }
  } else {
    const idx = modSlots.indexOf('__riven__');
    if (idx >= 0) modSlots[idx] = '';
  }
  renderModCards();
  initSortable();
  updateModdedStats();
}

function clearRiven() {
  rivenDraft = [{stat:'',pct:0},{stat:'',pct:0},{stat:'',pct:0},{stat:'',pct:0}];
  rivenApplied = null;
  const idx = modSlots.indexOf('__riven__');
  if (idx >= 0) modSlots[idx] = '';
  renderRivenRows();
  renderModCards();
  initSortable();
  updateModdedStats();
}

function onRivenDraftChange(i, field, value) {
  if (field === 'pct') rivenDraft[i].pct = parseFloat(value) || 0;
  else rivenDraft[i].stat = value;
}

function renderRivenRows() {
  const container = document.getElementById('riven-rows');
  container.innerHTML = rivenDraft.map((s, i) => `
    <div class="riven-stat-row${s.stat ? ' has-value' : ''}">
      <select class="riven-stat-select" onchange="onRivenDraftChange(${i},'stat',this.value)">
        ${RIVEN_STAT_OPTIONS.map(o =>
          `<option value="${esc(o.value)}"${o.value===s.stat?' selected':''}>${esc(o.label)}</option>`
        ).join('')}
      </select>
      <input type="number" class="riven-stat-input" step="0.1" value="${s.pct || ''}"
        placeholder="0" min="-999" max="9999"
        onchange="onRivenDraftChange(${i},'pct',this.value)"
        oninput="if(this.value.length>4)this.value=this.value.slice(0,4);onRivenDraftChange(${i},'pct',this.value)">
      <button class="riven-row-clear" onclick="clearRivenRow(${i})" title="Clear row">×</button>
    </div>
  `).join('');
}

function clearRivenRow(i) {
  rivenDraft[i] = { stat: '', pct: 0 };
  renderRivenRows();
}


function getRivenSpec() {
  if (!rivenApplied || !rivenApplied.length) return null;
  const stats = rivenApplied.filter(s => s.stat).map(s => ({stat: s.stat, value: s.pct / 100}));
  return stats.length ? {stats} : null;
}

// Close riven modal on backdrop click
document.addEventListener('click', e => {
  const riven = document.getElementById('riven-picker-overlay');
  if (riven && riven.classList.contains('active') && e.target === riven)
    closeRivenBuilder();
  const alch = document.getElementById('alchemy-mixer-overlay');
  if (alch && alch.classList.contains('active') && e.target === alch)
    closeAlchemyMixer();
  const guide = document.getElementById('guide-overlay');
  if (guide && guide.classList.contains('active') && e.target === guide)
    closeGuide();
  const cl = document.getElementById('changelog-overlay');
  if (cl && cl.classList.contains('active') && e.target === cl)
    closeChangelog();
});

function openGuide()  { document.getElementById('guide-overlay').classList.add('active'); }
function closeGuide() { document.getElementById('guide-overlay').classList.remove('active'); }

// ---------------------------------------------------------------------------
// What's New (Changelog) — CHANGELOG_ENTRIES in constants.js
// ---------------------------------------------------------------------------
function renderChangelog() {
  const body = document.getElementById('changelog-body');
  if (!body) return;
  let html = '';
  for (const entry of CHANGELOG_ENTRIES) {
    html += `<div class="changelog-entry">`;
    html += `<div class="changelog-version-row"><span class="changelog-ver">v${entry.version}</span><span class="changelog-date">${entry.date}</span></div>`;
    for (const sec of entry.sections) {
      html += `<h4 class="changelog-section-heading">${sec.heading}</h4><ul class="changelog-list">`;
      for (const item of sec.items) {
        html += `<li>${item}</li>`;
      }
      html += `</ul>`;
    }
    html += `</div>`;
  }
  body.innerHTML = html;
}

function openChangelog() {
  renderChangelog();
  document.getElementById('changelog-overlay').classList.add('active');
}
function closeChangelog() {
  document.getElementById('changelog-overlay').classList.remove('active');
}

// ---------------------------------------------------------------------------
// Warframe Buffs — BUFF_OPTIONS and buffRowId in constants.js
// ---------------------------------------------------------------------------
function addBuffRow() {
  const container = document.getElementById('buff-rows');
  const id = buffRowId++;
  const row = document.createElement('div');
  row.id = 'buff-row-' + id;
  row.style.cssText = 'display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap';
  const opts = BUFF_OPTIONS.map(o => `<option value="${o.key}">${o.label}</option>`).join('');
  row.innerHTML = `<select style="flex:1;min-width:140px">${opts}</select>`
    + `<label style="font-size:12px;color:#aaa">Str%</label>`
    + `<input type="number" value="100" min="1" max="999" style="width:56px" title="Ability Strength %">`
    + `<label style="font-size:11px;color:#b89d65;cursor:pointer;display:flex;align-items:center;gap:3px" title="Use Helminth (subsumed) reduced base values">`
    + `<input type="checkbox" class="buff-subsumed" style="accent-color:#b89d65"> Helminth</label>`
    + `<button type="button" onclick="this.parentElement.remove()" style="background:none;border:none;color:#c44;cursor:pointer;font-size:16px" title="Remove buff">&times;</button>`;
  container.appendChild(row);
}

function getActiveBuffs() {
  const rows = document.querySelectorAll('#buff-rows > div');
  const buffs = [];
  rows.forEach(row => {
    const sel = row.querySelector('select');
    const inp = row.querySelector('input[type="number"]');
    const sub = row.querySelector('.buff-subsumed');
    if (sel && inp) {
      const b = {name: sel.value, strength: (parseFloat(inp.value) || 100) / 100};
      if (sub && sub.checked) b.subsumed = true;
      buffs.push(b);
    }
  });
  return buffs;
}
