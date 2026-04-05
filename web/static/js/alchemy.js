/* alchemy.js — Void Codex Alchemy page */
/* global toggleDrawer, openGuide */

/* ── Element data ── */
var ELEMENTS = [
  { id:'cold', name:'Cold', color:'#4FC3F7', inner:true,
    icon:'<line x1="12" y1="2" x2="12" y2="22"/><line x1="4" y1="7" x2="20" y2="17"/><line x1="20" y1="7" x2="4" y2="17"/><line x1="12" y1="6" x2="9" y2="4"/><line x1="12" y1="6" x2="15" y2="4"/><line x1="12" y1="18" x2="9" y2="20"/><line x1="12" y1="18" x2="15" y2="20"/><line x1="7" y1="9" x2="5" y2="7.5"/><line x1="17" y1="9" x2="19" y2="7.5"/><line x1="7" y1="15" x2="5" y2="16.5"/><line x1="17" y1="15" x2="19" y2="16.5"/>',
    multipliers:{ armor:[{type:'Alloy',value:0.25}], flesh:[{type:'Infested',value:0.25}], shields:[{type:'Shield',value:0.5}], machinery:[] }},
  { id:'electricity', name:'Electricity', color:'#FFEB3B', inner:true,
    icon:'<polyline points="14,2 8,11 13,11 10,22" fill="none"/><line x1="16" y1="8" x2="19" y2="6"/><line x1="17" y1="13" x2="21" y2="13"/><line x1="16" y1="17" x2="19" y2="19"/>',
    multipliers:{ armor:[], flesh:[], shields:[{type:'Shield',value:0.5},{type:'Proto',value:0.5}], machinery:[{type:'Robotic',value:0.5}] }},
  { id:'heat', name:'Heat', color:'#FF7043', inner:true,
    icon:'<path d="M12 22c-4 0-7-2.5-7-6.5 0-3 2-5 4-7.5 0.5-0.6 1-1.5 1.5-2.5 0.5-1 1-2 1.5-3.5 0.5 1.5 1 2.5 1.5 3.5 0.5 1 1 1.9 1.5 2.5 2 2.5 4 4.5 4 7.5 0 4-3 6.5-7 6.5z" fill="none"/><path d="M12 22c-2 0-3.5-1.3-3.5-3.5 0-1.5 1-2.5 2-4 0.5 1 1 1.7 1.5 2.5 0.5-0.8 1-1.5 1.5-2.5 1 1.5 2 2.5 2 4 0 2.2-1.5 3.5-3.5 3.5z" fill="none"/>',
    multipliers:{ armor:[], flesh:[{type:'Cloned',value:0.25},{type:'Infested',value:0.5}], shields:[], machinery:[{type:'Robotic',value:0.25}] }},
  { id:'toxin', name:'Toxin', color:'#66BB6A', inner:true,
    icon:'<path d="M12 2 L12 6" fill="none"/><path d="M12 6c-3 3-6 5-6 9a6 6 0 0 0 12 0c0-4-3-6-6-9z" fill="none"/><circle cx="9.5" cy="14" r="1.2" fill="none"/><circle cx="14" cy="16" r="0.8" fill="none"/><circle cx="11" cy="18" r="0.6" fill="none"/>',
    multipliers:{ armor:[{type:'Ferrite',value:0.25}], flesh:[{type:'Cloned',value:0.25}], shields:[], machinery:[] }},
  { id:'corrosive', name:'Corrosive', color:'#8BC34A', components:['toxin','electricity'],
    icon:'<path d="M6 4c0 0 1 4-2 8s-1 8 4 8c3 0 3-2 5-2s2 2 5 2c5 0 5-4 4-8s-2-8-2-8" fill="none"/><path d="M9 10 L8 14" fill="none"/><path d="M15 8 L13 13" fill="none"/><circle cx="11" cy="16" r="1" fill="none"/>',
    multipliers:{ armor:[{type:'Ferrite',value:0.75},{type:'Alloy',value:-0.5}], flesh:[{type:'Cloned',value:0.75},{type:'Infested',value:0.5}], shields:[{type:'Proto',value:0.5},{type:'Shield',value:-0.5}], machinery:[{type:'Robotic',value:0.75}] }},
  { id:'radiation', name:'Radiation', color:'#FFEE58', components:['heat','electricity'],
    icon:'<circle cx="12" cy="12" r="2.5" fill="none"/><path d="M12 9.5 L10 3 A9 9 0 0 1 14 3 Z" fill="none"/><path d="M14.2 13.2 L19.5 16.5 A9 9 0 0 1 16 20 Z" fill="none"/><path d="M9.8 13.2 L4.5 16.5 A9 9 0 0 1 8 20 Z" fill="none"/>',
    multipliers:{ armor:[{type:'Alloy',value:0.75}], flesh:[{type:'Infested',value:-0.5}], shields:[{type:'Shield',value:-0.25}], machinery:[{type:'Robotic',value:0.25}] }},
  { id:'viral', name:'Viral', color:'#BA68C8', components:['cold','toxin'],
    icon:'<path d="M8 3c2 3 4 3 4 6s-4 3-4 6 2 3 4 6" fill="none"/><path d="M16 3c-2 3-4 3-4 6s4 3 4 6-2 3-4 6" fill="none"/><circle cx="12" cy="6" r="1" fill="none"/><circle cx="12" cy="12" r="1" fill="none"/><circle cx="12" cy="18" r="1" fill="none"/>',
    multipliers:{ armor:[], flesh:[{type:'Cloned',value:0.75}], shields:[], machinery:[] }},
  { id:'magnetic', name:'Magnetic', color:'#42A5F5', components:['cold','electricity'],
    icon:'<path d="M7 2v10a5 5 0 0 0 10 0V2" fill="none"/><line x1="4" y1="2" x2="10" y2="2"/><line x1="14" y1="2" x2="20" y2="2"/><path d="M4 8c-2 4 0 10 8 12" fill="none" stroke-dasharray="2 2"/><path d="M20 8c2 4 0 10-8 12" fill="none" stroke-dasharray="2 2"/>',
    multipliers:{ armor:[], flesh:[], shields:[{type:'Shield',value:0.75},{type:'Proto',value:0.75}], machinery:[] }},
  { id:'gas', name:'Gas', color:'#00BFA5', components:['heat','toxin'],
    icon:'<path d="M6 18c0-3 2-4 4-5s4-2 4-5a4 4 0 0 0-8 0" fill="none"/><path d="M10 18c0-2 1.5-3 3-4s3-2 3-4" fill="none"/><path d="M5 21c1 0 2-0.5 3-0.5s2 0.5 3 0.5 2-0.5 3-0.5 2 0.5 3 0.5" fill="none"/>',
    multipliers:{ armor:[], flesh:[{type:'Infested',value:0.75}], shields:[], machinery:[] }},
  { id:'blast', name:'Blast', color:'#EF5350', components:['cold','heat'],
    icon:'<circle cx="12" cy="12" r="2" fill="none"/><line x1="12" y1="2" x2="12" y2="7"/><line x1="12" y1="17" x2="12" y2="22"/><line x1="2" y1="12" x2="7" y2="12"/><line x1="17" y1="12" x2="22" y2="12"/><line x1="5" y1="5" x2="8.5" y2="8.5"/><line x1="15.5" y1="15.5" x2="19" y2="19"/><line x1="19" y1="5" x2="15.5" y2="8.5"/><line x1="8.5" y1="15.5" x2="5" y2="19"/>',
    multipliers:{ armor:[{type:'Ferrite',value:0.25}], flesh:[], shields:[], machinery:[{type:'Robotic',value:0.75}] }}
];

