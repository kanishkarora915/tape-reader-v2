import React from 'react';

const TIER_NAMES = { 1: 'CORE GATE', 2: 'DIRECTION', 3: 'AMPLIFIER', 4: 'BIG MOVE' };

const ENGINE_ORDER = [
  'e01','e02','e03','e04','e05','e06','e07','e08',
  'e09','e10','e11','e12','e13','e14','e15','e16',
  'e17','e18','e19','e20','e21','e22','e23','e24'
];

function getValueLine(key, data) {
  if (!data) return 'No data';
  switch (key) {
    case 'e01': return data.writer_signal || 'Monitoring OI...';
    case 'e02': return `IVR: ${data.ivr ?? '—'}/100`;
    case 'e03': return data.regime || 'Analyzing...';
    case 'e04': return `${data.total_score ?? '—'}/${data.max_score ?? '—'} consensus`;
    case 'e05': return data.total_gex != null ? `GEX ${data.total_gex > 0 ? '+' : ''}${data.total_gex.toFixed(0)}` : 'Computing...';
    case 'e06': return `PCR ${data.pcr || '—'}`;
    case 'e07': return data.traps?.length ? `${data.traps.length} trap(s)` : 'No traps';
    case 'e08': return data.position || 'Computing VWAP...';
    case 'e09': return data.summary || 'Computing...';
    case 'e10': return `MP: ${data.max_pain || '—'}`;
    case 'e11': return data.fii_3day_trend || 'Fetching FII data...';
    case 'e12': return data.bb_squeeze || 'Normal';
    case 'e13': return data.ignition_detected ? 'Ignition FIRED' : 'Monitoring...';
    case 'e14': return `Delta: ${data.delta_shift || 0}`;
    case 'e15': return data.stretched ? 'STRETCHED' : 'Normal range';
    case 'e16': return data.aligned ? 'ALIGNED' : 'Not aligned';
    case 'e17': return `USD/INR ${data.usdinr || '—'}`;
    case 'e18': return `${data.win_rate || 0}% over ${data.similar_setups || 0} setups`;
    case 'e19': return data.active ? 'UOA detected' : 'Monitoring...';
    case 'e20': return `Velocity: ${data.max_velocity || 0}`;
    case 'e21': return data.active ? 'Divergence found' : 'Monitoring...';
    case 'e22': return `Imbalance: ${data.imbalance_ratio || 50}%`;
    case 'e23': return data.morning_bias || 'Pre-market pending';
    case 'e24': return data.rationale ? 'Analysis ready' : 'Waiting for signal...';
    default: return '—';
  }
}

function getSignalLine(key, eng) {
  const { direction, verdict, tier, data } = eng;

  // Special cases first
  if (key === 'e04' && data) {
    return <span style={{ color: '#FFB300' }}>SCORE: {data.total_score ?? 0}/{data.max_score ?? 0}</span>;
  }
  if (key === 'e02' && data) {
    const gs = data.gate_status;
    const gateColor = gs === 'OPEN' ? '#00C853' : gs === 'PARTIAL' ? '#FFB300' : '#FF3D00';
    return <span style={{ color: gateColor }}>GATE {gs || '—'}</span>;
  }
  if (key === 'e12' && data?.bb_squeeze) {
    return <span style={{ color: '#FFB300' }}>SQUEEZE</span>;
  }
  if (key === 'e18' && data) {
    const wr = data.win_rate || 0;
    return <span style={{ color: wr > 60 ? '#00C853' : '#FFB300' }}>{wr}% WIN</span>;
  }
  if (tier === 4 && verdict === 'PASS') {
    return <span style={{ color: '#2196F3' }}>ALERT &#9733;</span>;
  }

  // Direction-based
  if (direction === 'BULLISH') return <span style={{ color: '#00C853' }}>+1 CALL</span>;
  if (direction === 'BEARISH') return <span style={{ color: '#FF3D00' }}>+1 PUT</span>;
  return <span style={{ color: '#444444' }}>NEUTRAL</span>;
}

