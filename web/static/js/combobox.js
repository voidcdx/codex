// ═══════════════════════════════════════════════════════
// Void Codex — Combobox Widget
// ═══════════════════════════════════════════════════════

function setupCombobox(inputId, dropdownId, items, onSelect, getImageUrl) {
  const input = document.getElementById(inputId);
  const dropdown = document.getElementById(dropdownId);
  const panel = input.closest('.panel');
  let _confirmed = '';

  function esc(s) { return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;'); }

  function render(q) {
    const lq = q.toLowerCase();
    const matches = lq ? items.filter(n => n.toLowerCase().includes(lq)) : items;
    const shown = matches.slice(0, 80);
    dropdown.innerHTML = shown.map(n => {
      const img = getImageUrl
        ? `<img class="combobox-img" src="${getImageUrl(n)}" alt="" onerror="this.style.display='none'">`
        : '';
      return `<div class="combobox-item" data-value="${esc(n)}">${img}${esc(n)}</div>`;
    }).join('');
    if (matches.length > 80) {
      dropdown.innerHTML += `<div class="combobox-hint">${matches.length} results \u2014 type to narrow</div>`;
    }
    const isOpen = shown.length > 0;
    dropdown.classList.toggle('open', isOpen);
    if (panel) panel.classList.toggle('combobox-open', isOpen);
  }

  function commit(name) {
    _confirmed = name;
    input.value = name;
    close();
    toggleSearchClear(input);
    if (onSelect) onSelect(name);
  }

  function close() {
    if (input.value !== _confirmed) {
      input.value = _confirmed;
      toggleSearchClear(input);
    }
    dropdown.classList.remove('open');
    if (panel) panel.classList.remove('combobox-open');
  }

  input.addEventListener('focus', () => { input.value = ''; toggleSearchClear(input); render(''); });
  input.addEventListener('input', () => { toggleSearchClear(input); render(input.value); });
  input.addEventListener('combobox-clear', () => { _confirmed = ''; });
  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') { close(); input.blur(); }
    if (e.key === 'Enter') {
      const first = dropdown.querySelector('.combobox-item');
      if (first) commit(first.dataset.value);
    }
  });

  dropdown.addEventListener('mousedown', e => {
    e.preventDefault();
    const item = e.target.closest('.combobox-item');
    if (item) commit(item.dataset.value);
  });

  let _touchStartY = 0;
  dropdown.addEventListener('touchstart', e => { _touchStartY = e.touches[0].clientY; }, { passive: true });
  dropdown.addEventListener('touchend', e => {
    const item = e.target.closest('.combobox-item');
    if (item && Math.abs(e.changedTouches[0].clientY - _touchStartY) < 10) {
      e.preventDefault();
      commit(item.dataset.value);
    }
  });

  document.addEventListener('mousedown', e => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) close();
  });

  return { set: commit };
}

function clearCombobox(which) {
  const input = document.getElementById(`${which}-search`);
  const dropdown = document.getElementById(`${which}-dropdown`);
  input.dispatchEvent(new CustomEvent('combobox-clear'));
  input.value = '';
  dropdown.classList.remove('open');
  toggleSearchClear(input);
  input.focus();
}

// ── Item Picker Modal (weapon / enemy) ──────────────────────────────────────
const _pickerConfigs = {};
let _pickerActive = null;

function setupPickerModal(which, items, onSelect, getImageUrl) {
  _pickerConfigs[which] = { items, onSelect, getImageUrl };
  return {
    set(name) {
      const input = document.getElementById(`${which}-search`);
      if (input) input.value = name;
      if (onSelect) onSelect(name);
    }
  };
}

function _applyVisualViewport() {
  const overlay = document.getElementById('item-picker-overlay');
  if (!overlay || !_pickerActive) return;
  const vv = window.visualViewport;
  overlay.style.top    = vv.offsetTop + 'px';
  overlay.style.height = vv.height + 'px';
}

function openPickerModal(which) {
  _pickerActive = which;
  const cfg = _pickerConfigs[which];
  if (!cfg) return;
  document.getElementById('item-picker-title').textContent =
    which === 'weapon' ? 'SELECT WEAPON' : 'SELECT ENEMY';
  const searchEl = document.getElementById('item-picker-search');
  searchEl.value = '';
  renderPickerResults('');
  document.body.style.overflow = 'hidden';
  const overlay = document.getElementById('item-picker-overlay');
  overlay.style.top = '';
  overlay.style.height = '';
  overlay.classList.add('active');
  if (window.visualViewport) {
    _applyVisualViewport();
    window.visualViewport.addEventListener('resize', _applyVisualViewport);
    window.visualViewport.addEventListener('scroll', _applyVisualViewport);
  }
  setTimeout(() => searchEl.focus(), 50);
}

function closePickerModal(e) {
  if (e && e.target !== document.getElementById('item-picker-overlay')) return;
  _closePickerNow();
}

function _closePickerNow() {
  const overlay = document.getElementById('item-picker-overlay');
  overlay.classList.remove('active');
  overlay.style.top = '';
  overlay.style.height = '';
  document.body.style.overflow = '';
  if (window.visualViewport) {
    window.visualViewport.removeEventListener('resize', _applyVisualViewport);
    window.visualViewport.removeEventListener('scroll', _applyVisualViewport);
  }
  _pickerActive = null;
}

function renderPickerResults(q) {
  if (!_pickerActive) return;
  const cfg = _pickerConfigs[_pickerActive];
  const lq = q.toLowerCase();
  const matches = lq ? cfg.items.filter(n => n.toLowerCase().includes(lq)) : cfg.items;
  const shown = matches.slice(0, 80);
  const list = document.getElementById('item-picker-list');
  list.innerHTML = shown.map(n => {
    const img = cfg.getImageUrl
      ? `<img class="combobox-img" src="${cfg.getImageUrl(n)}" alt="" onerror="this.style.display='none'">`
      : '';
    return `<div class="item-picker-item" data-value="${esc(n)}">${img}${esc(n)}</div>`;
  }).join('') + (matches.length > 80
    ? `<div class="combobox-hint">${matches.length} results — type to narrow</div>`
    : '');
}

document.addEventListener('DOMContentLoaded', () => {
  const list = document.getElementById('item-picker-list');
  if (!list) return;

  list.addEventListener('mousedown', e => {
    const item = e.target.closest('.item-picker-item');
    if (!item || !_pickerActive) return;
    e.preventDefault();
    const which = _pickerActive;
    const name = item.dataset.value;
    const input = document.getElementById(`${which}-search`);
    if (input) input.value = name;
    _closePickerNow();
    _pickerConfigs[which]?.onSelect(name);
  });

  let _touchStartY = 0;
  list.addEventListener('touchstart', e => { _touchStartY = e.touches[0].clientY; }, { passive: true });
  list.addEventListener('touchend', e => {
    const item = e.target.closest('.item-picker-item');
    if (!item || !_pickerActive) return;
    if (Math.abs(e.changedTouches[0].clientY - _touchStartY) >= 10) return;
    e.preventDefault();
    const which = _pickerActive;
    const name = item.dataset.value;
    const input = document.getElementById(`${which}-search`);
    if (input) input.value = name;
    _closePickerNow();
    _pickerConfigs[which]?.onSelect(name);
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && _pickerActive) _closePickerNow();
  });
});

