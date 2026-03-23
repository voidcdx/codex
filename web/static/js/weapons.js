// ═══════════════════════════════════════════════════════
// Void Codex — Weapon Display, Mod Grid, Element Badges,
//              Modded Stats, Special Slots
// ═══════════════════════════════════════════════════════

function polaritySVG(polarity) {
  if (!polarity) return '';
  const paths = {
    'Madurai':   '<path d="M6 2L11 10L6 8L1 10Z"/>',
    'Naramon':   '<path d="M1 4.5H11V7.5H1Z"/>',
    'Vazarin':   '<path d="M3 1C9 3 9 9 3 11L3 1Z"/>',
    'Zenurik':   '<path d="M1 2.5H11V4.5H1ZM1 7.5H11V9.5H1Z"/>',
    'Unairu':    '<path d="M6 1L11 11H1Z"/>',
    'Penjaga':   '<path d="M6 1L10 5L6 9M6 5H2"/>',
    'Umbra':     '<path d="M6 1L10 6L6 11L2 6ZM6 4L8 6L6 8"/>',
    'Universal': '<circle cx="6" cy="6" r="4"/>',
  };
  const p = paths[polarity];
  if (!p) return '';
  return `<span class="mod-polarity"><svg class="polarity-icon" viewBox="0 0 12 12" width="14" height="14" fill="currentColor" stroke="none">${p}</svg></span>`;
}

function initModGrid() {
  modSlots = ['','','','','','','',''];
  renderModCards();
  renderSpecialSlots();
  initSortable();

}

function renderModCards() {
  const grid = document.getElementById('mod-grid');
  grid.innerHTML = '';
  const STAT_LABELS = {
    damage:'DMG', multishot:'MS', crit_chance:'CC', crit_damage:'CD',
    status_chance:'SC', fire_rate:'FR', heat:'Heat', cold:'Cold',
    electricity:'Elec', toxin:'Tox',
    impact:'Impact', puncture:'Puncture', slash:'Slash',
  };
  modSlots.forEach((modName, i) => {
    const card = document.createElement('div');
    card.dataset.slot = i;

    if (modName === '__riven__') {
      card.className = 'mod-card riven-mod-card';
      const lines = (rivenApplied || []).filter(s => s.stat)
        .map(s => `<div class="riven-card-stat">${s.pct >= 0 ? '+' : ''}${s.pct}% ${esc(STAT_LABELS[s.stat] || s.stat)}</div>`)
        .join('');
      card.innerHTML = `
        <button class="mod-clear" onclick="event.stopPropagation();clearRiven()" title="Remove riven">&times;</button>
        <div class="riven-card-icon">⬡</div>
        <div class="mod-name" style="color:var(--riven)">Riven</div>
        <div class="riven-card-stats">${lines}</div>`;
      card.onclick = openRivenBuilder;
    } else if (modName) {
      card.className = 'mod-card';
      const mod = allMods.find(m => m.name === modName);
      const rarity = mod ? (mod.rarity || '').toLowerCase() : '';
      if (rarity) card.classList.add('rarity-' + rarity);
      const elemTag = mod && mod.primary_element ? mod.primary_element : '';
      const polIcon = mod ? polaritySVG(mod.polarity) : '';
      card.innerHTML = `
        <button class="mod-clear" onclick="event.stopPropagation();clearModSlot(${i})" title="Remove mod">&times;</button>
        ${polIcon}
        <div class="mod-name">${esc(modName)}</div>
        ${elemTag ? `<div class="mod-element">${esc(elemTag)}</div>` : ''}
        <div class="slot-num">${i+1}</div>`;
      card.onclick = () => openModPicker(i);
    } else {
      card.className = 'mod-card empty';
      card.innerHTML = `
        <div class="add-icon">+</div>
        <div class="add-label">Add Mod</div>
        <div class="slot-num">${i+1}</div>`;
      card.onclick = () => openModPicker(i);
    }
    grid.appendChild(card);
  });
  updateElementBadges();
}

function initSortable() {
  const grid = document.getElementById('mod-grid');
  if (_sortableInstance) _sortableInstance.destroy();
  _sortableInstance = new Sortable(grid, {
    animation: 200,
    delay: 150,
    delayOnTouchOnly: true,
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen',
    onEnd(evt) {
      const item = modSlots.splice(evt.oldIndex, 1)[0];
      modSlots.splice(evt.newIndex, 0, item);
      renderModCards();
      initSortable();
      updateModdedStats();
    }
  });
}

