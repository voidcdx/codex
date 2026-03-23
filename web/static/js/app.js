// ═══════════════════════════════════════════════════════
// Void Codex — App Bootstrap
// ═══════════════════════════════════════════════════════

async function loadData() {
  [allWeapons, allMods, allEnemies] = await Promise.all([
    fetch('/api/weapons').then(r => r.json()),
    fetch('/api/mods').then(r => r.json()),
    fetch('/api/enemies').then(r => r.json()),
  ]);

  const HIDDEN_WEAPON_CLASSES = new Set(['Exalted Weapon']);
  const HIDDEN_WEAPON_NAMES  = new Set(['Garuda Talons', 'Garuda Prime Talons']);
  const visibleWeapons = allWeapons.filter(w =>
    !HIDDEN_WEAPON_CLASSES.has(w.class) && !HIDDEN_WEAPON_NAMES.has(w.name)
  );

  weaponCombo = setupCombobox('weapon-search', 'weapon-dropdown',
    visibleWeapons.map(w => w.name),
    () => onWeaponChange(),
    name => {
      const w = allWeapons.find(x => x.name === name);
      return w?.image ? `/static/images/weapons/${w.image}` : '';
    }
  );
  enemyCombo = setupCombobox('enemy-search', 'enemy-dropdown',
    allEnemies.map(e => e.name),
    () => { showEnemyStats(getCurrentEnemy()); }
  );

  initModGrid();
}

document.addEventListener('DOMContentLoaded', () => {
  loadData();
  fetch('/api/version').then(r => r.json()).then(v => {
    document.getElementById('guide-app-ver').textContent  = `Void Codex v${v.app}`;
    document.getElementById('guide-game-ver').textContent = `Game data: ${v.game_data}`;
  }).catch(() => {});
});

// Mod picker search
document.addEventListener('DOMContentLoaded', () => {
  const search = document.getElementById('mod-picker-search');
  if (search) search.addEventListener('input', function() {
    renderPickerList(this.value);
    toggleSearchClear(this);
  });
});
