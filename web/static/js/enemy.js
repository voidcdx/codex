// ═══════════════════════════════════════════════════════
// Void Codex — Enemy Panel & Level Scaling
// ═══════════════════════════════════════════════════════

// steelPathOn, eximusOn, lastScaledEnemy declared in constants.js

function showEnemyStats(enemy) {
  if (!enemy) { document.getElementById('enemy-stats-content').innerHTML = ''; document.getElementById('enemy-scaled-stats').innerHTML = ''; return; }

  const lvlInput = document.getElementById('enemy-level');
  if (lvlInput) {
    const bl = enemy.base_level || 1;
    lvlInput.min = bl;
    lvlInput.value = bl;
  }

  const fmt = (v, suffix) => v != null && v !== 0 ? v + (suffix || '') : '\u2014';
  const cap = s => s ? s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : '\u2014';

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
    refreshCustomSelect('body-part-select');
  }

  const headMult = enemy.body_parts && enemy.body_parts['Head'];

  document.getElementById('enemy-stats-content').innerHTML = `
    <div style="margin-bottom:10px">
      <div style="font-size:15px;font-weight:600;color:var(--text)">${esc(enemy.name)}</div>
    </div>
    <div class="kv-stats">
      <div class="kv-row">
        <span class="kv-label">Faction</span>
        <span class="stat-value">${cap(enemy.faction)}</span>
      </div>
      <div class="kv-row">
        <span class="kv-label">Health Type</span>
        <span class="stat-value">${cap(enemy.health_type)}</span>
      </div>
      <div class="kv-row">
        <span class="kv-label">Base Level</span>
        <span class="stat-value">${enemy.base_level || 1}</span>
      </div>
      <div class="kv-divider"></div>
      <div class="kv-row">
        <span class="kv-label">Base Health</span>
        <span class="stat-value">${fmt(enemy.base_health)}</span>
      </div>
      <div class="kv-row">
        <span class="kv-label">Base Shield</span>
        <span class="stat-value">${fmt(enemy.base_shield)}</span>
      </div>
      <div class="kv-row">
        <span class="kv-label">Base Armor</span>
        <span class="stat-value">${fmt(enemy.base_armor)}</span>
      </div>
      ${headMult && headMult !== 1 ? `<div class="kv-row">
        <span class="kv-label">Head Multiplier</span>
        <span class="stat-value">${headMult}\u00d7</span>
      </div>` : ''}
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
  const enemy = getCurrentEnemy();
  const container = document.getElementById('enemy-scaled-stats');
  if (!enemy) { container.innerHTML = ''; lastScaledEnemy = null; return; }
  const level = Math.max(parseInt(document.getElementById('enemy-level').value) || 1, enemy.base_level || 1);
  try {
    const r = await fetch('/api/scaled-enemy', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ enemy: enemy.name, level, steel_path: steelPathOn, eximus: eximusOn }),
    });
    const d = await r.json();
    lastScaledEnemy = d;
    const fmt = v => {
      if (v <= 0) return '\u2014';
      return Number(v.toFixed(2)).toLocaleString(undefined, {maximumFractionDigits: 2});
    };
    const lvlLabel = steelPathOn ? `${level} <span style="color:var(--accent);font-size:10px">(SP \u00d72.5)</span>` : String(d.level);
    container.innerHTML = `
      <div class="scaled-stat-block">Lvl <span>${lvlLabel}</span></div>
      <div class="scaled-stat-block">HP <span>${fmt(d.health)}</span></div>
      <div class="scaled-stat-block">Shield <span>${fmt(d.shield)}</span></div>
      <div class="scaled-stat-block">Armor <span>${fmt(d.armor)}</span></div>
      ${eximusOn ? `<div class="scaled-stat-block">Overguard <span>${fmt(d.overguard)}</span></div>` : ''}
    `;
  } catch { container.innerHTML = ''; }
}