function clearModSlot(i) {
  modSlots[i] = '';
  renderModCards();
  initSortable();
  updateModdedStats();

}

function getSelectedMods() {
  const specials = [stanceSlot, exilusSlot].filter(Boolean);
  return [...specials, ...modSlots.filter(n => n && n !== '__riven__')];
}


// ---------------------------------------------------------------------------
// Mod Picker
// ---------------------------------------------------------------------------
function openModPicker(slotIndex) {
  _pickerSlot = slotIndex;
  document.getElementById('picker-slot-num').textContent = slotIndex + 1;
  const overlay = document.getElementById('mod-picker-overlay');
  overlay.classList.add('active');
  const search = document.getElementById('mod-picker-search');
  search.value = '';
  toggleSearchClear(search);
  search.focus();
  renderPickerList('');
}

function openSpecialPicker(kind) {
  _pickerSlot = kind; // 'stance' or 'exilus'
  document.getElementById('picker-slot-num').textContent =
    kind === 'stance' ? 'Stance' : 'Exilus';
  const overlay = document.getElementById('mod-picker-overlay');
  overlay.classList.add('active');
  const search = document.getElementById('mod-picker-search');
  search.value = '';
  toggleSearchClear(search);
  search.focus();
  renderPickerList('');
}

function closeModPicker() {
  document.getElementById('mod-picker-overlay').classList.remove('active');
  _pickerSlot = -1;
}

function renderPickerList(query) {
  const weapon = getCurrentWeapon();
  const types = getCompatibleModTypes(weapon);
  const q = query.toLowerCase();

  // Build set of mods already in use (excluding the slot currently being replaced)
  const inUse = new Set();
  if (_pickerSlot !== 'stance' && stanceSlot) inUse.add(stanceSlot);
  if (_pickerSlot !== 'exilus' && exilusSlot) inUse.add(exilusSlot);
  modSlots.forEach((name, i) => {
    if (name && name !== '__riven__' && i !== _pickerSlot) inUse.add(name);
  });

  let filtered;
  if (_pickerSlot === 'stance') {
    const NON_STANCE = new Set(['Aura','Railjack Aura','Warframe','Plexus','K-Drive',
      'Companion','Sentinel','MOA','Beast','Kubrow','Kavat','Vulpaphyla','Predasite',
      'Necramech','Archwing','Archgun','Archmelee']);
    filtered = allMods.filter(m => (m.base_drain || 0) < 0 && !NON_STANCE.has(m.type))
      .filter(m => weapon ? types.has(m.type) : true)
      .filter(m => !inUse.has(m.name))
      .filter(m => !q || m.name.toLowerCase().includes(q));
  } else if (_pickerSlot === 'exilus') {
    const exilusSet = getExilusSet();
    filtered = allMods.filter(m => exilusSet.has(m.name))
      .filter(m => !inUse.has(m.name))
      .filter(m => !q || m.name.toLowerCase().includes(q));
  } else {
    filtered = allMods
      .filter(m => types.has(m.type))
      .filter(m => !inUse.has(m.name))
      .filter(m => !q || m.name.toLowerCase().includes(q));
  }

  const list = document.getElementById('mod-picker-list');
  const RARITY_COLORS = { common: '#9e9e78', uncommon: '#6a8f47', rare: '#5a7cc4', legendary: '#c49a1f' };
  list.innerHTML = filtered.slice(0, 100).map(m => {
    const rc = RARITY_COLORS[(m.rarity || '').toLowerCase()] || '#888';
    const elem = m.primary_element || '';
    return `<div class="mod-picker-item" data-mod="${esc(m.name)}" onclick="selectPickerMod(this)">
      <span class="mod-rarity-dot" style="background:${rc}"></span>
      ${esc(m.name)}
      ${elem ? `<span class="mod-element-tag">${esc(elem)}</span>` : ''}
    </div>`;
  }).join('');
}

function selectPickerMod(el) {
  if (_pickerSlot === -1) return;
  const modName = el.dataset.mod;
  // Prevent duplicates across all slots
  const allSelected = getSelectedMods();
  const currentInSlot = _pickerSlot === 'stance' ? stanceSlot
    : _pickerSlot === 'exilus' ? exilusSlot
    : modSlots[_pickerSlot];
  if (modName !== currentInSlot && allSelected.includes(modName)) return;
  if (_pickerSlot === 'stance') {
    stanceSlot = modName;
    closeModPicker();
    renderSpecialSlots();
  } else if (_pickerSlot === 'exilus') {
    exilusSlot = modName;
    closeModPicker();
    renderSpecialSlots();
  } else {
    modSlots[_pickerSlot] = modName;
    closeModPicker();
    renderModCards();
    initSortable();
  }
  updateModdedStats();

}

