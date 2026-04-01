import React, { useMemo, useState } from 'react';

function safe(val) {
  return val != null && val !== '' && val !== undefined;
}

function fmt(n) {
  if (!safe(n)) return '\u2014';
  const num = Number(n);
  return isNaN(num) ? '\u2014' : num.toLocaleString('en-IN', { maximumFractionDigits: 1 });
}

function chgColor(v) {
  if (!safe(v)) return '#444';
  return Number(v) >= 0 ? '#00C853' : '#FF3D00';
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
      { label: 'R3', price: ltp + 300, type: 'Pivot Resistance', color: '#444' },
      { label: 'R2', price: ltp + 200, type: 'Pivot Resistance', color: '#444' },
      { label: 'R1', price: ltp + 100, type: 'Pivot Resistance', color: '#00C853' },
      { label: 'CALL WALL', price: e05?.call_wall, type: 'GEX Resistance', color: '#FF3D00' },
      { label: 'VWAP +2SD', price: e08?.sd2_upper, type: 'Stretch Zone', color: '#444' },
      { label: 'ATM STRIKE', price: atm, type: '\u2605 CURRENT', color: '#FFB300', highlight: true },
      { label: 'VWAP +1SD', price: e08?.sd1_upper, type: 'First Target', color: '#444' },
      { label: 'DAILY VWAP', price: e08?.d_vwap, type: 'Support', color: '#2196F3' },
      { label: 'S1', price: ltp - 100, type: 'Pivot Support', color: '#00C853' },
      { label: 'PUT WALL', price: e05?.put_wall, type: 'GEX Support', color: '#00C853' },
      { label: 'MAX PAIN', price: e10?.max_pain, type: 'Expiry Gravity', color: '#2196F3' },
      { label: 'S2', price: ltp - 200, type: 'Pivot Support', color: '#444' },
      { label: 'S3', price: ltp - 300, type: 'Pivot Support', color: '#444' },
      { label: 'WEEKLY VWAP', price: e08?.w_vwap, type: 'Major Support', color: '#2196F3' },
    ].filter(r => safe(r.price));
    rows.sort((a, b) => Number(b.price) - Number(a.price));
    return rows;
  }, [hasData, niftyLtp, e05, e08, e10]);

  const pcr = e06?.pcr != null ? Number(e06.pcr) : null;
  const weeklyBias = pcr != null
    ? pcr > 1.1 ? { text: 'BULLISH WEEK', color: '#00C853' }
      : pcr < 0.8 ? { text: 'BEARISH WEEK', color: '#FF3D00' }
      : { text: 'NEUTRAL WEEK', color: '#444' }
    : null;

  const oiTrend = pcr != null
    ? pcr > 1.1
      ? { text: 'PUT HEAVY = bullish bias', color: '#00C853' }
      : { text: 'CALL HEAVY = bearish bias', color: '#FF3D00' }
    : null;

  const sectionHeader = {
    fontSize: 10,
    color: '#FFB300',
    fontWeight: 600,
    letterSpacing: 3,
    textTransform: 'uppercase',
    borderBottom: '1px solid #1f1f1f',
    paddingBottom: 8,
    marginBottom: 12,
    fontFamily: "'IBM Plex Mono', monospace",
  };

  if (!hasData) {
    return (
      <div style={{
        fontFamily: "'IBM Plex Mono', monospace",
        background: '#0a0a0a',
        padding: '16px 20px',
        minHeight: 400,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <span style={{ color: '#333', fontSize: 13, letterSpacing: 2, fontFamily: "'IBM Plex Mono', monospace" }}>
          Login to view levels
        </span>
      </div>
    );
  }

  return (
    <div style={{
      fontFamily: "'IBM Plex Mono', monospace",
      background: '#0a0a0a',
      padding: '16px 20px',
    }}>
      {/* Title */}
      <div style={{
        color: '#FFB300',
        fontSize: 15,
        fontWeight: 700,
        letterSpacing: 4,
        textTransform: 'uppercase',
        marginBottom: 20,
        fontFamily: "'IBM Plex Mono', monospace",
      }}>
        NEXT DAY & WEEKLY LEVELS — NIFTY
      </div>

      {/* 3-column grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gap: 0,
      }}>

        {/* COL 1: TODAY'S KEY LEVELS */}
        <div style={{ borderRight: '1px solid #1f1f1f', paddingRight: 16 }}>
          <div style={sectionHeader}>TODAY'S KEY LEVELS</div>

          {/* Table header */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            padding: '4px 8px',
            borderBottom: '1px solid #1f1f1f',
            marginBottom: 2,
          }}>
            <span style={{ color: '#444', fontSize: 9, fontWeight: 600, letterSpacing: 1, fontFamily: "'IBM Plex Mono', monospace" }}>LEVEL</span>
            <span style={{ color: '#444', fontSize: 9, fontWeight: 600, letterSpacing: 1, textAlign: 'right', fontFamily: "'IBM Plex Mono', monospace" }}>PRICE</span>
            <span style={{ color: '#444', fontSize: 9, fontWeight: 600, letterSpacing: 1, textAlign: 'right', fontFamily: "'IBM Plex Mono', monospace" }}>TYPE</span>
          </div>

          {/* Rows */}
          {levels.map((row, i) => (
            <LevelRow key={i} row={row} />
          ))}
        </div>

        {/* COL 2: WEEKLY OI ANALYSIS */}
        <div style={{ borderRight: '1px solid #1f1f1f', paddingLeft: 16, paddingRight: 16 }}>
          <div style={sectionHeader}>WEEKLY OI ANALYSIS</div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <StatRow label="PCR" value={safe(pcr) ? pcr.toFixed(2) : '\u2014'} />
            <StatRow label="MAX PAIN" value={fmt(e10?.max_pain)} />
            <StatRow label="DAYS TO EXPIRY" value={safe(e10?.days_to_expiry) ? e10.days_to_expiry : '\u2014'} />
            {oiTrend && (
              <StatRow label="OI TREND" value={oiTrend.text} valueColor={oiTrend.color} />
            )}

            {/* Weekly bias big label */}
            {weeklyBias && (
              <div style={{ marginTop: 20, textAlign: 'center' }}>
                <div style={{
                  fontSize: 18,
                  fontWeight: 700,
                  color: weeklyBias.color,
                  letterSpacing: 2,
                  fontFamily: "'IBM Plex Mono', monospace",
                }}>
                  {weeklyBias.text}
                </div>
              </div>
            )}

            {/* Interpretation */}
            <div style={{
              marginTop: 12,
              color: '#7A5600',
              fontSize: 10,
              fontStyle: 'italic',
              lineHeight: 1.6,
              fontFamily: "'IBM Plex Mono', monospace",
            }}>
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
        <div style={{ paddingLeft: 16 }}>
          <div style={sectionHeader}>PRE-MARKET TOMORROW</div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <StatRow label="GIFT NIFTY" value={safe(e23?.gift_nifty) ? fmt(e23.gift_nifty) : '\u2014'} />
            <StatRow label="EXPECTED GAP" value={e23?.morning_bias || '\u2014'} />
            <StatRow label="GAP FILL" value={safe(e23?.gap_fill_target) ? fmt(e23.gap_fill_target) : '\u2014'} />

            {/* Global cues */}
            {Array.isArray(e23?.global_cues) && e23.global_cues.length > 0 && (
              <div style={{ marginTop: 8 }}>
                <div style={{ color: '#444', fontSize: 9, fontWeight: 600, letterSpacing: 2, marginBottom: 6, fontFamily: "'IBM Plex Mono', monospace" }}>
                  GLOBAL CUES
                </div>
                {e23.global_cues.map((cue, i) => (
                  <div key={i} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '3px 0',
                    fontSize: 11,
                    fontFamily: "'IBM Plex Mono', monospace",
                  }}>
                    <span style={{ color: '#E8E8E8' }}>{cue.name}</span>
                    <span style={{ color: chgColor(cue.change) }}>
                      {chgPrefix(cue.change)}{safe(cue.change) ? Number(cue.change).toFixed(2) : '\u2014'}%
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Tomorrow Bias */}
            {safe(e23?.morning_bias) && (
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <div style={{ color: '#444', fontSize: 9, letterSpacing: 2, marginBottom: 4, fontFamily: "'IBM Plex Mono', monospace" }}>
                  TOMORROW BIAS
                </div>
                <div style={{
                  fontSize: 18,
                  fontWeight: 700,
                  color: '#FFB300',
                  letterSpacing: 2,
                  fontFamily: "'IBM Plex Mono', monospace",
                }}>
                  {e23.morning_bias}
                </div>
              </div>
            )}

            <StatRow label="FII DIRECTION" value={e11?.fii_3day_trend || '\u2014'} />

            {/* Prediction */}
            <div style={{
              marginTop: 12,
              color: '#7A5600',
              fontSize: 10,
              fontStyle: 'italic',
              lineHeight: 1.6,
              fontFamily: "'IBM Plex Mono', monospace",
            }}>
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
  const [hovered, setHovered] = useState(false);
  const bg = row.highlight
    ? '#1a1400'
    : hovered
      ? '#161616'
      : 'transparent';

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        padding: '4px 8px',
        fontSize: 10,
        background: bg,
        borderBottom: '1px solid #141414',
        cursor: 'default',
        fontFamily: "'IBM Plex Mono', monospace",
      }}
    >
      <span style={{ color: row.color, fontWeight: 600 }}>{row.label}</span>
      <span style={{ color: '#E8E8E8', textAlign: 'right' }}>{fmt(row.price)}</span>
      <span style={{ color: row.color, textAlign: 'right', fontSize: 9 }}>{row.type}</span>
    </div>
  );
}

function StatRow({ label, value, valueColor }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      fontSize: 11,
      fontFamily: "'IBM Plex Mono', monospace",
    }}>
      <span style={{ color: '#444' }}>{label}</span>
      <span style={{ color: valueColor || '#E8E8E8', fontWeight: 600 }}>{value}</span>
    </div>
  );
}
