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

// ── Select Dropdown ────────────────────────────────────────
// Hides native <select>, builds a themed button+dropdown using
// the same .combobox-dropdown / .combobox-item CSS as search boxes.

function setupSelectDropdown(selectId, onChange) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  sel.style.display = 'none';

  const wrap = document.createElement('div');
  wrap.className = 'sel-wrap';
  sel.parentNode.insertBefore(wrap, sel.nextSibling);

  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'sel-btn';

  const dd = document.createElement('div');
  dd.className = 'combobox-dropdown sel-dropdown';

  wrap.appendChild(btn);
  wrap.appendChild(dd);

  function rebuild() {
    dd.innerHTML = '';
    for (const opt of sel.options) {
      const div = document.createElement('div');
      div.className = 'combobox-item' + (opt.value === sel.value ? ' sel-selected' : '');
      div.textContent = opt.text;
      div.dataset.value = opt.value;
      div.addEventListener('mousedown', e => {
        e.preventDefault();
        sel.value = opt.value;
        sel.dispatchEvent(new Event('change'));
        close();
        if (onChange) onChange();
      });
      div.addEventListener('touchend', e => {
        e.preventDefault();
        sel.value = opt.value;
        sel.dispatchEvent(new Event('change'));
        close();
        if (onChange) onChange();
      });
      dd.appendChild(div);
    }
    btn.textContent = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : '';
  }

  function open()  { dd.classList.add('open');    wrap.classList.add('open'); }
  function close() { dd.classList.remove('open'); wrap.classList.remove('open'); }

  rebuild();

  btn.addEventListener('click', () => dd.classList.contains('open') ? close() : open());
  document.addEventListener('mousedown', e => { if (!wrap.contains(e.target)) close(); });

  sel.addEventListener('change', () => {
    if (sel.options[sel.selectedIndex]) btn.textContent = sel.options[sel.selectedIndex].text;
    dd.querySelectorAll('.combobox-item').forEach(d => d.classList.toggle('sel-selected', d.dataset.value === sel.value));
  });

  wrap._rebuild = rebuild;
}

function refreshSelectDropdown(selectId) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  const wrap = sel.parentNode.querySelector('.sel-wrap');
  if (wrap && wrap._rebuild) wrap._rebuild();
}
