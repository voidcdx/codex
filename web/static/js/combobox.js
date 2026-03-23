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

function setupSearch(inputId, selectId, getNames, onChange) {
  const el = document.getElementById(inputId);
  el.addEventListener('input', function() {
    const q = this.value.toLowerCase();
    const names = getNames().filter(n => n.toLowerCase().includes(q));
    populateSelect(selectId, names);
    if (onChange) onChange();
    toggleSearchClear(this);
  });
}
