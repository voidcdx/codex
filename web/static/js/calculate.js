// ═══════════════════════════════════════════════════════
// Void Codex — Calculation & Results Display
// ═══════════════════════════════════════════════════════

async function runCalculation() {
  const weapon = document.getElementById('weapon-search').value;
  const enemy  = document.getElementById('enemy-search').value;
  const mods   = getSelectedMods();
  const critMode    = document.getElementById('crit-mode').value;
  const bodyPart    = document.getElementById('body-part-select').value || 'Body';
  const viralStacks     = parseInt(document.getElementById('viral-stacks').value, 10) || 0;
  const corrosiveStacks = parseInt(document.getElementById('corrosive-stacks').value, 10) || 0;
  const comboTier       = Math.max(1, parseInt(document.getElementById('combo-counter').value, 10) || 1);
  const comboCounter    = (comboTier - 1) * 10; // tier → raw hits: tier=1→0 (×1), tier=12→110 (×12)
  const uniqueStatuses  = parseInt(document.getElementById('unique-statuses').value, 10) || 0;
  const galvStacks      = parseInt(document.getElementById('galv-stacks').value, 10) || 0;

  if (!weapon || !enemy) {
    showError('Please select a weapon and enemy.');
    return;
  }

  const btn = document.getElementById('calc-btn');
  btn.disabled = true;
  btn.textContent = 'Calculating…';

  try {
    const resp = await fetch('/api/calculate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({weapon, mods, enemy, crit_mode: critMode, body_part: bodyPart, viral_stacks: viralStacks, corrosive_stacks: corrosiveStacks, combo_counter: comboCounter, unique_statuses: uniqueStatuses, galvanized_stacks: galvStacks, attack: selectedAttack, riven: getRivenSpec(), enemy_level: parseInt(document.getElementById('enemy-level').value) || 1, steel_path: steelPathOn, eximus: eximusOn, buffs: getActiveBuffs(), arcanes: getActiveArcanes(), ...getBonusElement()}),
    });
    const data = await resp.json();
    if (!resp.ok) {
      showError(data.detail || 'Calculation failed.');
    } else {
      showResults(data);
    }
  } catch(e) {
    showError('Network error: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Calculate';
  }
}

function showError(msg) {
  document.getElementById('no-results').style.display = 'none';
  document.getElementById('results-content').style.display = 'none';
  let errDiv = document.getElementById('error-msg');
  if (!errDiv) {
    errDiv = document.createElement('div');
    errDiv.id = 'error-msg';
    errDiv.className = 'error-msg';
    document.getElementById('results-panel').appendChild(errDiv);
  }
  errDiv.textContent = msg;
  errDiv.style.display = 'block';
}

