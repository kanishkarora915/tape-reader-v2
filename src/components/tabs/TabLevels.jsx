import React, { useMemo } from 'react';

const COLORS = {
  bg: '#0a0a0a',
  panel: '#0f0f0f',
  border: '#1f1f1f',
  amber: '#FFB300',
  amberDim: '#7A5600',
  white: '#E8E8E8',
  green: '#00C853',
  red: '#FF3D00',
  blue: '#2196F3',
  gray: '#444444',
  hover: '#161616',
};

const font = { fontFamily: '"IBM Plex Mono", monospace' };

function safe(val) {
  return val != null && val !== '' && val !== undefined;
}

function fmt(n) {
  if (!safe(n)) return '—';
  const num = Number(n);
  return isNaN(num) ? '—' : num.toLocaleString('en-IN', { maximumFractionDigits: 1 });
}

function chgColor(v) {
  if (!safe(v)) return COLORS.gray;
  return Number(v) >= 0 ? COLORS.green : COLORS.red;
}

function chgPrefix(v) {
  if (!safe(v)) return '';
  return Number(v) >= 0 ? '+' : '';
}

export default function TabLevels({ engines, tick }) {
  const niftyLtp = tick?.nifty?.ltp;
  const e05 = engines?.e05?.data;
  const e06 = engines?.e06?.data;
  const e08 = engines?.e08?.data;
  const e10 = engines?.e10?.data;
  const e11 = engines?.e11?.data;
  const e23 = engines?.e23?.data;

  const hasData = safe(niftyLtp);

  const levels = useMemo(() => {
    if (!hasData) return [];
    const ltp = Number(niftyLtp);
    const atm = Math.round(ltp / 50) * 50;
    const rows = [
      { label: 'R3', price: ltp + 300, type: 'Pivot Resistance', color: COLORS.gray },
      { label: 'R2', price: ltp + 200, type: 'Pivot Resistance', color: COLORS.gray },
      { label: 'R1', price: ltp + 100, type: 'Pivot Resistance', color: COLORS.green },
      { label: 'CALL WALL', price: e05?.call_wall, type: 'GEX Resistance', color: COLORS.red },
      { label: 'VWAP +2SD', price: e08?.sd2_upper, type: 'Stretch Zone', color: COLORS.gray },
      { label: 'ATM STRIKE', price: atm, type: '\u2605 CURRENT', color: COLORS.amber, highlight: true },
      { label: 'VWAP +1SD', price: e08?.sd1_upper, type: 'First Target', color: COLORS.gray },
      { label: 'DAILY VWAP', price: e08?.d_vwap, type: 'Support', color: COLORS.blue },
      { label: 'S1', price: ltp - 100, type: 'Pivot Support', color: COLORS.green },
      { label: 'PUT WALL', price: e05?.put_wall, type: 'GEX Support', color: COLORS.green },
      { label: 'MAX PAIN', price: e10?.max_pain, type: 'Expiry Gravity', color: COLORS.blue },
      { label: 'S2', price: ltp - 200, type: 'Pivot Support', color: COLORS.gray },
      { label: 'S3', price: ltp - 300, type: 'Pivot Support', color: COLORS.gray },
      { label: 'WEEKLY VWAP', price: e08?.w_vwap, type: 'Major Support', color: COLORS.blue },
    ].filter(r => safe(r.price));
    rows.sort((a, b) => Number(b.price) - Number(a.price));
    return rows;
  }, [hasData, niftyLtp, e05, e08, e10]);

  const pcr = e06?.pcr != null ? Number(e06.pcr) : null;
  const weeklyBias = pcr != null
    ? pcr > 1.1 ? { text: 'BULLISH WEEK', color: COLORS.green }
      : pcr < 0.8 ? { text: 'BEARISH WEEK', color: COLORS.red }
      : { text: 'NEUTRAL WEEK', color: COLORS.gray }
    : null;

  const oiTrend = pcr != null
    ? pcr > 1.1
      ? { text: 'PUT HEAVY = bullish bias', color: COLORS.green }
      : { text: 'CALL HEAVY = bearish bias', color: COLORS.red }
    : null;

  if (!hasData) {
    return (
      <div style={{ ...font, background: COLORS.bg, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: COLORS.gray, fontSize: 13 }}>Login with Kite to view levels</span>
      </div>
    );
  }

  return (
    <div style={{ ...font, background: COLORS.bg, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Title */}
      <div style={{ padding: '8px 12px', borderBottom: `1px solid ${COLORS.border}`, color: COLORS.amber, fontSize: 11, fontWeight: 700, letterSpacing: 1.2, textTransform: 'uppercase' }}>
        NEXT DAY &amp; WEEKLY LEVELS — NIFTY
      </div>

      {/* 3-col grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', flex: 1, minHeight: 0 }}>

        {/* COL 1: TODAY'S KEY LEVELS */}
        <div style={{ borderRight: `1px solid ${COLORS.border}`, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <div style={{ padding: '6px 10px', color: COLORS.amber, fontSize: 10, fontWeight: 700, letterSpacing: 1, borderBottom: `1px solid ${COLORS.border}` }}>
            TODAY'S KEY LEVELS
          </div>
          {/* Table header */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', padding: '4px 10px', borderBottom: `1px solid ${COLORS.border}`, color: COLORS.gray, fontSize: 10, fontWeight: 600 }}>
            <span>LEVEL</span>
            <span style={{ textAlign: 'right' }}>PRICE</span>
            <span style={{ textAlign: 'right' }}>TYPE</span>
          </div>
          {/* Rows */}
          <div style={{ flex: 1, overflow: 'auto' }}>
            {levels.map((row, i) => (
              <LevelRow key={i} row={row} />
            ))}
          </div>
        </div>

        {/* COL 2: WEEKLY OI ANALYSIS */}
        <div style={{ borderRight: `1px solid ${COLORS.border}`, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <div style={{ padding: '6px 10px', color: COLORS.amber, fontSize: 10, fontWeight: 700, letterSpacing: 1, borderBottom: `1px solid ${COLORS.border}` }}>
            WEEKLY OI ANALYSIS
          </div>
          <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <InfoRow label="WEEKLY PCR" value={safe(pcr) ? pcr.toFixed(2) : '—'} />
            <InfoRow label="MAX PAIN" value={fmt(e10?.max_pain)} />
            <InfoRow label="DAYS TO EXPIRY" value={safe(e10?.days_to_expiry) ? e10.days_to_expiry : '—'} />
            <InfoRow label="EXPIRY DRIFT" value={e10?.oi_drift_direction || '—'} valueColor={COLORS.amber} />
            <InfoRow label="EXPIRY TYPE" value={e10?.expiry_type || '—'} />
            {oiTrend && (
              <InfoRow label="OI TREND" value={oiTrend.text} valueColor={oiTrend.color} />
            )}

            {/* Weekly bias big label */}
            {weeklyBias && (
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: weeklyBias.color, letterSpacing: 1.5 }}>
                  {weeklyBias.text}
                </div>
              </div>
            )}

            {/* Interpretation */}
            <div style={{ marginTop: 8, color: COLORS.amberDim, fontSize: 10, fontStyle: 'italic', lineHeight: 1.5 }}>
              {pcr != null
                ? pcr > 1.1
                  ? 'High PCR indicates aggressive put writing by institutional players. Market makers are positioned for upside. Watch for dips to be bought near put wall and max pain levels.'
                  : pcr < 0.8
                    ? 'Low PCR signals heavy call writing pressure. Institutions expect limited upside. Rallies towards call wall likely to face resistance. Stay cautious on longs.'
                    : 'Neutral PCR zone. No strong directional bias from OI data. Market likely to remain range-bound between call wall and put wall. Trade the range.'
                : 'Awaiting OI data for weekly analysis...'}
            </div>
          </div>
        </div>

        {/* COL 3: PRE-MARKET TOMORROW */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <div style={{ padding: '6px 10px', color: COLORS.amber, fontSize: 10, fontWeight: 700, letterSpacing: 1, borderBottom: `1px solid ${COLORS.border}` }}>
            PRE-MARKET TOMORROW
          </div>
          <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <InfoRow label="GIFT NIFTY" value={safe(e23?.gift_nifty) ? fmt(e23.gift_nifty) : '—'} />
            <InfoRow label="EXPECTED GAP" value={e23?.morning_bias || '—'} />
            <InfoRow label="GAP FILL LEVEL" value={safe(e23?.gap_fill_target) ? fmt(e23.gap_fill_target) : '—'} />

            {/* Global cues */}
            {Array.isArray(e23?.global_cues) && e23.global_cues.length > 0 && (
              <div style={{ marginTop: 4 }}>
                <div style={{ color: COLORS.gray, fontSize: 10, fontWeight: 600, marginBottom: 4 }}>GLOBAL CUES</div>
                {e23.global_cues.map((cue, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0', fontSize: 11 }}>
                    <span style={{ color: COLORS.white }}>{cue.name}</span>
                    <span style={{ color: chgColor(cue.change) }}>
                      {chgPrefix(cue.change)}{safe(cue.change) ? Number(cue.change).toFixed(2) : '—'}%
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Tomorrow bias */}
            {safe(e23?.morning_bias) && (
              <div style={{ marginTop: 12, textAlign: 'center' }}>
                <div style={{ color: COLORS.gray, fontSize: 10, marginBottom: 4 }}>TOMORROW BIAS</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.amber, letterSpacing: 1 }}>
                  {e23.morning_bias}
                </div>
              </div>
            )}

            <InfoRow label="FII DIRECTION" value={e11?.fii_3day_trend || '—'} />

            {/* Prediction */}
            <div style={{ marginTop: 8, color: COLORS.amberDim, fontSize: 10, fontStyle: 'italic', lineHeight: 1.5 }}>
              {safe(e23?.morning_bias) && safe(e11?.fii_3day_trend)
                ? `Pre-market signals suggest ${(e23.morning_bias || '').toLowerCase()} opening. FII trend is ${(e11.fii_3day_trend || '').toLowerCase()}. Watch Gift Nifty and SGX levels for confirmation before 9:00 AM. Gap fills are high-probability setups in the first 30 minutes.`
                : 'Awaiting pre-market data. Global cues will update after US market close.'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* --- Sub-components --- */

function LevelRow({ row }) {
  const [hovered, setHovered] = React.useState(false);
  const bg = row.highlight
    ? '#1a1400'
    : hovered
      ? COLORS.hover
      : 'transparent';

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        padding: '3px 10px',
        fontSize: 11,
        background: bg,
        borderBottom: `1px solid ${COLORS.border}`,
        cursor: 'default',
      }}
    >
      <span style={{ color: row.color, fontWeight: 600 }}>{row.label}</span>
      <span style={{ color: COLORS.white, textAlign: 'right' }}>{fmt(row.price)}</span>
      <span style={{ color: row.color, textAlign: 'right', fontSize: 10 }}>{row.type}</span>
    </div>
  );
}

function InfoRow({ label, value, valueColor }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11 }}>
      <span style={{ color: COLORS.gray }}>{label}</span>
      <span style={{ color: valueColor || COLORS.white, fontWeight: 600 }}>{value}</span>
    </div>
  );
}
