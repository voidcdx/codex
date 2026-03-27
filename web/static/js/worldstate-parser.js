/**
 * worldstate-parser.js
 * Client-side translation of scripts/parse_worldstate.py.
 * parseWorldState(raw, solnodeMap?) → structured worldstate object.
 */
'use strict';

const FISSURE_TIERS = {
  VoidT1: 'Lith', VoidT2: 'Meso', VoidT3: 'Neo',
  VoidT4: 'Axi',  VoidT5: 'Requiem', VoidT6: 'Omnia',
};

const MISSION_TYPES = {
  Assassination:          'Assassination',
  Assault:                'Assault',
  Capture:                'Capture',
  Defense:                'Defense',
  Disruption:             'Disruption',
  Excavation:             'Excavation',
  Exterminate:            'Exterminate',
  Hive:                   'Hive',
  Hijack:                 'Hijack',
  Infested:               'Infested Salvage',
  InfestedSalvage:        'Infested Salvage',
  Interception:           'Interception',
  Junction:               'Junction',
  MobileDefense:          'Mobile Defense',
  Pursuit:                'Pursuit',
  Rescue:                 'Rescue',
  Sabotage:               'Sabotage',
  Spy:                    'Spy',
  Survival:               'Survival',
  LongSurvival:           'Endurance',
  RailjackAerial:         'Skirmish',
  RailjackMission:        'Railjack',
  VoidCascade:            'Void Cascade',
  VoidFlood:              'Void Flood',
  VoidArmageddon:         'Void Armageddon',
  GasCity:                'Gas City',
  ArchwingAssassination:  'Archwing Assassination',
};

const FACTION_NAMES = {
  FC_GRINEER:     'Grineer',
  FC_CORPUS:      'Corpus',
  FC_INFESTATION: 'Infested',
  FC_OROKIN:      'Orokin',
  FC_TENNO:       'Tenno',
  FC_MURMUR:      'Murmur',
  FC_NARMER:      'Narmer',
  FC_CORRUPTED:   'Corrupted',
  FC_SCALDRA:     'Scaldra',
  FC_TECHROT:     'Techrot',
};

// ── Date helpers ─────────────────────────────────────────────────────────────

function parseDate(val) {
  if (val == null) return null;
  if (typeof val === 'number') {
    // Assume seconds if < 1e11, else milliseconds
    return new Date(val > 1e11 ? val : val * 1000);
  }
  if (typeof val === 'object') {
    const inner = val['$date'];
    if (inner == null) return null;
    if (typeof inner === 'object') {
      const ms = parseInt(inner['$numberLong'] || 0, 10);
      return new Date(ms);
    }
    if (typeof inner === 'number') return new Date(inner);
  }
  return null;
}

