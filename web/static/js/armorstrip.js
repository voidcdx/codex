// ═══════════════════════════════════════════════════════
// Void Codex — Armor Strip Panel
// ═══════════════════════════════════════════════════════

function updateArmorStripDisplay() {
  const abilityPct = (parseInt(document.getElementById('strip-ability-pct').value, 10) || 0) / 100;
  const cpPct      = (parseInt(document.getElementById('strip-cp-pct').value,      10) || 0) / 100;
  const siHits     = parseInt(document.getElementById('strip-si-hits').value,     10) || 0;
  const siPerHit   = parseFloat(document.getElementById('strip-si-per-hit').value)    || 6.0;

  document.getElementById('strip-ability-badge').textContent = Math.round(abilityPct * 100) + '%';
  document.getElementById('strip-cp-badge').textContent      = Math.round(cpPct * 100) + '%';

  const flatRemoved = siHits * siPerHit;
  document.getElementById('strip-si-total').textContent = flatRemoved.toLocaleString(undefined, {maximumFractionDigits: 1});

  const scaledArmor = lastScaledEnemy ? lastScaledEnemy.armor : 0;

  if (!lastScaledEnemy || scaledArmor === 0) {
    document.getElementById('strip-armor-val').textContent = '0';
    document.getElementById('strip-dr-val').textContent    = '0%';
    document.getElementById('strip-bar-fill').style.width  = '0%';
    document.getElementById('strip-stripped-pct').textContent = '0% stripped';
    return;
  }

  const pctStripped = Math.min(1.0, abilityPct + cpPct);
  const finalArmor  = Math.max(0, scaledArmor * (1.0 - pctStripped) - flatRemoved);
  const dr          = finalArmor > 0 ? (finalArmor / (finalArmor + 300)) : 0;

  document.getElementById('strip-armor-val').textContent = finalArmor.toLocaleString(undefined, {maximumFractionDigits: 1});
  document.getElementById('strip-dr-val').textContent    = (dr * 100).toFixed(1) + '%';

  const strippedFraction = Math.min(1.0, (scaledArmor - finalArmor) / scaledArmor);
  document.getElementById('strip-bar-fill').style.width  = (strippedFraction * 100).toFixed(1) + '%';
  document.getElementById('strip-stripped-pct').textContent = (strippedFraction * 100).toFixed(1) + '% stripped';
}

function getArmorStripPayload() {
  const abilityPct = (parseInt(document.getElementById('strip-ability-pct').value, 10) || 0) / 100;
  const cpPct      = (parseInt(document.getElementById('strip-cp-pct').value,      10) || 0) / 100;
  const siHits     = parseInt(document.getElementById('strip-si-hits').value,     10) || 0;
  const siPerHit   = parseFloat(document.getElementById('strip-si-per-hit').value)    || 6.0;
  return {
    ability_strip_pct:      Math.min(1.0, abilityPct),
    cp_strip_pct:           Math.min(1.0, cpPct),
    shattering_impact_flat: siHits * siPerHit,
  };
}

function initArmorStrip() {
  const ids = ['strip-ability-pct', 'strip-cp-pct', 'strip-si-hits', 'strip-si-per-hit'];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateArmorStripDisplay);
  });
  updateArmorStripDisplay();
}
