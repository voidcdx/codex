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

// ── Custom Select ─────────────────────────────────────────
// Wraps a hidden native <select> with a glassmorphic custom dropdown.
// The native select stays in the DOM so existing .value reads keep working.

function _buildCustomSelectUI(wrap, sel, onChange) {
  const currentText = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : '';
  wrap.innerHTML = `
    <button type="button" class="custom-select-btn" aria-haspopup="listbox">
      <span class="custom-select-value">${esc(currentText)}</span>
      <svg class="custom-select-arrow" width="10" height="6" viewBox="0 0 10 6" fill="none">
        <path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>
    <div class="custom-select-dropdown" role="listbox"></div>
  `;
  const btn = wrap.querySelector('.custom-select-btn');
  const dropdown = wrap.querySelector('.custom-select-dropdown');

  function rebuildOptions() {
    dropdown.innerHTML = '';
    for (const opt of sel.options) {
      const div = document.createElement('div');
      div.className = 'custom-select-option' + (opt.value === sel.value ? ' selected' : '');
      div.textContent = opt.text;
      div.dataset.value = opt.value;
      div.addEventListener('mousedown', e => {
        e.preventDefault();
        sel.value = opt.value;
        sel.dispatchEvent(new Event('change'));
        wrap.querySelector('.custom-select-value').textContent = opt.text;
        dropdown.querySelectorAll('.custom-select-option').forEach(o =>
          o.classList.toggle('selected', o.dataset.value === opt.value)
        );
        wrap.classList.remove('open');
        if (onChange) onChange();
      });
      dropdown.appendChild(div);
    }
  }
  rebuildOptions();

  btn.addEventListener('click', () => {
    wrap.classList.toggle('open');
  });
  btn.addEventListener('keydown', e => {
    if (e.key === 'Escape') wrap.classList.remove('open');
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); wrap.classList.toggle('open'); }
  });
  document.addEventListener('mousedown', e => {
    if (!wrap.contains(e.target)) wrap.classList.remove('open');
  });

  wrap._rebuildOptions = rebuildOptions;
}

function setupCustomSelect(selectId, onChange) {
  const sel = document.getElementById(selectId);
  const wrap = document.querySelector(`.custom-select-wrap[data-for="${selectId}"]`);
  if (!sel || !wrap) return;
  _buildCustomSelectUI(wrap, sel, onChange);
}

function refreshCustomSelect(selectId) {
  const sel = document.getElementById(selectId);
  const wrap = document.querySelector(`.custom-select-wrap[data-for="${selectId}"]`);
  if (!sel || !wrap) return;
  if (wrap._rebuildOptions) {
    wrap._rebuildOptions();
    const valSpan = wrap.querySelector('.custom-select-value');
    if (valSpan && sel.options[sel.selectedIndex]) {
      valSpan.textContent = sel.options[sel.selectedIndex].text;
    }
  }
}

function setCustomSelectValue(selectId, value) {
  const sel = document.getElementById(selectId);
  if (sel) sel.value = value;
  refreshCustomSelect(selectId);
}
