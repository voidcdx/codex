// ═══════════════════════════════════════════════════════
// Void Codex — Utility Functions
// ═══════════════════════════════════════════════════════

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function fmtNum(n) {
  return n.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

function dmgIcon(type, size) {
  size = size || 14;
  const color = ELEM_COLORS[type] || '#888';
  const inner = DMG_ICONS[type];
  if (!inner) return '<span class="elem-dot" style="background:' + color + '"></span>';
  return '<svg class="dmg-icon" width="' + size + '" height="' + size + '" viewBox="0 0 16 16" fill="none" style="color:' + color + '" aria-hidden="true">' + inner + '</svg>';
}

function initTooltips() {
  document.querySelectorAll('[data-tooltip]').forEach(el => {
    if (el._tippyBound) return;
    const text = TOOLTIPS[el.dataset.tooltip];
    if (!text) return;
    el._tippyBound = true;
    if (typeof tippy === 'function') {
      tippy(el, {
        content: text,
        placement: 'top',
        theme: 'warframe',
        delay: [200, 0],
        maxWidth: 280,
      });
    }
  });
}

function populateSelect(id, names) {
  const sel = document.getElementById(id);
  sel.innerHTML = names.map(n => `<option value="${esc(n)}">${esc(n)}</option>`).join('');
}

function setSelectValue(id, value) {
  const sel = document.getElementById(id);
  for (const opt of sel.options) {
    if (opt.value === value) { sel.value = value; return; }
  }
}

function setSelectByText(sel, text) {
  for (const opt of sel.options) {
    if (opt.value === text) { sel.value = text; return; }
  }
}

function toggleSearchClear(input) {
  const wrap = input.closest('.search-wrap');
  if (wrap) wrap.classList.toggle('has-value', input.value.length > 0);
}

function clearSearch(inputId) {
  const el = document.getElementById(inputId);
  el.value = '';
  el.dispatchEvent(new Event('input'));
  el.focus();
}

function getCurrentWeapon() {
  const name = document.getElementById('weapon-search').value;
  return allWeapons.find(x => x.name === name) || null;
}

function getCurrentEnemy() {
  const name = document.getElementById('enemy-search').value;
  return allEnemies.find(x => x.name === name) || null;
}

function getBonusElement() {
  const div = document.getElementById('bonus-element-div');
  if (!div || div.style.display === 'none') return {};
  return {
    bonus_element: document.getElementById('bonus-element-type').value,
    bonus_element_pct: (parseFloat(document.getElementById('bonus-element-pct').value) || 25) / 100.0,
  };
}