function eta(expiry) {
  if (!expiry) return '?';
  const total = Math.floor((expiry.getTime() - Date.now()) / 1000);
  if (total <= 0) return 'Expired';
  const days  = Math.floor(total / 86400);
  const rem   = total % 86400;
  const hours = Math.floor(rem / 3600);
  const mins  = Math.floor((rem % 3600) / 60);
  if (days)  return `${days}d ${hours}h`;
  if (hours) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

// ── Lookup helpers ────────────────────────────────────────────────────────────

function nodeDisplay(nodeKey, solnodeMap) {
  if (!nodeKey) return '';
  const key = nodeKey.includes('/')
    ? nodeKey.replace(/\/$/, '').split('/').pop()
    : nodeKey;
  const info = (solnodeMap && (solnodeMap[key] || solnodeMap[nodeKey])) || {};
  const name   = info.name   || '';
  const planet = info.planet || '';
  if (name && planet) return `${name} (${planet})`;
  if (name) return name;
  // Fallback: split CamelCase planet prefix
  const m = key.match(/^([A-Z][a-z]+)(.+)/);
  if (m) {
    const mission = m[2].replace(/([A-Z])/g, ' $1').trim();
    return `${mission} (${m[1]})`;
  }
  return key;
}

function missionType(typeKey) {
  if (!typeKey) return '';
  const suffix = typeKey.includes('/')
    ? typeKey.replace(/\/$/, '').split('/').pop()
    : typeKey;
  return MISSION_TYPES[suffix] || suffix;
}

function faction(factionKey) {
  return FACTION_NAMES[factionKey] || factionKey;
}

function fmtCredits(n) {
  return String(Math.floor(n || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// ── Section parsers ───────────────────────────────────────────────────────────

function parseFissures(raw, solnodeMap) {
  const now = Date.now();
  const TIER_ORDER = { Lith: 0, Meso: 1, Neo: 2, Axi: 3, Requiem: 4, Omnia: 5 };
  const out = [];
  for (const f of raw) {
    const expiry = parseDate(f.Expiry);
    if (expiry && expiry.getTime() < now) continue;
    const modifier = f.Modifier || '';
    const tier     = FISSURE_TIERS[modifier] || modifier;
    const mKey     = f.MissionType || '';
    const isStorm  = /VoidStorm|VoidArmageddon|VoidCascade|VoidFlood/.test(mKey);
    out.push({
      node:           nodeDisplay(f.Node || '', solnodeMap),
      mission_type:   missionType(mKey),
      enemy:          faction(f.Faction || ''),
      tier,
      eta:            eta(expiry),
      is_storm:       isStorm,
      is_steel_path:  f.Hard === true,
    });
  }
  out.sort((a, b) => (TIER_ORDER[a.tier] ?? 99) - (TIER_ORDER[b.tier] ?? 99));
  return out;
}

function parseAlerts(raw, solnodeMap) {
  const now = Date.now();
  const out = [];
  for (const a of raw) {
    const expiry = parseDate(a.Expiry);
    if (expiry && expiry.getTime() < now) continue;
    const mission = a.MissionInfo || {};
    const reward  = mission.missionReward || {};
    const counted = reward.countedItems || [];
    const items   = reward.items || [];
    const credits = reward.credits || 0;
    const parts   = [];
    for (const ci of counted) {
      const ct = ci.ItemCount || 1;
      const nm = (ci.ItemType || '').replace(/\/$/, '').split('/').pop();
      parts.push(ct > 1 ? `${ct}× ${nm}` : nm);
    }
    for (const it of items) {
      parts.push(String(it).replace(/\/$/, '').split('/').pop());
    }
    if (credits) parts.push(`${fmtCredits(credits)} Credits`);
    out.push({
      node:         nodeDisplay(mission.location || '', solnodeMap),
      mission_type: missionType(mission.missionType || ''),
      faction:      faction(mission.faction || ''),
      reward:       parts.join(', ') || 'Unknown',
      eta:          eta(expiry),
    });
  }
  return out;
}

function parseSortie(raw, solnodeMap) {
  if (!raw || !raw.length) return null;
  const s       = raw[0];
  const expiry  = parseDate(s.Expiry);
  const variants = s.Variants || [];
  const missions = variants.map(v => ({
    node:         nodeDisplay(v.node || '', solnodeMap),
    mission_type: missionType(v.missionType || ''),
    modifier:     v.modifierType || '',
  }));
  const bossPath = s.Boss || '';
  const boss     = bossPath.replace(/\/$/, '').split('/').pop().replace('Boss', '').trim();
  return {
    boss:     boss || 'Unknown',
    faction:  faction(s.Faction || ''),
    eta:      eta(expiry),
    missions,
  };
}

function parseArchonHunt(raw, solnodeMap) {
  if (!raw || !raw.length) return null;
  for (const entry of raw) {
    if (!entry.Boss) continue;
    const expiry   = parseDate(entry.Expiry);
    const variants = entry.Variants || [];
    const missions = variants.map(v => ({
      node:         nodeDisplay(v.node || '', solnodeMap),
      mission_type: missionType(v.missionType || ''),
      modifier:     v.modifierType || '',
    }));
    const bossPath = entry.Boss || '';
    const boss     = bossPath.replace(/\/$/, '').split('/').pop();
    return {
      boss,
      faction:  faction(entry.Faction || ''),
      eta:      eta(expiry),
      missions,
    };
  }
  return null;
}

function parseVoidTrader(raw, solnodeMap) {
  if (!raw || !raw.length) {
    return { active: false, eta: 'Unknown', node: '', inventory: [] };
  }
  const trader     = raw[0];
  const activation = parseDate(trader.Activation);
  const expiry     = parseDate(trader.Expiry);
  const now        = Date.now();
  const active     = activation && activation.getTime() <= now &&
                     (!expiry || expiry.getTime() > now);
  const inventory  = (trader.Manifest || []).map(item => {
    const itemName = (item.ItemType || '').replace(/\/$/, '').split('/').pop();
    return {
      item:    itemName,
      ducats:  item.PrimePrice  || 0,
      credits: item.RegularPrice || 0,
    };
  });
  return {
    active,
    node:      nodeDisplay(trader.Node || '', solnodeMap),
    eta:       eta(active ? expiry : activation),
    arrives:   activation ? activation.toISOString() : null,
    departs:   expiry     ? expiry.toISOString()     : null,
    inventory,
  };
}

function parseNightwave(raw) {
  const nw = (raw || []).find(s => (s.Tag || '').includes('RadioLegion'));
  if (!nw) return null;
  const expiry     = parseDate(nw.Expiry);
  const challenges = (nw.ActiveChallenges || []).map(ch => {
    const chExpiry = parseDate(ch.Expiry);
    const info     = ch.Challenge || '';
    const title    = info.includes('/') ? info.replace(/\/$/, '').split('/').pop() : info;
    return {
      title,
      reputation: ch.xpAmount  || 0,
      is_daily:   ch.isDaily   || false,
      is_elite:   ch.isElite   || false,
      eta:        eta(chExpiry),
    };
  });
  return {
    season:            nw.Season || 0,
    phase:             nw.Phase  || 0,
    eta:               eta(expiry),
    active_challenges: challenges,
  };
}

function parseCycles(raw) {
  const cycles = [];
  const nowMs  = Date.now();
  const nowS   = Math.floor(nowMs / 1000);

  // Cetus — computed from known epoch (community-derived constants)
  try {
    const DAY_S   = 6000, NIGHT_S = 3000, CYCLE_S = 9000;
    const EPOCH_S = 1509785490;
    const elapsed = (nowS - EPOCH_S) % CYCLE_S;
    const isDay   = elapsed < DAY_S;
    const secsLeft = isDay ? (DAY_S - elapsed) : (CYCLE_S - elapsed);
    cycles.push({
      location: 'Cetus',
      state:    isDay ? 'Day' : 'Night',
      eta:      eta(new Date(nowMs + secsLeft * 1000)),
    });
  } catch (_) { /* ignore */ }

  // Orb Vallis
  const vallis = raw.VallisCycle;
  if (vallis && typeof vallis === 'object') {
    const expiry   = parseDate(vallis.expiry || vallis.Expiry);
    const rawState = vallis.state ?? vallis.isDay ?? 'cold';
    const isWarm   = rawState === true || ['warm', 'true', 'day'].includes(String(rawState).toLowerCase());
    cycles.push({ location: 'Orb Vallis', state: isWarm ? 'Warm' : 'Cold', eta: eta(expiry) });
  }

  // Cambion Drift
  const cambion = raw.CambionCycle;
  if (cambion && typeof cambion === 'object') {
    const expiry = parseDate(cambion.expiry || cambion.Expiry);
    const active = String(cambion.active || cambion.state || '').toLowerCase();
    const isFass = active === 'fass' || cambion.isDay === true;
    cycles.push({ location: 'Cambion Drift', state: isFass ? 'Fass' : 'Vome', eta: eta(expiry) });
  }

  // Zariman Ten Zero
  const zariman = raw.ZarimanCycle;
  if (zariman && typeof zariman === 'object') {
    const expiry   = parseDate(zariman.expiry || zariman.Expiry);
    const rawState = zariman.state ?? zariman.isDay ?? 'grineer';
    const isCorpus = rawState === true || ['corpus', 'true', 'day'].includes(String(rawState).toLowerCase());
    cycles.push({ location: 'Zariman Ten Zero', state: isCorpus ? 'Corpus' : 'Grineer', eta: eta(expiry) });
  }

  return cycles;
}

function parseEvents(raw) {
  const now = Date.now();
  const out = [];
  for (const ev of (raw.Events || [])) {
    try {
      const expiry = parseDate(ev.Expiry);
      if (expiry && expiry.getTime() < now) continue;

      let name = '';
      const desc = ev.Description;
      if (desc) name = typeof desc === 'object' ? (desc.value || '') : String(desc);
      if (!name) {
        const msgs = ev.Messages || [];
        if (msgs.length && typeof msgs[0] === 'object') name = msgs[0].message || '';
      }
      if (!name) name = ev.Tag || '';
      if (!name) continue;

      let reward = '';
      const rewards = ev.Rewards || [];
      if (rewards.length && typeof rewards[0] === 'object') {
        const r      = rewards[0];
        const items  = r.items || r.Items || [];
        const cr     = r.credits || r.Credits || 0;
        if (items.length) {
          const first = items[0];
          reward = typeof first === 'string'
            ? first
            : (first.ItemType || '').replace(/\/$/, '').split('/').pop();
        } else if (cr) {
          reward = `${fmtCredits(cr)} Credits`;
        }
      }

      out.push({
        name:   name.slice(0, 60),
        eta:    eta(expiry),
        reward: reward.slice(0, 50),
      });
    } catch (_) { /* skip malformed */ }
    if (out.length >= 10) break;
  }
  return out;
}

function parseInvasions(raw, solnodeMap) {
  const out = [];
  for (const inv of (raw || [])) {
    if (inv.Completed) continue;
    const expiry   = parseDate(inv.Expiry);
    const attacker = inv.AttackerInfo || {};
    const defender = inv.DefenderInfo || {};

    function reward(side) {
      const r       = (side.MissionInfo || {}).missionReward || {};
      const counted = r.countedItems || [];
      const items   = r.items || [];
      const parts   = [];
      for (const ci of counted) {
        const ct = ci.ItemCount || 1;
        const nm = (ci.ItemType || '').replace(/\/$/, '').split('/').pop();
        parts.push(ct > 1 ? `${ct}× ${nm}` : nm);
      }
      for (const it of items) {
        parts.push(String(it).replace(/\/$/, '').split('/').pop());
      }
      const cr = r.credits || 0;
      if (cr) parts.push(`${fmtCredits(cr)} cr`);
      return parts.join(', ') || 'Unknown';
    }

    const count    = inv.Count    || 0;
    const required = inv.Goal     || 1;
    const progress = Math.min(100, Math.max(0, Math.abs(count) / Math.max(required, 1) * 100));

    out.push({
      node:             nodeDisplay(inv.Node || '', solnodeMap),
      attacker:         faction(attacker.faction || ''),
      defender:         faction(defender.faction || ''),
      attacker_reward:  reward(attacker),
      defender_reward:  reward(defender),
      progress:         Math.round(progress * 10) / 10,
      eta:              eta(expiry),
      vs_infestation:   attacker.faction === 'FC_INFESTATION' || defender.faction === 'FC_INFESTATION',
    });
  }
  return out;
}

// ── Main export ───────────────────────────────────────────────────────────────

export function parseWorldState(raw, solnodeMap = {}) {
  return {
    fissures:    parseFissures(raw.ActiveMissions || [], solnodeMap),
    alerts:      parseAlerts(raw.Alerts || [], solnodeMap),
    sortie:      parseSortie(raw.Sorties || [], solnodeMap),
    archon_hunt: parseArchonHunt(raw.LevelOverrides || raw.Goals || [], solnodeMap),
    void_trader: parseVoidTrader(raw.VoidTraders || [], solnodeMap),
    nightwave:   parseNightwave(raw.SyndicateMissions || []),
    invasions:   parseInvasions(raw.Invasions || [], solnodeMap),
    cycles:      parseCycles(raw),
    events:      parseEvents(raw),
  };
}
