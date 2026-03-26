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
  weaponCombo.set('Acceltra');

  const HIDDEN_ENEMY_NAMES = new Set([
    'Explosive Barrel', 'Storage Container', '[Wiki Dummy]',
    'Clem', 'Darvo', 'Hacked Drone'
  ]);
  const HIDDEN_ENEMY_PATTERNS = [/\bturret\b/i, /\bdropship\b/i, /\bcrewship\b/i];
  const FAUNA_NAMES = new Set([
    'Alpine Monitor Sawgaw', 'Amethyst Nexifera', 'Ashen Kuaka',
    'Bau Vasca Kavat', 'Black-Banded Bolarola', 'Brindle Kubrodon',
    'Coastal Mergoo', 'Common Avichaea', 'Common Condroc',
    'Crescent Vulpaphyla', 'Dappled Horrasque', 'Death Scuttler',
    'Delicate Pobber', 'Desert Skate', 'Dusky-Headed Virmink',
    'Emperor Condroc', 'Fire-Veined Stover', 'Flossy Sawgaw',
    'Frogmouthed Sawgaw', 'Fuming Dax Stover', 'Ghost Kuaka',
    'Green Velocipod', 'Horrasque Stormer', 'Howler Undazoa',
    'Kavat', 'Kubrodon Incarnadine', 'Kubrow',
    'Medjay Predasite', 'Nephil Vasca Kavat', 'Ostia Vasca Kavat',
    'Panzer Vulpaphyla', 'Pharaoh Predasite', 'Plains Kuaka',
    'Purple Velocipod', 'Red-Crested Virmink', 'Rogue Condroc',
    'Scarlet Nexifera', 'Scuttlers', 'Sentinel Stover',
    'Sly Vulpaphyla', 'Splendid Mergoo', 'Sporule Avichaea',
    'Spotted Bolarola', 'Subterranean Pobber', 'Sunny Pobber',
    'Swimmer Horrasque', 'Thorny Bolarola', 'Umber Undazoa',
    'Vallis Kubrodon', 'Vaporous Undazoa', 'Viscid Avichaea',
    'Viridian Nexifera', 'Vizier Predasite', 'White Velocipod',
    'White-Breasted Virmink', 'Woodland Mergoo'
  ]);
  const visibleEnemies = allEnemies.filter(e =>
    !HIDDEN_ENEMY_NAMES.has(e.name) &&
    !FAUNA_NAMES.has(e.name) &&
    !HIDDEN_ENEMY_PATTERNS.some(p => p.test(e.name))
  );

  enemyCombo = setupCombobox('enemy-search', 'enemy-dropdown',
    visibleEnemies.map(e => e.name),
    () => { showEnemyStats(getCurrentEnemy()); }
  );
  enemyCombo.set('Corrupted Heavy Gunner');

  initModGrid();

  setupSelectDropdown('crit-mode');
  setupSelectDropdown('body-part-select');
  setupSelectDropdown('bonus-element-type', () => {
    updateModdedStats();
    updateElementBadges();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadData();
  if (typeof initArmorStrip === 'function') initArmorStrip();
  fetch('/api/version').then(r => r.json()).then(v => {
    document.getElementById('guide-app-ver').textContent  = `Void Codex v${v.app}`;
    document.getElementById('guide-game-ver').textContent = `Game data: ${v.game_data}`;
    const navVer = document.getElementById('nav-ver');
    if (navVer) navVer.textContent = `v${v.app}`;
  }).catch(() => {});
});

// ── Mobile sidebar toggle ───────────────────────────────
function toggleDrawer() {
  const btn     = document.getElementById('burger-btn');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (!sidebar) return;
  const open = sidebar.classList.toggle('open');
  if (overlay) overlay.classList.toggle('open', open);
  if (btn) btn.classList.toggle('open', open);
}

// Mod picker search
document.addEventListener('DOMContentLoaded', () => {
  const search = document.getElementById('mod-picker-search');
  if (search) search.addEventListener('input', function() {
    renderPickerList(this.value);
    toggleSearchClear(this);
  });
});