function showResults(data) {
  const errDiv = document.getElementById('error-msg');
  if (errDiv) errDiv.style.display = 'none';
  document.getElementById('no-results').style.display = 'none';

  const breakdown = data.breakdown;
  const entries = Object.entries(breakdown).sort((a,b) => b[1] - a[1]);
  const maxVal = entries.length ? entries[0][1] : 1;

  const meta = [
    `Weapon: ${data.weapon}`,
    `Mods: ${data.mods.length ? data.mods.join(', ') : '(none)'}`,
    `Enemy: ${data.enemy}`,
    `Crit: ${data.crit_mode} — ×${data.crit_multiplier.toFixed(3)}${data.body_part && data.body_part !== 'Body' ? ` (${data.body_part})` : ''}`,
    data.viral_stacks > 0 ? `Viral: ${data.viral_stacks} stacks (×${[1.75,2,2.25,2.5,2.75,3,3.25,3.5,3.75,4.25][data.viral_stacks-1]})` : null,
    data.corrosive_stacks > 0 ? `Corrosive: ${data.corrosive_stacks} stacks (−${Math.min(80, 20 + 6*data.corrosive_stacks)}% armor)` : null,
    data.galvanized_stacks > 0 ? `Galv. Stacks: ${data.galvanized_stacks}` : null,
    data.buffs && data.buffs.length > 0 ? `Buffs: ${data.buffs.map(b => b.name + (b.strength !== 1 ? ` (${Math.round(b.strength*100)}%)` : '')).join(', ')}` : null,
  ].filter(Boolean).join(' &nbsp;|&nbsp; ');

  const _effEnemy = getCurrentEnemy();
  const _factionMap = _effEnemy ? (FACTION_EFFECTIVENESS[_effEnemy.faction.toLowerCase()] || {}) : {};

  const rows = entries.map(([type, val]) => {
    const pct = maxVal > 0 ? (val / maxVal * 100).toFixed(1) : 0;
    const key  = type.toLowerCase();
    const color = ELEM_COLORS[key] || 'var(--accent)';
    const dot = dmgIcon(key);
    const ttAttr = TOOLTIPS[key] ? ` data-tooltip="${key}"` : '';
    const eff = _factionMap[key];
    const effBadge = eff === 1.5 ? '<span class="eff-badge eff-vuln">+50%</span>'
                   : eff === 0.5 ? '<span class="eff-badge eff-res">−50%</span>'
                   : '';
    return `<tr>
      <td${ttAttr}>${dot}${type}${effBadge}</td>
      <td class="bar-cell"><div class="bar-bg"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div></td>
      <td>${val.toFixed(2)}</td>
    </tr>`;
  }).join('');

  const ms = _currentMultishot;
  const msNote = ms > 1.0001
    ? `<span class="ms-note">Per-trigger damage (includes ×${ms.toFixed(2)} multishot)</span>`
    : '';

  // Status procs section
  const PROC_LABELS = { slash: 'Slash (Bleed)', heat: 'Heat (Burn)', gas: 'Gas (Cloud)', toxin: 'Toxin (Poison)', electricity: 'Electricity (Arc)' };
  const PROC_COLORS = { slash: ELEM_COLORS.slash, heat: ELEM_COLORS.heat, gas: ELEM_COLORS.gas, toxin: ELEM_COLORS.toxin, electricity: ELEM_COLORS.electricity };
  const CC_PROC_LABELS = { viral: 'Viral Health Vulnr.', magnetic: 'Magnetic (Shield)', radiation: 'Radiation (Confuse)', blast: 'Blast (Accuracy)', cold: 'Cold (Freeze)' };
  const CC_PROC_COLORS = { viral: ELEM_COLORS.viral, magnetic: ELEM_COLORS.magnetic, radiation: ELEM_COLORS.radiation, blast: ELEM_COLORS.blast, cold: ELEM_COLORS.cold };
  let procsHtml = '';
  if (data.procs) {
    const activeDot = Object.entries(data.procs).filter(([k, p]) => p.active && k in PROC_LABELS);
    const activeCc  = Object.entries(data.procs).filter(([k, p]) => p.active && k in CC_PROC_LABELS);
    if (activeDot.length) {
      const procRows = activeDot.map(([key, p]) => {
        const color = PROC_COLORS[key] || 'var(--accent)';
        const dot = dmgIcon(key);
        return `<tr>
          <td>${dot}${PROC_LABELS[key] || key}</td>
          <td>${p.damage_per_tick.toFixed(2)} × ${p.ticks} ticks</td>
          <td>${p.total_damage.toFixed(2)}</td>
        </tr>`;
      }).join('');
      procsHtml += `
        <h4 style="margin:12px 0 6px;color:var(--text-muted);font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em">Status Procs (if triggered)</h4>
        <table class="breakdown-table">
          <thead><tr><th>Proc</th><th>Per Tick</th><th>Total (6 ticks)</th></tr></thead>
          <tbody>${procRows}</tbody>
        </table>`;
    }
    if (activeCc.length) {
      const ccRows = activeCc.map(([key, p]) => {
        const color = CC_PROC_COLORS[key] || 'var(--accent)';
        const dot = dmgIcon(key);
        return `<tr>
          <td>${dot}${CC_PROC_LABELS[key] || key}</td>
          <td colspan="2" style="color:var(--text-muted);font-size:0.85em">${p.effect}</td>
        </tr>`;
      }).join('');
      procsHtml += `
        <h4 style="margin:12px 0 6px;color:var(--text-muted);font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em">CC / Debuff Procs (if triggered)</h4>
        <table class="breakdown-table">
          <thead><tr><th>Proc</th><th colspan="2">Effect</th></tr></thead>
          <tbody>${ccRows}</tbody>
        </table>`;
    }
  }

  // DPS section
  let dpsHtml = '';
  if (data.fire_rate != null) {
    const fr  = data.fire_rate;
    const mag = data.magazine;
    const rel = data.reload;
    const ms  = data.modded_ms || 1.0;
    const sc  = data.modded_sc || 0.0;

    const burstDps     = data.total * fr;
    const sustainedDps = (rel > 0 && mag > 1)
      ? data.total * mag / (mag / fr + rel)
      : null;

    const inherentMs = data.inherent_multishot || 1;
    const scPerPellet = data.sc_per_pellet || sc;
    const totalProjectiles = inherentMs * ms;
    const procsPerSec = scPerPellet * totalProjectiles * fr;
    let procDpsRows = '';
    let totalProcDps = 0;
    if (data.procs) {
      for (const [key, p] of Object.entries(data.procs)) {
        if (!p.active || procsPerSec <= 0 || !(key in PROC_LABELS)) continue;
        const pdps = p.damage_per_tick * procsPerSec;
        totalProcDps += pdps;
        const label = PROC_LABELS[key] || key;
        const color = ELEM_COLORS[key] || 'var(--accent)';
        const dot   = dmgIcon(key);
        procDpsRows += `<tr><td>${dot}${label} DPS</td><td></td><td>${fmtNum(pdps)}</td></tr>`;
      }
    }

    const scPct = (sc * 100).toFixed(1);
    const pelletNote = inherentMs > 1 ? ` (${(scPerPellet*100).toFixed(1)}%/pellet \u00d7${totalProjectiles.toFixed(1)})` : '';
    const footnote = procsPerSec > 0
      ? `<div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px">Proc DPS is steady-state average @ ${scPct}% status chance${pelletNote}</div>`
      : '';

    // TTK calculation (requires lastScaledEnemy from refreshEnemyScaling)
    let ttkHtml = '';
    if (lastScaledEnemy && data.total > 0) {
      const totalHP = lastScaledEnemy.health + lastScaledEnemy.shield + (eximusOn ? (lastScaledEnemy.overguard || 0) : 0);
      if (totalHP > 0) {
        const stk = Math.ceil(totalHP / data.total);
        const burstTTK = (stk - 1) / fr;
        let sustainedTTKRow = '';
        if (rel > 0 && mag > 1 && stk > mag) {
          const reloads = Math.floor((stk - 1) / mag);
          const sustainedTTK = (stk - 1) / fr + reloads * rel;
          sustainedTTKRow = `<tr><td>Sustained TTK</td><td style="font-size:0.75rem;color:var(--text-muted)">${reloads} reload${reloads !== 1 ? 's' : ''}</td><td>${sustainedTTK.toFixed(2)}s</td></tr>`;
        }
        const fmtHP = v => Number(v.toFixed(2)).toLocaleString(undefined, {maximumFractionDigits: 2});
        const levelLabel = lastScaledEnemy.level != null ? `Lvl ${lastScaledEnemy.level}` : '';
        ttkHtml = `
          <h4 style="margin:12px 0 6px;color:var(--text-muted);font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em">Kill Time</h4>
          <table class="breakdown-table">
            <thead><tr><th>Metric</th><th></th><th>Value</th></tr></thead>
            <tbody>
              <tr><td>Enemy HP</td><td style="font-size:0.75rem;color:var(--text-muted)">${levelLabel}</td><td>${fmtHP(totalHP)}</td></tr>
              <tr><td>Shots to Kill</td><td></td><td>${stk.toLocaleString()}</td></tr>
              <tr><td>Burst TTK</td><td style="font-size:0.75rem;color:var(--text-muted)">${fr}/s</td><td>${burstTTK.toFixed(2)}s</td></tr>
              ${sustainedTTKRow}
            </tbody>
          </table>`;
      }
    }

    dpsHtml = `
      <h4 style="margin:12px 0 6px;color:var(--text-muted);font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em">DPS</h4>
      <table class="breakdown-table">
        <thead><tr><th>Metric</th><th></th><th>DPS</th></tr></thead>
        <tbody>
          <tr><td>Burst DPS</td><td style="font-size:0.75rem;color:var(--text-muted)">${ms > 1.0001 ? `×${ms.toFixed(2)} multishot × ` : ''}${fr}/s</td><td>${fmtNum(burstDps)}</td></tr>
          ${sustainedDps != null ? `<tr><td>Sustained DPS</td><td style="font-size:0.75rem;color:var(--text-muted)">${rel}s reload / ${mag} mag</td><td>${fmtNum(sustainedDps)}</td></tr>` : ''}
          ${procDpsRows}
        </tbody>
        ${totalProcDps > 0 ? `<tfoot class="total-row"><tr><td colspan="2">TOTAL w/ procs</td><td>${fmtNum(burstDps + totalProcDps)}</td></tr></tfoot>` : ''}
      </table>
      ${footnote}${ttkHtml}`;
  }

  document.getElementById('results-content').innerHTML = `
    <div class="result-header">
      <h3>${esc(data.weapon)} vs ${esc(data.enemy)}</h3>
      <div class="result-total">${data.total.toFixed(2)} <span>total damage</span></div>
    </div>
    <div class="result-meta">${meta}</div>
    <table class="breakdown-table">
      <thead><tr><th>Type</th><th>Bar</th><th>Damage</th></tr></thead>
      <tbody>${rows}</tbody>
      <tfoot class="total-row">
        <tr><td colspan="2">TOTAL</td><td>${data.total.toFixed(2)}</td></tr>
      </tfoot>
    </table>
    ${msNote}
    ${procsHtml}
    ${dpsHtml}
  `;
  document.getElementById('results-content').style.display = 'block';
  initTooltips();
}
