/* alchemy.js — Void Codex Alchemy page */
/* global toggleDrawer, openGuide */

/* ── Element data ── */
var ELEMENTS = [
  { id:'cold', name:'Cold', color:'#4FC3F7', inner:true,
    icon:'<line x1="12" y1="2" x2="12" y2="22"/><line x1="4" y1="7" x2="20" y2="17"/><line x1="20" y1="7" x2="4" y2="17"/><line x1="12" y1="6" x2="9" y2="4"/><line x1="12" y1="6" x2="15" y2="4"/><line x1="12" y1="18" x2="9" y2="20"/><line x1="12" y1="18" x2="15" y2="20"/><line x1="7" y1="9" x2="5" y2="7.5"/><line x1="17" y1="9" x2="19" y2="7.5"/><line x1="7" y1="15" x2="5" y2="16.5"/><line x1="17" y1="15" x2="19" y2="16.5"/>',
    factions:{ 'Sentient':0.5, 'Techrot':-0.5 }},
  { id:'electricity', name:'Electricity', color:'#FFEB3B', inner:true,
    icon:'<polyline points="14,2 8,11 13,11 10,22" fill="none"/><line x1="16" y1="8" x2="19" y2="6"/><line x1="17" y1="13" x2="21" y2="13"/><line x1="16" y1="17" x2="19" y2="19"/>',
    factions:{ 'Corpus Amalgam':0.5, 'Murmur':0.5, 'Anarchs':0.5 }},
  { id:'heat', name:'Heat', color:'#FF7043', inner:true,
    icon:'<path d="M12 22c-4 0-7-2.5-7-6.5 0-3 2-5 4-7.5 0.5-0.6 1-1.5 1.5-2.5 0.5-1 1-2 1.5-3.5 0.5 1.5 1 2.5 1.5 3.5 0.5 1 1 1.9 1.5 2.5 2 2.5 4 4.5 4 7.5 0 4-3 6.5-7 6.5z" fill="none"/><path d="M12 22c-2 0-3.5-1.3-3.5-3.5 0-1.5 1-2.5 2-4 0.5 1 1 1.7 1.5 2.5 0.5-0.8 1-1.5 1.5-2.5 1 1.5 2 2.5 2 4 0 2.2-1.5 3.5-3.5 3.5z" fill="none"/>',
    factions:{ 'Infested':0.5, 'Kuva Grineer':-0.5 }},
  { id:'toxin', name:'Toxin', color:'#66BB6A', inner:true,
    icon:'<path d="M12 2 L12 6" fill="none"/><path d="M12 6c-3 3-6 5-6 9a6 6 0 0 0 12 0c0-4-3-6-6-9z" fill="none"/><circle cx="9.5" cy="14" r="1.2" fill="none"/><circle cx="14" cy="16" r="0.8" fill="none"/><circle cx="11" cy="18" r="0.6" fill="none"/>',
    factions:{ 'Narmer':0.5 }},
  { id:'corrosive', name:'Corrosive', color:'#8BC34A', components:['toxin','electricity'],
    icon:'<path d="M17 4a9 9 0 0 1 1 12" fill="none"/><path d="M14 19a9 9 0 0 1-10-6" fill="none"/><path d="M4 8a9 9 0 0 1 8-6" fill="none"/><path d="M8 14 L7 18" fill="none"/><path d="M13 16 L12.5 19.5" fill="none"/><circle cx="7" cy="20" r="0.8" fill="none"/><circle cx="12.5" cy="21.5" r="0.6" fill="none"/>',
    factions:{ 'Grineer':0.5, 'Kuva Grineer':0.5, 'Scaldra':0.5, 'Sentient':-0.5 }},
  { id:'radiation', name:'Radiation', color:'#FFEE58', components:['heat','electricity'],
    icon:'<circle cx="12" cy="12" r="2.5" fill="none"/><path d="M12 9.5 L10 3 A9 9 0 0 1 14 3 Z" fill="none"/><path d="M14.2 13.2 L19.5 16.5 A9 9 0 0 1 16 20 Z" fill="none"/><path d="M9.8 13.2 L4.5 16.5 A9 9 0 0 1 8 20 Z" fill="none"/>',
    factions:{ 'Sentient':0.5, 'Murmur':0.5, 'Corrupted':-0.5, 'Anarchs':-0.5 }},
  { id:'viral', name:'Viral', color:'#BA68C8', components:['cold','toxin'],
    icon:'<path d="M8 3c2 3 4 3 4 6s-4 3-4 6 2 3 4 6" fill="none"/><path d="M16 3c-2 3-4 3-4 6s4 3 4 6-2 3-4 6" fill="none"/><circle cx="12" cy="6" r="1" fill="none"/><circle cx="12" cy="12" r="1" fill="none"/><circle cx="12" cy="18" r="1" fill="none"/>',
    factions:{ 'Corrupted':0.5, 'Deimos Infested':-0.5, 'Murmur':-0.5 }},
  { id:'magnetic', name:'Magnetic', color:'#42A5F5', components:['cold','electricity'],
    icon:'<path d="M7 2v10a5 5 0 0 0 10 0V2" fill="none"/><line x1="4" y1="2" x2="10" y2="2"/><line x1="14" y1="2" x2="20" y2="2"/><path d="M4 8c-2 4 0 10 8 12" fill="none" stroke-dasharray="2 2"/><path d="M20 8c2 4 0 10-8 12" fill="none" stroke-dasharray="2 2"/>',
    factions:{ 'Corpus':0.5, 'Corpus Amalgam':0.5, 'Techrot':0.5, 'Narmer':-0.5 }},
  { id:'gas', name:'Gas', color:'#00BFA5', components:['heat','toxin'],
    icon:'<path d="M6 18c0-3 2-4 4-5s4-2 4-5a4 4 0 0 0-8 0" fill="none"/><path d="M10 18c0-2 1.5-3 3-4s3-2 3-4" fill="none"/><path d="M5 21c1 0 2-0.5 3-0.5s2 0.5 3 0.5 2-0.5 3-0.5 2 0.5 3 0.5" fill="none"/>',
    factions:{ 'Deimos Infested':0.5, 'Techrot':0.5, 'Scaldra':-0.5 }},
  { id:'blast', name:'Blast', color:'#EF5350', components:['cold','heat'],
    icon:'<circle cx="12" cy="12" r="2" fill="none"/><line x1="12" y1="2" x2="12" y2="7"/><line x1="12" y1="17" x2="12" y2="22"/><line x1="2" y1="12" x2="7" y2="12"/><line x1="17" y1="12" x2="22" y2="12"/><line x1="5" y1="5" x2="8.5" y2="8.5"/><line x1="15.5" y1="15.5" x2="19" y2="19"/><line x1="19" y1="5" x2="15.5" y2="8.5"/><line x1="8.5" y1="15.5" x2="5" y2="19"/>',
    factions:{ 'Deimos Infested':0.5, 'Corpus Amalgam':-0.5 }}
];