function EngineCard({ engineKey, eng }) {
  const { name, tier, verdict, data } = eng;
  const idx = engineKey.toUpperCase();
  const isActive = verdict === 'PASS' || verdict === 'PARTIAL';
  const isT1Fail = tier === 1 && verdict === 'FAIL';
  const isT4Active = tier === 4 && verdict === 'PASS';
  const dimmed = !isActive && tier !== 1;

  let borderColor = '#1f1f1f';
  if (isT4Active) borderColor = '#2196F3';
  if (isT1Fail) borderColor = '#FF3D00';

  return (
    <div
      style={{
        border: `1px solid ${borderColor}`,
        padding: '10px 12px',
        background: '#0f0f0f',
        fontFamily: "'IBM Plex Mono', monospace",
        opacity: dimmed ? 0.5 : 1,
        borderRadius: 0,
      }}
    >
      {/* Line 1: ID + Name */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ color: '#444444', fontSize: 10 }}>[{idx}]</span>
        <span style={{ color: '#FFB300', fontWeight: 700, fontSize: 12 }}>{name}</span>
      </div>

      {/* Line 2: Tier */}
      <div style={{ marginTop: 4, fontSize: 10 }}>
        <span
          style={{
            display: 'inline-block',
            padding: '1px 6px',
            fontSize: 10,
            fontFamily: "'IBM Plex Mono', monospace",
            color: '#E8E8E8',
            borderRadius: 0,
            background:
              tier === 1 ? '#7A5600' :
              tier === 2 ? '#1a3a1a' :
              tier === 3 ? '#1a1a3a' :
              '#0d2948',
          }}
        >
          TIER: {tier} — {TIER_NAMES[tier] || 'UNKNOWN'}
        </span>
      </div>

      {/* Line 3: Status */}
      <div style={{ marginTop: 4, fontSize: 11 }}>
        <span style={{ color: '#444444' }}>STATUS: </span>
        <span style={{ color: isActive ? '#00C853' : '#444444' }}>
          {isActive ? 'ACTIVE' : 'INACTIVE'}
        </span>
      </div>

      {/* Line 4: Signal */}
      <div style={{ marginTop: 3, fontSize: 11 }}>
        {getSignalLine(engineKey, eng)}
      </div>

      {/* Line 5: Value */}
      <div style={{ marginTop: 3, fontSize: 10 }}>
        <span style={{ color: '#444444' }}>VALUE: </span>
        <span style={{ color: '#E8E8E8' }}>{getValueLine(engineKey, data || {})}</span>
      </div>
    </div>
  );
}

export default function TabEngines({ engines }) {
  if (!engines || Object.keys(engines).length === 0) {
    return (
      <div style={{
        fontFamily: "'IBM Plex Mono', monospace",
        color: '#444444',
        fontSize: 12,
        padding: 24,
        background: '#0a0a0a',
      }}>
        Waiting for engine data...
      </div>
    );
  }

  let active = 0, calls = 0, puts = 0, neutral = 0, t4alerts = 0;
  ENGINE_ORDER.forEach(k => {
    const eng = engines[k];
    if (!eng) return;
    const isActive = eng.verdict === 'PASS' || eng.verdict === 'PARTIAL';
    if (isActive) active++;
    if (eng.direction === 'BULLISH') calls++;
    else if (eng.direction === 'BEARISH') puts++;
    else neutral++;
    if (eng.tier === 4 && eng.verdict === 'PASS') t4alerts++;
  });

  return (
    <div style={{
      fontFamily: "'IBM Plex Mono', monospace",
      background: '#0a0a0a',
      padding: 0,
    }}>
      {/* Title */}
      <div style={{
        color: '#FFB300',
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: 1,
        padding: '10px 12px',
        borderBottom: '1px solid #1f1f1f',
        background: '#0f0f0f',
      }}>
        ALL 24 ENGINES — LIVE STATUS
      </div>

      {/* Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 1,
        background: '#1f1f1f',
      }}>
        {ENGINE_ORDER.map(k => {
          const eng = engines[k];
          if (!eng) return (
            <div key={k} style={{
              background: '#0f0f0f',
              padding: '10px 12px',
              fontSize: 10,
              color: '#444444',
              fontFamily: "'IBM Plex Mono', monospace",
            }}>
              [{k.toUpperCase()}] No data
            </div>
          );
          return <EngineCard key={k} engineKey={k} eng={eng} />;
        })}
      </div>

      {/* Summary row */}
      <div style={{
        marginTop: 2,
        fontSize: 11,
        color: '#FFB300',
        fontFamily: "'IBM Plex Mono', monospace",
        padding: '8px 12px',
        background: '#0f0f0f',
        borderTop: '1px solid #1f1f1f',
      }}>
        ACTIVE ENGINES: {active}/24 | CALL VOTES: {calls} | PUT VOTES: {puts} | NEUTRAL: {neutral} | BIG MOVE ALERTS: {t4alerts}
      </div>
    </div>
  );
}
