// ═══════════════════════════════════════════════════════
// Void Codex — Enemy Panel & Level Scaling
// ═══════════════════════════════════════════════════════

// steelPathOn, eximusOn, lastScaledEnemy declared in constants.js

function showEnemyStats(enemy) {
  const statsEl  = document.getElementById('enemy-stats-content');
  const scaledEl = document.getElementById('enemy-scaled-stats');
  if (!enemy) {
    statsEl.innerHTML  = '';
    scaledEl.innerHTML = '';
    return;
  }

  const lvlInput = document.getElementById('enemy-level');
  if (lvlInput) {
    const bl = enemy.base_level || 1;
    lvlInput.min   = bl;
    lvlInput.value = bl;
  }

  const cap = s => s ? s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : '—';

  const bpSelect = document.getElementById('body-part-select');
  if (bpSelect && enemy.body_parts) {
    const prevVal = bpSelect.value;
    bpSelect.innerHTML = '';
    for (const [part, mult] of Object.entries(enemy.body_parts)) {
      const opt = document.createElement('option');
      opt.value = part;
      opt.textContent = mult !== 1.0 ? `${part} (\u00d7${mult})` : part;
      bpSelect.appendChild(opt);
    }
    bpSelect.value = (enemy.body_parts[prevVal] != null) ? prevVal : 'Body';
    refreshSelectDropdown('body-part-select');
  }

  const headMult = enemy.body_parts && enemy.body_parts['Head'];
  const headVal  = headMult && headMult !== 1 ? `${headMult}\u00d7` : '\u2014';

  statsEl.innerHTML = `
    <div class="threat-card">
      <div class="threat-card-name">${esc(enemy.name)}</div>
      <div class="threat-badges">
        <span class="threat-badge threat-badge-faction">${cap(enemy.faction)}</span>
        <span class="threat-badge threat-badge-health">${cap(enemy.health_type)}</span>
      </div>
      <div class="threat-stats-row">
        <div>
          <div class="threat-stat-label">Base Lvl</div>
          <div class="threat-stat-val">${enemy.base_level || 1}</div>
        </div>
        <div>
          <div class="threat-stat-label">Head</div>
          <div class="threat-stat-val">${headVal}</div>
        </div>
        <div>
          <div class="threat-stat-label">Base Armor</div>
          <div class="threat-stat-val">${enemy.base_armor || '\u2014'}</div>
        </div>
      </div>
      <div class="threat-bars" id="threat-bars"></div>
    </div>
  `;
  refreshEnemyScaling();
}

function toggleSteelPath() {
  steelPathOn = !steelPathOn;
  document.getElementById('steel-path-btn').classList.toggle('active', steelPathOn);
  refreshEnemyScaling();
}

function toggleEximus() {
  eximusOn = !eximusOn;
  document.getElementById('eximus-btn').classList.toggle('active', eximusOn);
  refreshEnemyScaling();
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('enemy-level').addEventListener('input', refreshEnemyScaling);
});

async function refreshEnemyScaling() {
  const enemy    = getCurrentEnemy();
  const scaledEl = document.getElementById('enemy-scaled-stats');
  const barsEl   = document.getElementById('threat-bars');
  if (!enemy) {
    if (scaledEl) scaledEl.innerHTML = '';
    if (barsEl)   barsEl.innerHTML   = '';
    lastScaledEnemy = null;
    return;
  }

  const level = Math.max(parseInt(document.getElementById('enemy-level').value) || 1, enemy.base_level || 1);
  try {
    const r = await fetch('/api/scaled-enemy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enemy: enemy.name, level, steel_path: steelPathOn, eximus: eximusOn }),
    });
    const d = await r.json();
    lastScaledEnemy = d;
    if (typeof updateArmorStripDisplay === 'function') updateArmorStripDisplay();
    if (scaledEl) scaledEl.innerHTML = '';
    if (!barsEl) return;

    const fmtN = v => (v > 0)
      ? Number(v.toFixed(2)).toLocaleString(undefined, { maximumFractionDigits: 2 })
      : null;

    const dr = d.armor > 0 ? Math.round(d.armor / (d.armor + 300) * 100) : 0;

    const bars = [
      { key: 'hp', label: 'HP',     val: d.health,                        sub: fmtN(d.health),                            cls: 'threat-bar-fill-hp' },
      { key: 'sh', label: 'Shield', val: d.shield,                        sub: fmtN(d.shield),                            cls: 'threat-bar-fill-sh' },
      { key: 'ar', label: 'Armor',  val: d.armor,                         sub: d.armor > 0 ? `${fmtN(d.armor)} · ${dr}% DR` : null, cls: 'threat-bar-fill-ar' },
      { key: 'og', label: 'OG',     val: eximusOn ? d.overguard : 0,      sub: (eximusOn && d.overguard > 0) ? fmtN(d.overguard) : null, cls: 'threat-bar-fill-og' },
    ].filter(b => b.val > 0 && b.sub !== null);

    const maxVal = Math.max(...bars.map(b => b.val));

    barsEl.innerHTML = bars.map(b => `
      <div class="threat-bar-row">
        <span class="threat-bar-label">${b.label}</span>
        <div class="threat-bar-wrap">
          <div class="threat-bar-track"><div class="threat-bar-fill ${b.cls}" id="tbar-${b.key}"></div></div>
          <span class="threat-bar-sub">${b.sub}</span>
        </div>
      </div>`).join('');

    bars.forEach(b => {
      const fill = document.getElementById(`tbar-${b.key}`);
      if (fill) fill.style.width = `${Math.round(b.val / maxVal * 100)}%`;
    });

  } catch {
    if (scaledEl) scaledEl.innerHTML = '';
  }
}