/* ── Faction metadata (Update 36+ damage effectiveness) ── */
/* Source: src/calculator.py FACTION_EFFECTIVENESS table from wiki.warframe.com */
var FACTION_META = {
  'Grineer':         { color:'#C9A227', short:'GRN', icon:'<path d="M12 2v20"/><circle cx="12" cy="12" r="8"/><path d="M4 12h16"/>' },
  'Kuva Grineer':    { color:'#B71C1C', short:'KVA', icon:'<path d="M12 2c-3 5-6 8-6 12a6 6 0 0 0 12 0c0-4-3-7-6-12z"/>' },
  'Narmer':          { color:'#D4A574', short:'NAR', icon:'<path d="M6 6 L12 2 L18 6 L18 14 L12 20 L6 14 Z"/><circle cx="9" cy="10" r="1"/><circle cx="15" cy="10" r="1"/>' },
  'Corpus':          { color:'#4FC3F7', short:'COR', icon:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><line x1="12" y1="3" x2="12" y2="8"/>' },
  'Corpus Amalgam':  { color:'#00E5C8', short:'AMG', icon:'<circle cx="8" cy="12" r="5"/><circle cx="16" cy="12" r="5"/><line x1="11" y1="12" x2="13" y2="12"/>' },
  'Infested':        { color:'#9CCC65', short:'INF', icon:'<path d="M12 3c-2 2-5 2-5 6s3 4 2 7 3 4 3 5 2-2 3-5 3-3 2-7-3-4-5-6z"/><circle cx="10" cy="11" r="0.8"/><circle cx="14" cy="13" r="0.8"/>' },
  'Deimos Infested': { color:'#EC407A', short:'DEI', icon:'<path d="M7 10a5 5 0 0 1 10 0v3l-2 4h-6l-2-4z"/><circle cx="10" cy="11" r="1"/><circle cx="14" cy="11" r="1"/><line x1="10" y1="17" x2="10" y2="20"/><line x1="14" y1="17" x2="14" y2="20"/>' },
  'Corrupted':       { color:'#FFD54F', short:'CRP', icon:'<path d="M12 2 L22 12 L12 22 L2 12 Z"/><circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="1" fill="currentColor"/>' },
  'Sentient':        { color:'#CE93D8', short:'SNT', icon:'<path d="M12 2 L14 10 L22 12 L14 14 L12 22 L10 14 L2 12 L10 10 Z"/>' },
  'Murmur':          { color:'#26C6DA', short:'MUR', icon:'<path d="M3 12c2-4 4-4 6 0s4 4 6 0 4-4 6 0"/><path d="M3 16c2-3 4-3 6 0s4 3 6 0 4-3 6 0"/>' },
  'Scaldra':         { color:'#FF5722', short:'SCA', icon:'<path d="M12 2 L16 8 L20 6 L18 12 L22 14 L16 16 L18 22 L12 18 L6 22 L8 16 L2 14 L6 12 L4 6 L8 8 Z"/>' },
  'Techrot':         { color:'#E91E63', short:'TCH', icon:'<rect x="5" y="5" width="14" height="14" rx="1"/><line x1="9" y1="2" x2="9" y2="5"/><line x1="15" y1="2" x2="15" y2="5"/><line x1="9" y1="19" x2="9" y2="22"/><line x1="15" y1="19" x2="15" y2="22"/><polyline points="10,10 13,10 11,14 14,14"/>' },
  'Anarchs':         { color:'#7E57C2', short:'ANA', icon:'<circle cx="12" cy="12" r="9"/><line x1="5" y1="16" x2="19" y2="16"/><line x1="9" y1="16" x2="12" y2="6"/><line x1="15" y1="16" x2="12" y2="6"/>' }
};

var INNER_ANGLES = [-135, -45, 135, 45];
var OUTER_ANGLES = [-90, -30, 30, 90, 150, 210];

var TACTIC_TIPS = {
  cold:        'Cold damage slows enemies and reduces their attack speed. Strong against Sentients. Resisted by Techrot.',
  electricity: 'Electricity creates a chain-lightning effect on status proc. Strong against Corpus Amalgam, Murmur, and Anarchs.',
  heat:        'Heat damage ignites enemies, dealing damage over time and stripping armor. Strong against Infested. Resisted by Kuva Grineer.',
  toxin:       'Toxin damage bypasses shields entirely, dealing damage directly to health. Strong against Narmer.',
  corrosive:   'Corrosive procs strip armor — 26% first stack, up to 80% at 10 stacks. Strong against Grineer, Kuva Grineer, and Scaldra. Resisted by Sentients.',
  viral:       'Viral increases all damage to health — the meta choice for high-level content. Strong against Corrupted. Resisted by Deimos Infested and Murmur.',
  radiation:   'Radiation causes enemies to attack each other. Strong against Sentients and Murmur. Resisted by Corrupted and Anarchs.',
  magnetic:    'Magnetic disrupts shields and energy. Strong against Corpus, Corpus Amalgam, and Techrot. Resisted by Narmer.',
  gas:         'Gas creates a lingering toxin cloud on proc. Strong against Deimos Infested and Techrot. Resisted by Scaldra.',
  blast:       'Blast knocks down enemies. Strong against Deimos Infested. Resisted by Corpus Amalgam.'
};

var selected = ELEMENTS.find(function(e) { return e.id === 'corrosive'; });
var tooltip = null;
var slot1 = null;
var slot2 = null;
var combinerResult = null;

function findEl(id) { return ELEMENTS.find(function(e) { return e.id === id; }); }

function svgIcon(el, size) {
  return '<svg width="'+size+'" height="'+size+'" viewBox="0 0 24 24" fill="none" stroke="'+el.color+'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+el.icon+'</svg>';
}

/* ── Wheel ── */
function buildWheel() {
  var wheel = document.getElementById('wheel');
  var inner = ELEMENTS.filter(function(e) { return e.inner; });
  var outer = ELEMENTS.filter(function(e) { return !e.inner; });

  inner.forEach(function(el, i) {
    var angle = INNER_ANGLES[i];
    var r = 110;
    var tx = Math.cos(angle * Math.PI / 180) * r;
    var ty = Math.sin(angle * Math.PI / 180) * r;
    var btn = document.createElement('button');
    btn.className = 'elem-btn inner' + (selected.id === el.id ? ' selected' : '');
    btn.dataset.id = el.id;
    btn.style.cssText = 'left:50%;top:50%;transform:translate(calc(-50% + '+tx+'px),calc(-50% + '+ty+'px));--tx:calc(-50% + '+tx+'px);--ty:calc(-50% + '+ty+'px)';
    btn.innerHTML = '<div class="elem-shine"></div><div class="elem-glow" style="background:'+el.color+'"></div>'+svgIcon(el, 24)+'<span class="elem-name">'+el.name+'</span>';
    btn.onclick = function() { selectElement(el.id); };
    wheel.appendChild(btn);
  });

  outer.forEach(function(el, i) {
    var angle = OUTER_ANGLES[i];
    var r = 200;
    var tx = Math.cos(angle * Math.PI / 180) * r;
    var ty = Math.sin(angle * Math.PI / 180) * r;
    var btn = document.createElement('button');
    btn.className = 'elem-btn outer' + (selected.id === el.id ? ' selected' : '');
    btn.dataset.id = el.id;
    btn.style.cssText = 'left:50%;top:50%;transform:translate(calc(-50% + '+tx+'px),calc(-50% + '+ty+'px));--tx:calc(-50% + '+tx+'px);--ty:calc(-50% + '+ty+'px)';
    btn.innerHTML = '<div class="elem-shine"></div><div class="elem-glow" style="background:'+el.color+'"></div>'+svgIcon(el, 24);
    btn.onclick = function() { selectElement(el.id); };
    wheel.appendChild(btn);
  });
}

/* ── Banner ── */
function renderBanner() {
  var el = selected;
  var banner = document.getElementById('selected-banner');
  var comboHTML = '';
  var descText = TACTIC_TIPS[el.id] || 'Elemental damage type';

  if (el.components) {
    var c = el.components.map(findEl);
    comboHTML = '<div class="sb-combo">(' + c[0].name + ' + ' + c[1].name + ')</div>';
  }

  var statusDesc = el.components
    ? (el.id === 'corrosive' ? 'Reduces target armor permanently'
      : el.id === 'viral' ? 'Increases damage to health'
      : el.id === 'radiation' ? 'Causes enemies to attack each other'
      : el.id === 'magnetic' ? 'Disrupts shields and energy'
      : el.id === 'gas' ? 'Creates a cloud of toxin damage'
      : el.id === 'blast' ? 'Knocks down enemies'
      : 'Combined elemental damage')
    : 'Base elemental damage';

  banner.innerHTML =
    '<div class="sb-glow" style="background:'+el.color+'"></div>' +
    '<div class="sb-icon" style="background:'+el.color+'15;border:1px solid '+el.color+'40">'+svgIcon(el, 32)+'</div>' +
    '<div class="sb-info"><div class="sb-name">'+el.name+'</div>'+comboHTML+'</div>' +
    '<div class="sb-status"><div class="sb-badge">Status Active</div><div class="sb-desc">'+statusDesc+'</div></div>';
}

/* ── Faction effectiveness cards ── */
function factionSvg(name, size) {
  var meta = FACTION_META[name];
  if (!meta) return '';
  return '<svg class="faction-glyph" width="'+size+'" height="'+size+'" viewBox="0 0 24 24" fill="none" stroke="'+meta.color+'" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+meta.icon+'</svg>';
}

function renderCards() {
  var container = document.getElementById('cards');
  container.innerHTML = '';
  var el = selected;
  var strong = [];
  var weak = [];
  Object.keys(el.factions || {}).forEach(function(name) {
    var v = el.factions[name];
    if (v > 0) strong.push({ name: name, value: v });
    else if (v < 0) weak.push({ name: name, value: v });
  });
  strong.sort(function(a,b) { return b.value - a.value; });
  weak.sort(function(a,b) { return a.value - b.value; });

  var cats = [
    { title:'Strong Against', items: strong, cls:'positive' },
    { title:'Resisted By',    items: weak,   cls:'negative' }
  ];

  cats.forEach(function(cat) {
    var card = document.createElement('div');
    card.className = 'hw-card faction-card';
    var tag = cat.items.length === 0
      ? 'NEUTRAL'
      : cat.items.length + (cat.items.length === 1 ? ' FACTION' : ' FACTIONS');
    var rowsHTML = '';
    if (cat.items.length) {
      rowsHTML = cat.items.map(function(m, i) {
        var meta = FACTION_META[m.name] || { color:'#888', short:'?', icon:'' };
        var v = Math.round(m.value * 100);
        var cls = v > 0 ? 'positive' : 'negative';
        var display = v > 0 ? '+'+v+'%' : v+'%';
        var pct = Math.abs(v);
        return '<div class="faction-row" data-name="'+m.name+'" data-display="'+display+'" data-cls="'+cls+'" style="--faction-color:'+meta.color+';--delay:'+(0.08+i*0.1)+'s">' +
          '<div class="faction-row-header">' +
            '<div class="faction-badge">' +
              factionSvg(m.name, 18) +
              '<span class="faction-short">'+meta.short+'</span>' +
              '<span class="faction-name">'+m.name+'</span>' +
            '</div>' +
            '<span class="faction-value '+cls+'">'+display+'</span>' +
          '</div>' +
          '<div class="faction-bar-track">' +
            '<div class="faction-bar-fill '+cls+'" data-width="'+pct+'"></div>' +
            '<div class="faction-bar-tip '+cls+'" data-pct="'+pct+'"></div>' +
          '</div>' +
        '</div>';
      }).join('');
    } else {
      rowsHTML =
        '<div class="faction-empty">' +
          '<div class="faction-empty-ring"></div>' +
          '<div class="faction-empty-dots">• • •</div>' +
          '<div class="faction-empty-text">NO INTERACTION</div>' +
        '</div>';
    }
    card.innerHTML =
      '<div class="hw-card-header">' +
        '<div class="hw-card-title">'+cat.title+'</div>' +
        '<div class="hw-card-tag '+cat.cls+'">'+tag+'</div>' +
      '</div>' +
      '<div class="faction-list">'+rowsHTML+'</div>' +
      '<div class="hw-card-footer"></div>';
    container.appendChild(card);

    // Animate bars
    requestAnimationFrame(function() {
      card.querySelectorAll('.faction-row').forEach(function(row) {
        var d = parseFloat(row.style.getPropertyValue('--delay')) * 1000;
        var fill = row.querySelector('.faction-bar-fill');
        var tip = row.querySelector('.faction-bar-tip');
        setTimeout(function() {
          if (fill) fill.style.width = fill.dataset.width + '%';
          if (tip) {
            tip.style.opacity = '1';
            if (tip.classList.contains('positive')) tip.style.left = tip.dataset.pct + '%';
            else tip.style.right = tip.dataset.pct + '%';
          }
        }, d);
      });
    });

    // Tooltips
    card.querySelectorAll('.faction-row').forEach(function(row) {
      row.addEventListener('mouseenter', function() {
        tooltip.querySelector('.tt-name').textContent = row.dataset.name;
        var v = tooltip.querySelector('.tt-val');
        v.textContent = row.dataset.display;
        v.className = 'tt-val ' + row.dataset.cls;
        tooltip.classList.add('visible');
      });
      row.addEventListener('mousemove', function(e) {
        tooltip.style.left = (e.clientX+12)+'px';
        tooltip.style.top = (e.clientY-36)+'px';
      });
      row.addEventListener('mouseleave', function() {
        tooltip.classList.remove('visible');
      });
    });
  });
}

/* ── Tactic tip ── */
function renderTactic() {
  var tip = document.getElementById('tactic-text');
  tip.textContent = TACTIC_TIPS[selected.id] || 'Elemental damage types have unique status effects. Analyze the enemy faction and health type to maximize your combat efficiency.';
}

/* ── Select element ── */
function selectElement(id) {
  selected = findEl(id);
  document.querySelectorAll('.elem-btn').forEach(function(b) {
    b.classList.toggle('selected', b.dataset.id === id);
  });
  renderBanner();
  renderCards();
  renderTactic();
}

/* ── Combiner ── */
function buildCombinerBases() {
  var container = document.getElementById('combiner-bases');
  var bases = ELEMENTS.filter(function(e) { return e.inner; });
  bases.forEach(function(el) {
    var btn = document.createElement('button');
    btn.className = 'combiner-base-btn';
    btn.dataset.id = el.id;
    btn.innerHTML = svgIcon(el, 20) + '<span>'+el.name+'</span>';
    btn.onclick = function() { handleBaseClick(el); };
    container.appendChild(btn);
  });
}

function handleBaseClick(el) {
  if (!slot1) { slot1 = el; }
  else if (!slot2) { slot2 = el; }
  else { slot2 = el; }
  updateCombiner();
}

function clearSlot(n) {
  if (n === 1) slot1 = null;
  else slot2 = null;
  updateCombiner();
}

function updateCombiner() {
  var s1 = document.getElementById('slot1');
  var s2 = document.getElementById('slot2');
  var res = document.getElementById('combiner-result');

  // Slot 1
  if (slot1) {
    s1.classList.add('filled');
    s1.innerHTML = svgIcon(slot1, 32);
    document.getElementById('slot1-label').textContent = slot1.name;
  } else {
    s1.classList.remove('filled');
    s1.innerHTML = '<svg class="combiner-slot-plus" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';
    document.getElementById('slot1-label').textContent = 'Slot 1';
  }

  // Slot 2
  if (slot2) {
    s2.classList.add('filled');
    s2.innerHTML = svgIcon(slot2, 32);
    document.getElementById('slot2-label').textContent = slot2.name;
  } else {
    s2.classList.remove('filled');
    s2.innerHTML = '<svg class="combiner-slot-plus" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';
    document.getElementById('slot2-label').textContent = 'Slot 2';
  }

  // Result
  combinerResult = null;
  if (slot1 && slot2) {
    if (slot1.id === slot2.id) {
      combinerResult = slot1;
    } else {
      combinerResult = ELEMENTS.find(function(e) {
        return e.components && e.components.indexOf(slot1.id) !== -1 && e.components.indexOf(slot2.id) !== -1;
      }) || null;
    }
  }

  if (combinerResult) {
    res.classList.add('has-result');
    res.innerHTML = svgIcon(combinerResult, 40);
    document.getElementById('result-label').textContent = combinerResult.name;
  } else {
    res.classList.remove('has-result');
    res.innerHTML = '<svg class="combiner-result-empty" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="32" height="32"><path d="M13 2l-2 6h5l-4 12"/><line x1="4" y1="4" x2="20" y2="20" stroke-opacity="0.3"/></svg>';
    document.getElementById('result-label').textContent = 'Result';
  }

  // Highlight active base buttons
  document.querySelectorAll('.combiner-base-btn').forEach(function(btn) {
    var active = (slot1 && btn.dataset.id === slot1.id) || (slot2 && btn.dataset.id === slot2.id);
    btn.classList.toggle('active', active);
  });
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', function() {
  tooltip = document.getElementById('bar-tooltip');

  // Slot click handlers
  document.getElementById('slot1').onclick = function() { clearSlot(1); };
  document.getElementById('slot2').onclick = function() { clearSlot(2); };
  document.getElementById('combiner-result').onclick = function() {
    if (combinerResult) selectElement(combinerResult.id);
  };

  buildWheel();
  buildCombinerBases();
  renderBanner();
  renderCards();
  renderTactic();

  // Version
  fetch('/api/version').then(function(r) { return r.json(); }).then(function(d) {
    var v = document.getElementById('nav-ver');
    if (v) v.textContent = 'v' + d.app;
  }).catch(function() {});
});