// Close picker on outside click
document.addEventListener('click', e => {
  const overlay = document.getElementById('mod-picker-overlay');
  if (overlay && overlay.classList.contains('active') && e.target === overlay) {
    closeModPicker();
  }
});

// Picker search DOMContentLoaded listener is in app.js

// ---------------------------------------------------------------------------
// Element Combination Badges
// ---------------------------------------------------------------------------
// ELEM_COMBOS and PRIMARY_ELEMENTS defined in constants.js

function updateElementBadges() {
  const container = document.getElementById('element-badges');
  if (!container) return;
  // Gather elemental mods in slot order, tracking slot index
  const elemQueue = [];
  modSlots.forEach((name, slotIdx) => {
    if (!name) return;
    const mod = allMods.find(m => m.name === name);
    if (mod && mod.primary_element && PRIMARY_ELEMENTS.has(mod.primary_element.toLowerCase())) {
      elemQueue.push({ element: mod.primary_element.toLowerCase(), slotIdx });
    }
  });

  // Append weapon's innate primary elements at slot 8 (after all 8 mod slots)
  const weaponData = getCurrentWeapon();
  if (weaponData) {
    const atk = getSelectedAttackData(weaponData);
    const bd = ((atk || weaponData).base_damage) || {};
    Object.keys(bd).forEach(k => {
      if (PRIMARY_ELEMENTS.has(k) && bd[k] > 0) {
        elemQueue.push({ element: k, slotIdx: 8 });
      }
    });
  }

  // Combine in order (same as combiner.py logic)
  const badges = [];
  const used = new Set();
  for (let i = 0; i < elemQueue.length; i++) {
    if (used.has(i)) continue;
    let combined = false;
    for (let j = i + 1; j < elemQueue.length; j++) {
      if (used.has(j)) continue;
      const key = elemQueue[i].element + '+' + elemQueue[j].element;
      if (ELEM_COMBOS[key]) {
        badges.push({ a: elemQueue[i].element, b: elemQueue[j].element, result: ELEM_COMBOS[key], slotA: elemQueue[i].slotIdx, slotB: elemQueue[j].slotIdx });
        used.add(i);
        used.add(j);
        combined = true;
        break;
      }
    }
    if (!combined) {
      badges.push({ a: elemQueue[i].element, b: null, result: elemQueue[i].element, slotA: elemQueue[i].slotIdx, slotB: -1 });
      used.add(i);
    }
  }

  container.innerHTML = badges.filter(b => b.b).map(b => {
    const ca = ELEM_COLORS[b.a] || '#888';
    const cb = ELEM_COLORS[b.b] || '#888';
    const cr = ELEM_COLORS[b.result.toLowerCase()] || 'var(--accent)';
    const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
    return `<div class="element-badge">
      ${dmgIcon(b.a, 12)}${cap(b.a)}
      <span class="arrow">+</span>
      ${dmgIcon(b.b, 12)}${cap(b.b)}
      <span class="arrow">=</span>
      ${dmgIcon(b.result.toLowerCase(), 12)}${cap(b.result)}
    </div>`;
  }).join('');

  drawElementArcs(badges.filter(b => b.b !== null));
}

