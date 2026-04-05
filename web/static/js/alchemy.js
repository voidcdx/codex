/* alchemy.js — Void Codex Alchemy page */
/* global toggleDrawer, openGuide */

/* ── Element data ── */
var ELEMENTS = [
  { id:'cold', name:'Cold', color:'#4FC3F7', inner:true,
    icon:'<polygon points="12,2 20.66,7 20.66,17 12,22 3.34,17 3.34,7"/><line x1="12" y1="2" x2="12" y2="22"/><line x1="3.34" y1="7" x2="20.66" y2="17"/><line x1="3.34" y1="17" x2="20.66" y2="7"/>',
    multipliers:{ armor:[{type:'Alloy',value:0.25}], flesh:[{type:'Infested',value:0.25}], shields:[{type:'Shield',value:0.5}], machinery:[] }},
  { id:'electricity', name:'Electricity', color:'#FFEB3B', inner:true,
    icon:'<circle cx="12" cy="12" r="10" fill="none"/><polyline points="13,2 10,10 15,10 11,22"/>',
    multipliers:{ armor:[], flesh:[], shields:[{type:'Shield',value:0.5},{type:'Proto',value:0.5}], machinery:[{type:'Robotic',value:0.5}] }},
  { id:'heat', name:'Heat', color:'#FF7043', inner:true,
    icon:'<circle cx="12" cy="12" r="2"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>',
    multipliers:{ armor:[], flesh:[{type:'Cloned',value:0.25},{type:'Infested',value:0.5}], shields:[], machinery:[{type:'Robotic',value:0.25}] }},
  { id:'toxin', name:'Toxin', color:'#66BB6A', inner:true,
    icon:'<path d="M12 2c-4 5.5-8 9-8 13a8 8 0 1 0 16 0c0-4-4-7.5-8-13" fill="none"/><path d="M9 12c1.5-1.5 4.5-1.5 6 0" fill="none"/><path d="M9 16c1.5 1.5 4.5 1.5 6 0" fill="none"/>',
    multipliers:{ armor:[{type:'Ferrite',value:0.25}], flesh:[{type:'Cloned',value:0.25}], shields:[], machinery:[] }},
  { id:'corrosive', name:'Corrosive', color:'#8BC34A', components:['toxin','electricity'],
    icon:'<path d="M12 3a9 9 0 0 1 7.79 4.5" fill="none"/><path d="M21 12a9 9 0 0 1-4.5 7.79" fill="none"/><path d="M12 21a9 9 0 0 1-7.79-4.5" fill="none"/><path d="M3 12a9 9 0 0 1 4.5-7.79" fill="none"/><circle cx="12" cy="12" r="3" fill="none"/>',
    multipliers:{ armor:[{type:'Ferrite',value:0.75},{type:'Alloy',value:-0.5}], flesh:[{type:'Cloned',value:0.75},{type:'Infested',value:0.5}], shields:[{type:'Proto',value:0.5},{type:'Shield',value:-0.5}], machinery:[{type:'Robotic',value:0.75}] }},
  { id:'radiation', name:'Radiation', color:'#FFEE58', components:['heat','electricity'],
    icon:'<circle cx="12" cy="12" r="2"/><path d="M12 2a7 7 0 0 1 5 2.05" fill="none"/><path d="M20.66 8A7 7 0 0 1 21 13" fill="none"/><path d="M17 19.95A7 7 0 0 1 12 22" fill="none"/><path d="M7 19.95A7 7 0 0 1 3 13" fill="none"/><path d="M3.34 8A7 7 0 0 1 7 4.05" fill="none"/>',
    multipliers:{ armor:[{type:'Alloy',value:0.75}], flesh:[{type:'Infested',value:-0.5}], shields:[{type:'Shield',value:-0.25}], machinery:[{type:'Robotic',value:0.25}] }},
  { id:'viral', name:'Viral', color:'#BA68C8', components:['cold','toxin'],
    icon:'<circle cx="9" cy="12" r="5" fill="none"/><circle cx="15" cy="12" r="5" fill="none"/><line x1="12" y1="7" x2="12" y2="17"/>',
    multipliers:{ armor:[], flesh:[{type:'Cloned',value:0.75}], shields:[], machinery:[] }},
  { id:'magnetic', name:'Magnetic', color:'#42A5F5', components:['cold','electricity'],
    icon:'<line x1="6" y1="4" x2="6" y2="20"/><line x1="18" y1="4" x2="18" y2="20"/><path d="M6 7c4 0 4 5 12 5" fill="none"/><path d="M6 17c4 0 4-5 12-5" fill="none"/><line x1="6" y1="12" x2="18" y2="12"/>',
    multipliers:{ armor:[], flesh:[], shields:[{type:'Shield',value:0.75},{type:'Proto',value:0.75}], machinery:[] }},
  { id:'gas', name:'Gas', color:'#00BFA5', components:['heat','toxin'],
    icon:'<circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="4" r="1"/><circle cx="18.93" cy="7" r="1"/><circle cx="20" cy="13" r="1"/><circle cx="16" cy="19" r="1"/><circle cx="8" cy="19" r="1"/><circle cx="4" cy="13" r="1"/><circle cx="5.07" cy="7" r="1"/>',
    multipliers:{ armor:[], flesh:[{type:'Infested',value:0.75}], shields:[], machinery:[] }},
  { id:'blast', name:'Blast', color:'#EF5350', components:['cold','heat'],
    icon:'<circle cx="12" cy="12" r="2"/><path d="M7 12a5 5 0 0 1 2.5-4.33" fill="none"/><path d="M14.5 7.67A5 5 0 0 1 17 12" fill="none"/><path d="M14.5 16.33A5 5 0 0 1 7 12" fill="none"/><path d="M4 12a8 8 0 0 1 4-6.93" fill="none"/><path d="M16 5.07A8 8 0 0 1 20 12" fill="none"/><path d="M16 18.93A8 8 0 0 1 4 12" fill="none"/>',
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