var INNER_ANGLES = [-135, -45, 135, 45];
var OUTER_ANGLES = [-90, -30, 30, 90, 150, 210];

var TACTIC_TIPS = {
  cold:        'Cold damage slows enemies and reduces their attack speed. Effective against Alloy Armor and Shields.',
  electricity: 'Electricity creates a chain-lightning effect on status proc. Strong against Shields and Robotics.',
  heat:        'Heat damage ignites enemies, dealing damage over time and stripping armor. Strong against Infested flesh.',
  toxin:       'Toxin damage bypasses shields entirely, dealing damage directly to health. Effective against Ferrite Armor.',
  corrosive:   'Corrosive procs permanently strip armor — 80% on the first stack. Essential for Ferrite-armored Grineer.',
  viral:       'Viral increases all damage to health — the meta choice for high-level content paired with Slash.',
  radiation:   'Radiation causes enemies to attack each other. Strongest against Alloy Armor (Eidolons, heavy Grineer).',
  magnetic:    'Magnetic disrupts shields and energy. The go-to element for Corpus enemies and Profit-Taker shields.',
  gas:         'Gas creates a lingering toxin cloud on proc. Strongest against Infested flesh.',
  blast:       'Blast knocks down enemies. Effective against Machinery and Ferrite Armor.'
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

/* ── Multiplier cards ── */
function renderCards() {
  var container = document.getElementById('cards');
  container.innerHTML = '';
  var cats = [
    { title:'Armor',     items: selected.multipliers.armor },
    { title:'Flesh',     items: selected.multipliers.flesh },
    { title:'Shields',   items: selected.multipliers.shields },
    { title:'Machinery', items: selected.multipliers.machinery }
  ];

  cats.forEach(function(cat) {
    var card = document.createElement('div');
    card.className = 'hw-card';
    var tag = cat.items.length > 0 ? cat.items.length + ' MATCH' : 'NEUTRAL';
    var barsHTML = '';
    if (cat.items.length) {
      barsHTML = cat.items.map(function(m, i) {
        var v = Math.round(m.value * 100);
        var cls = v > 0 ? 'positive' : 'negative';
        var display = v > 0 ? '+'+v+'%' : v+'%';
        var pct = Math.abs(v);
        return '<div class="bar-row" data-name="'+m.type+'" data-display="'+display+'" data-cls="'+cls+'" style="--delay:'+(0.1+i*0.08)+'s;--glow-delay:'+(0.45+i*0.08)+'s">' +
          '<div class="bar-label-row"><span class="bar-name">'+m.type+'</span>' +
          '<span class="bar-value '+cls+'" style="animation:fadeIn 0.3s '+(0.15+i*0.08)+'s both">'+display+'</span></div>' +
          '<div class="bar-track"><div class="bar-fill '+cls+'" data-width="'+pct+'"></div>' +
          '<div class="bar-glow '+cls+'" data-pct="'+pct+'" data-dir="'+cls+'"></div></div></div>';
      }).join('');
    } else {
      barsHTML = '<div class="bar-empty">NO MODIFIER</div>';
    }
    card.innerHTML =
      '<div class="hw-card-header"><div class="hw-card-title">'+cat.title+'</div><div class="hw-card-tag">'+tag+'</div></div>' +
      '<div class="bar-list">'+barsHTML+'</div><div class="hw-card-footer"></div>';
    container.appendChild(card);

    // Animate bars
    requestAnimationFrame(function() {
      card.querySelectorAll('.bar-fill').forEach(function(bar) {
        var w = bar.dataset.width;
        var d = parseFloat(bar.closest('.bar-row').style.getPropertyValue('--delay')) * 1000;
        setTimeout(function() { bar.style.width = w + '%'; }, d);
      });
      card.querySelectorAll('.bar-glow').forEach(function(glow) {
        var pct = glow.dataset.pct;
        var dir = glow.dataset.dir;
        var d = parseFloat(glow.closest('.bar-row').style.getPropertyValue('--glow-delay')) * 1000;
        setTimeout(function() {
          glow.style.opacity = '1';
          if (dir === 'positive') { glow.style.left = pct+'%'; glow.style.transform = 'translateX(-100%)'; }
          else { glow.style.right = pct+'%'; glow.style.transform = 'translateX(100%)'; }
        }, d);
      });
    });

    // Tooltips
    card.querySelectorAll('.bar-row').forEach(function(row) {
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