function drawElementArcs(combos) {
  const svg = document.getElementById('element-arcs');
  if (!svg) return;
  svg.innerHTML = '';
  if (!combos || !combos.length) { svg.style.height = '0'; return; }

  const grid = document.getElementById('mod-grid');
  const wrap = document.getElementById('mod-grid-wrapper');
  const wrapRect = wrap.getBoundingClientRect();
  const arcSpace = 30 + combos.length * 28;
  svg.setAttribute('width', wrap.offsetWidth);
  svg.setAttribute('height', grid.offsetHeight + arcSpace);

  // Pre-compute per-row-band local indices so arcs from different rows
  // don't stack extra vertical offset on top of each other.
  const bandCounters = {};
  const localIdxArr = combos.map(combo => {
    const band = Math.floor(Math.max(combo.slotA < 0 ? 0 : combo.slotA,
                                      combo.slotB < 0 ? 0 : combo.slotB) / 2);
    const li = bandCounters[band] || 0;
    bandCounters[band] = li + 1;
    return li;
  });

  combos.forEach((combo, idx) => {
    if (combo.slotA < 0 || combo.slotB < 0) return;
    const cardA = grid.children[combo.slotA];
    const cardB = grid.children[combo.slotB];
    if (!cardA || !cardB) return;

    const rectA = cardA.getBoundingClientRect();
    const rectB = cardB.getBoundingClientRect();
    const ax = rectA.left - wrapRect.left + rectA.width / 2;
    const ay = rectA.top - wrapRect.top + rectA.height;
    const bx = rectB.left - wrapRect.left + rectB.width / 2;
    const by = rectB.top - wrapRect.top + rectB.height;
    const mx = (ax + bx) / 2;
    const my = Math.max(ay, by) + 18 + localIdxArr[idx] * 28;
    const color = ELEM_COLORS[combo.result.toLowerCase()] || 'var(--accent)';

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M${ax} ${ay} Q${ax} ${my} ${mx} ${my} M${bx} ${by} Q${bx} ${my} ${mx} ${my}`);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', color);
    path.setAttribute('stroke-width', '1.5');
    path.setAttribute('stroke-opacity', '0.5');
    svg.appendChild(path);

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('transform', `translate(${mx},${my})`);
    const label = combo.result;
    const tw = label.length * 7 + 14;
    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bg.setAttribute('x', -tw / 2); bg.setAttribute('y', -9);
    bg.setAttribute('width', tw); bg.setAttribute('height', 18);
    bg.setAttribute('rx', 9);
    bg.setAttribute('fill', 'rgba(15,15,25,0.85)');
    bg.setAttribute('stroke', color); bg.setAttribute('stroke-width', '1');
    g.appendChild(bg);
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('text-anchor', 'middle'); text.setAttribute('dy', '4');
    text.setAttribute('fill', color); text.setAttribute('font-size', '11');
    text.setAttribute('font-weight', '600'); text.setAttribute('font-family', 'inherit');
    text.textContent = label;
    g.appendChild(text);
    svg.appendChild(g);
  });
}

window.addEventListener('resize', () => updateElementBadges());


// Returns the set of mod types compatible with the given weapon
function getCompatibleModTypes(weapon) {
  if (!weapon) return new Set();
  const slot = weapon.slot || '';
  const cls  = weapon.class || '';
  const types = new Set([weapon.name]); // always include weapon-specific mods

  if (slot === 'Primary') {
    types.add('Primary');
    if (cls === 'Shotgun') {
      types.add('Shotgun');
    } else if (cls === 'Sniper Rifle') {
      types.add('Rifle');
      types.add('Sniper');
    } else if (cls === 'Bow' || cls === 'Crossbow') {
      types.add('Rifle');
      types.add('Bow');
    } else {
      types.add('Rifle');
      types.add('Assault Rifle');
    }
  } else if (slot === 'Secondary') {
    types.add('Pistol');
  } else if (slot === 'Melee') {
    types.add('Melee');
    const classMap = {
      'Dagger':           'Daggers',
      'Dual Daggers':     'Dual Daggers',
      'Sword':            'Swords',
      'Dual Swords':      'Dual Swords',
      'Nikana':           'Nikanas',
      'Dual Nikanas':     'Dual Nikanas',
      'Two-Handed Nikana':'Two-Handed Nikana',
      'Heavy Blade':      'Heavy Blade',
      'Hammer':           'Hammers',
      'Polearm':          'Polearms',
      'Staff':            'Staves',
      'Whip':             'Whips',
      'Blade and Whip':   'Blade And Whip',
      'Glaive':           'Glaives',
      'Claws':            'Claws',
      'Tonfa':            'Tonfas',
      'Scythe':           'Scythes',
      'Heavy Scythe':     'Heavy Scythe',
      'Rapier':           'Rapiers',
      'Sword and Shield': 'Sword And Shield',
      'Machete':          'Machetes',
      'Sparring':         'Sparring',
      'Fist':             'Fists',
      'Nunchaku':         'Nunchaku',
      'Warfan':           'Warfans',
      'Gunblade':         'Gunblade',
    };
    if (classMap[cls]) types.add(classMap[cls]);
  }
  return types;
}

// (buildModOptions and refreshModDropdowns removed — replaced by card grid + picker)

function onWeaponChange() {
  selectedAttack = null;
  const weapon = getCurrentWeapon();
  const compatTypes = getCompatibleModTypes(weapon);
  // Clear regular mod slots that are no longer compatible with the new weapon
  modSlots = modSlots.map(name => {
    if (!name || name === '__riven__') return name;
    const mod = allMods.find(m => m.name === name);
    return (mod && compatTypes.has(mod.type)) ? name : '';
  });
  // Stance slot is melee-only — clear if switching to a ranged weapon
  if (stanceSlot && !isMeleeWeapon()) {
    stanceSlot = '';
  }
  // Exilus set is weapon-type-specific — clear exilus if it no longer applies
  if (exilusSlot && !getExilusSet().has(exilusSlot)) {
    exilusSlot = '';
  }
  // Combo counter is melee-only — hide for ranged weapons and reset to tier 1
  const comboInput  = document.getElementById('combo-counter');
  const comboDiv    = document.getElementById('combo-div');
  const meleeWeapon = isMeleeWeapon();
  comboDiv.style.display = meleeWeapon ? '' : 'none';
  if (!meleeWeapon) comboInput.value = 1;
  // Update combo max: Venka Prime can reach 13x; all other weapons cap at 12x
  comboInput.max = (weapon && weapon.name === 'Venka Prime') ? 13 : 12;
  if (parseInt(comboInput.value) > parseInt(comboInput.max)) comboInput.value = comboInput.max;

  // Bonus element selector: visible only for Kuva/Tenet weapons
  const bonusDiv = document.getElementById('bonus-element-div');
  if (bonusDiv) {
    const isKT = weapon && (weapon.name.startsWith('Kuva ') || weapon.name.startsWith('Tenet '));
    bonusDiv.style.display = isKT ? '' : 'none';
    if (!isKT) {
      document.getElementById('bonus-element-type').value = 'heat';
      document.getElementById('bonus-element-pct').value = 25;
    }
  }

  updateAttackSelector(weapon);
  showWeaponStats(weapon);
  renderSpecialSlots();
  updateModdedStats();

  updateElementBadges();
}

function updateAttackSelector(weapon) {
  if (!weapon || !weapon.attacks || weapon.attacks.length <= 1) {
    selectedAttack = null;
  } else {
    selectedAttack = selectedAttack || weapon.attacks[0].name;
  }
}

function selectAttack(name) {
  selectedAttack = name;
  showWeaponStats(getCurrentWeapon());
  updateModdedStats();
  updateElementBadges();
}

function getSelectedAttackData(weapon) {
  if (!weapon || !weapon.attacks || !weapon.attacks.length) return null;
  if (selectedAttack) {
    const found = weapon.attacks.find(a => a.name === selectedAttack);
    if (found) return found;
  }
  return weapon.attacks[0];
}

// ---------------------------------------------------------------------------
// Weapon stats panel — base stats
// ---------------------------------------------------------------------------
function showWeaponStats(weapon) {
  const panel = document.getElementById('weapon-stats-panel');
  if (!weapon) { panel.style.display = 'none'; return; }

  const atk = getSelectedAttackData(weapon);
  const pct = v => (v * 100).toFixed(1) + '%';
  const fmt = (v, suffix) => v != null ? v + (suffix || '') : '—';
  const sub = [weapon.slot, weapon.class, weapon.trigger].filter(Boolean).join(' · ');

  const imgHtml = weapon.image
    ? `<div class="weapon-stats-img-row" id="weapon-img-row">
        <img src="/static/images/weapons/${esc(weapon.image)}" alt=""
             onerror="document.getElementById('weapon-img-row').style.display='none'">
        <div>
          <div class="weapon-stats-name">${esc(weapon.name)}</div>
          <div class="weapon-stats-sub">${esc(sub)}</div>
        </div>
       </div>`
    : `<div style="margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--border)">
        <div class="weapon-stats-name">${esc(weapon.name)}</div>
        <div class="weapon-stats-sub">${esc(sub)}</div>
       </div>`;

  const hasMultiAttack = weapon.attacks && weapon.attacks.length > 1;
  const attackTabsHtml = hasMultiAttack
    ? `<div class="attack-tabs">${weapon.attacks.map(a =>
        `<button class="attack-tab${a.name === selectedAttack ? ' active' : ''}"
          onclick="selectAttack(this.dataset.name)" data-name="${esc(a.name)}">${esc(a.name)}</button>`
      ).join('')}</div>`
    : '';

  document.getElementById('weapon-stats-content').innerHTML = `
    ${imgHtml}
    ${attackTabsHtml}
    <div class="stat-rows">
      <div class="stat-row">
        <div class="stat-block">
          <div class="stat-label" data-tooltip="crit-chance">Crit Chance</div>
          <div class="stat-value crit" id="sv-cc">${pct((atk ? atk.crit_chance : weapon.crit_chance) || 0)}</div>
          <div class="stat-modded" id="sm-cc" style="display:none"></div>
        </div>
        <div class="stat-block">
          <div class="stat-label" data-tooltip="crit-mult">Crit Mult</div>
          <div class="stat-value crit" id="sv-cm">${fmt((atk ? atk.crit_multiplier : weapon.crit_multiplier), 'x')}</div>
          <div class="stat-modded" id="sm-cm" style="display:none"></div>
        </div>
        <div class="stat-block">
          <div class="stat-label" data-tooltip="status">Status</div>
          <div class="stat-value status" id="sv-sc">${pct((atk ? atk.status_chance : weapon.status_chance) || 0)}${(atk && atk.multishot > 1) ? ' <span style="font-size:0.7rem;color:var(--text-muted)">\u00d7' + atk.multishot + ' pellets</span>' : ''}</div>
          <div class="stat-modded" id="sm-sc" style="display:none"></div>
          <div class="stat-modded" id="sm-sc-pellet" style="display:none"></div>
        </div>
      </div>
      <div class="stat-row">
        <div class="stat-block">
          <div class="stat-label" data-tooltip="fire-rate">Fire Rate</div>
          <div class="stat-value">${fmt(atk ? atk.fire_rate : weapon.fire_rate)}</div>
          <div class="stat-modded" id="sm-fr" style="display:none"></div>
        </div>
        <div class="stat-block">
          <div class="stat-label" data-tooltip="magazine">Magazine</div>
          <div class="stat-value" id="sv-mag">${fmt(weapon.magazine)}</div>
          <div class="stat-modded" id="sm-mag" style="display:none"></div>
        </div>
        ${weapon.max_ammo ? `<div class="stat-block">
          <div class="stat-label" data-tooltip="max-ammo">Max Ammo</div>
          <div class="stat-value" id="sv-ammo">${fmt(weapon.max_ammo)}</div>
          <div class="stat-modded" id="sm-ammo" style="display:none"></div>
        </div>` : ''}
        <div class="stat-block">
          <div class="stat-label" data-tooltip="reload">Reload</div>
          <div class="stat-value" id="sv-reload">${fmt(weapon.reload, 's')}</div>
          <div class="stat-modded" id="sm-reload" style="display:none"></div>
        </div>
        <div class="stat-block">
          <div class="stat-label" data-tooltip="multishot">Multishot</div>
          <div class="stat-value" id="sv-ms">1.0</div>
          <div class="stat-modded" id="sm-ms" style="display:none"></div>
        </div>
      </div>
    </div>
    <div id="damage-table-wrap"></div>
  `;

  renderDamageTable(atk ? atk.base_damage : weapon.base_damage, null);
  panel.style.display = 'block';
  initTooltips();
}

function renderDamageTable(baseDmg, moddedData) {
  const wrap = document.getElementById('damage-table-wrap');
  if (!wrap) return;

  const hasModded = moddedData && Object.keys(moddedData.modded_damage || {}).length > 0;

  // Merge all damage types: base IPS + modded elementals
  const allTypes = new Set([
    ...Object.keys(baseDmg),
    ...(hasModded ? Object.keys(moddedData.modded_damage) : []),
  ]);

  const baseTotal = Object.values(baseDmg).reduce((s, v) => s + v, 0);
  const moddedTotal = hasModded ? moddedData.modded_total : null;

  const headerModded = hasModded
    ? `<th style="text-align:right" class="col-modded">Modded</th>`
    : '';

  const rows = Array.from(allTypes).map(type => {
    const baseVal = baseDmg[type];
    const modVal  = hasModded ? moddedData.modded_damage[type] : null;
    const color   = ELEM_COLORS[type] || 'var(--text)';
    const dot     = dmgIcon(type);
    const label   = type.charAt(0).toUpperCase() + type.slice(1);
    const ttAttr  = TOOLTIPS[type] ? ` data-tooltip="${type}"` : '';

    const baseCell = baseVal != null
      ? `<td class="col-base" style="text-align:right">${baseVal.toFixed(1)}</td>`
      : `<td class="col-base" style="text-align:right;color:var(--border)">—</td>`;

    const moddedCell = hasModded
      ? `<td class="col-modded" style="text-align:right">${modVal != null ? modVal.toFixed(1) : '—'}</td>`
      : '';

    return `<tr>
      <td${ttAttr}>${dot}${label}</td>
      ${baseCell}
      ${moddedCell}
    </tr>`;
  }).join('');

  const moddedTotalCell = hasModded
    ? `<td style="text-align:right" class="col-modded">${moddedTotal.toFixed(1)}</td>`
    : '';

  wrap.innerHTML = `
    <table class="breakdown-table">
      <thead>
        <tr>
          <th>Damage Type</th>
          <th style="text-align:right">Base</th>
          ${headerModded}
        </tr>
      </thead>
      <tbody>${rows}</tbody>
      <tfoot class="total-row">
        <tr>
          <td>Total</td>
          <td style="text-align:right">${baseTotal.toFixed(1)}</td>
          ${moddedTotalCell}
        </tr>
      </tfoot>
    </table>
  `;
  initTooltips();
}

// ---------------------------------------------------------------------------
// Live modded stats update
// ---------------------------------------------------------------------------
// _modUpdateTimer declared in constants.js

function updateModdedStats() {
  clearTimeout(_modUpdateTimer);
  _modUpdateTimer = setTimeout(_doUpdateModdedStats, 120);
}

async function _doUpdateModdedStats() {
  const weapon = getCurrentWeapon();
  if (!weapon) return;

  const mods = getSelectedMods();

  try {
    const resp = await fetch('/api/modded-weapon', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ weapon: weapon.name, mods, attack: selectedAttack, riven: getRivenSpec(), galvanized_stacks: parseInt(document.getElementById('galv-stacks').value, 10) || 0, ...getBonusElement() }),
    });
    if (!resp.ok) return;
    const data = await resp.json();

    // Update damage table
    const atkData = getSelectedAttackData(weapon);
    const qBase = data.quantized_base_damage || (atkData ? atkData.base_damage : weapon.base_damage);
    const moddedDiffers = data && JSON.stringify(data.modded_damage) !== JSON.stringify(data.quantized_base_damage);
    const hasAnyMods = (mods.length > 0 || !!getRivenSpec()) && moddedDiffers;
    renderDamageTable(qBase, hasAnyMods ? data : null);

    // Update crit/status stat blocks
    const hasMods = hasAnyMods;
    const hasSomeMods = mods.length > 0 || !!getRivenSpec();
    const pct = v => (v * 100).toFixed(1) + '%';

    const smCC = document.getElementById('sm-cc');
    const smCM = document.getElementById('sm-cm');
    const smSC = document.getElementById('sm-sc');

    if (smCC) {
      if (hasSomeMods && Math.abs(data.modded_cc - data.base_cc) > 0.0001) {
        smCC.textContent = pct(data.modded_cc);
        smCC.style.display = 'block';
      } else {
        smCC.style.display = 'none';
      }
    }
    if (smCM) {
      if (hasSomeMods && Math.abs(data.modded_cm - data.base_cm) > 0.0001) {
        smCM.textContent = data.modded_cm.toFixed(2) + 'x';
        smCM.style.display = 'block';
      } else {
        smCM.style.display = 'none';
      }
    }
    if (smSC) {
      if (hasSomeMods && Math.abs(data.modded_sc - data.base_sc) > 0.0001) {
        smSC.textContent = pct(data.modded_sc);
        smSC.style.display = 'block';
      } else {
        smSC.style.display = 'none';
      }
    }
    const smSCPellet = document.getElementById('sm-sc-pellet');
    if (smSCPellet) {
      if (data.inherent_multishot > 1) {
        const ppSc = data.sc_per_pellet || 0;
        smSCPellet.textContent = pct(ppSc) + '/pellet';
        smSCPellet.style.display = 'block';
      } else {
        smSCPellet.style.display = 'none';
      }
    }

    const smMS = document.getElementById('sm-ms');
    if (smMS) {
      const ms = data.modded_multishot || 1.0;
      _currentMultishot = ms;
      if (hasSomeMods && ms > 1.0001) {
        smMS.textContent = '→ ' + ms.toFixed(2) + 'x';
        smMS.style.display = 'block';
      } else {
        smMS.style.display = 'none';
        if (!hasSomeMods) _currentMultishot = 1.0;
      }
    }

    const smFR = document.getElementById('sm-fr');
    if (smFR) {
      const baseFr  = data.base_fr  || 0;
      const moddedFr = data.modded_fr || 0;
      if (hasSomeMods && baseFr > 0 && Math.abs(moddedFr - baseFr) > 0.001) {
        smFR.textContent = '→ ' + moddedFr.toFixed(2) + '/s';
        smFR.style.display = 'block';
      } else {
        smFR.style.display = 'none';
      }
    }

    const smReload = document.getElementById('sm-reload');
    if (smReload) {
      const baseRel   = data.base_reload   || 0;
      const moddedRel = data.modded_reload || 0;
      if (hasSomeMods && baseRel > 0 && Math.abs(moddedRel - baseRel) > 0.001) {
        smReload.textContent = '→ ' + moddedRel.toFixed(2) + 's';
        smReload.style.display = 'block';
      } else {
        smReload.style.display = 'none';
      }
    }

    const smMag = document.getElementById('sm-mag');
    const svMag = document.getElementById('sv-mag');
    if (smMag && svMag) {
      const baseMag   = data.base_magazine   || 0;
      const moddedMag = data.modded_magazine || 0;
      if (hasSomeMods && baseMag > 0 && moddedMag !== baseMag) {
        smMag.textContent = '→ ' + moddedMag;
        smMag.style.display = 'block';
      } else {
        smMag.style.display = 'none';
      }
    }

    const smAmmo = document.getElementById('sm-ammo');
    const svAmmo = document.getElementById('sv-ammo');
    if (smAmmo && svAmmo) {
      const baseAmmo   = data.base_ammo_max   || 0;
      const moddedAmmo = data.modded_ammo_max || 0;
      if (hasSomeMods && baseAmmo > 0 && moddedAmmo !== baseAmmo) {
        smAmmo.textContent = '→ ' + moddedAmmo;
        smAmmo.style.display = 'block';
      } else {
        smAmmo.style.display = 'none';
      }
    }
  } catch(e) {
    // silent — non-critical
  }
}

function isMeleeWeapon() {
  const w = getCurrentWeapon();
  if (!w) return false;
  const types = getCompatibleModTypes(w);
  return types.has('Melee') || [...types].some(t =>
    ['Daggers','Dual Daggers','Dual Swords','Swords','Hammers','Fists','Polearms',
     'Scythes','Whips','Claws','Heavy Blade','Blade And Whip','Machetes',
     'Nunchaku','Gunblade','Thrown Melee'].includes(t));
}

function getExilusSet() {
  const w = getCurrentWeapon();
  if (!w) return new Set([...EXILUS_PRIMARY, ...EXILUS_SECONDARY, ...EXILUS_MELEE]);
  const types = getCompatibleModTypes(w);

  let base;
  if (types.has('Melee') || [...types].some(t =>
    ['Daggers','Dual Daggers','Dual Swords','Swords','Hammers','Fists','Polearms',
     'Scythes','Whips','Claws','Heavy Blade','Blade And Whip','Machetes',
     'Nunchaku','Gunblade','Thrown Melee'].includes(t))) {
    base = new Set(EXILUS_MELEE);
  } else if (types.has('Pistol')) {
    base = new Set(EXILUS_SECONDARY);
  } else {
    base = new Set(EXILUS_PRIMARY);
  }

  // Add weapon-specific exilus mods for the selected weapon
  for (const [modName, weapons] of Object.entries(WEAPON_SPECIFIC_EXILUS)) {
    if (weapons.includes(w.name)) base.add(modName);
  }
  return base;
}

function renderSpecialSlots() {
  const container = document.getElementById('special-slots');
  const melee = isMeleeWeapon();
  const hasWeapon = !!getCurrentWeapon();
  const stanceDisabled = hasWeapon && !melee;

  const makeCard = (kind, slotName, label, colorClass, icon, disabled) => {
    const card = document.createElement('div');
    card.className = `mod-card special-slot ${colorClass}${disabled ? ' disabled' : ''}`;
    if (!disabled) card.onclick = () => openSpecialPicker(kind);
    if (slotName && !disabled) {
      const mod = allMods.find(m => m.name === slotName);
      const polIcon = mod ? polaritySVG(mod.polarity) : '';
      card.innerHTML = `
        <button class="mod-clear" onclick="event.stopPropagation();clear${kind === 'stance' ? 'Stance' : 'Exilus'}()" title="Remove">&times;</button>
        ${polIcon}
        <div class="special-slot-label">${label}</div>
        <div class="mod-name">${esc(slotName)}</div>`;
    } else {
      card.classList.add('empty');
      card.innerHTML = `
        <div class="special-slot-label">${label}</div>
        <div class="special-slot-icon">${icon}</div>`;
    }
    return card;
  };
  container.innerHTML = '';
  container.appendChild(makeCard('stance', stanceSlot, 'Stance', 'stance-slot', '⚔', stanceDisabled));
  container.appendChild(makeCard('exilus', exilusSlot, 'Exilus', 'exilus-slot', '✦', false));
}

function clearStance() {
  stanceSlot = '';
  renderSpecialSlots();
  updateModdedStats();
}
function clearExilus() {
  exilusSlot = '';
  renderSpecialSlots();
  updateModdedStats();
}
