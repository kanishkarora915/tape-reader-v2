import { useMemo } from 'react'

const F = "'IBM Plex Mono', monospace"
const S = {
  root: { fontFamily: F, background: '#0a0a0a', padding: '16px 20px', minHeight: '100vh' },
  header: { fontSize: 10, color: '#FFB300', fontWeight: 600, letterSpacing: 3, textTransform: 'uppercase', borderBottom: '1px solid #1f1f1f', paddingBottom: 8, marginBottom: 16 },
  subHeader: { fontSize: 9, color: '#555', letterSpacing: 2, marginBottom: 12 },
  row: { display: 'flex', padding: '5px 0', borderBottom: '1px solid #141414', fontSize: 11, alignItems: 'center' },
  label: { color: '#555', fontSize: 10 },
  green: { color: '#00C853' },
  red: { color: '#FF3D00' },
  amber: { color: '#FFB300' },
  white: { color: '#E8E8E8' },
  dim: { color: '#444' },
}

function fmt(n) {
  if (n == null || isNaN(n)) return '—'
  const abs = Math.abs(n)
  if (abs >= 10000000) return `${(n / 10000000).toFixed(2)}Cr`
  if (abs >= 100000) return `${(n / 100000).toFixed(1)}L`
  return n.toLocaleString('en-IN')
}

function chgColor(n) { return n > 0 ? '#00C853' : n < 0 ? '#FF3D00' : '#444' }
function chgSign(n) { return n > 0 ? '+' : '' }

export default function TabUOA({ engines }) {
  const e19 = engines?.e19?.data || {}
  const oiChanges = e19.oi_changes || []
  const recentChanges = e19.recent_changes || []
  const volumeSpikes = e19.volume_spikes || []
  const sums = e19.sums || {}
  const interpretations = e19.interpretations || []
  const trade = e19.trade
  const status = e19.status || 'Waiting for data...'
  const cycle = e19.cycle || 0

  const hasData = oiChanges.length > 0 || Object.keys(sums).length > 0

  return (
    <div style={S.root}>

      {/* ── Header ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <div style={{ ...S.header, marginBottom: 4 }}>UNUSUAL OPTIONS ACTIVITY — E19</div>
          <div style={S.subHeader}>Live OI change tracker · Strike-wise CE/PE analysis · Auto-updating sums</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 10, color: sums.direction === 'BULLISH' ? '#00C853' : sums.direction === 'BEARISH' ? '#FF3D00' : '#444', fontWeight: 700, letterSpacing: 2 }}>
            {sums.direction || 'NEUTRAL'}
          </div>
          <div style={{ fontSize: 9, color: '#555' }}>Cycle #{cycle} · {status}</div>
        </div>
      </div>

      {/* ── Trade Recommendation ── */}
      {trade && typeof trade === 'object' && trade.ltp && (
        <div style={{ background: '#0f0f0f', border: `1px solid ${trade.action?.includes('CALL') ? '#00C853' : '#FF3D00'}`, padding: '16px 20px', marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: trade.action?.includes('CALL') ? '#00C853' : '#FF3D00', letterSpacing: 2 }}>
              {trade.action}
            </div>
            <div style={{ fontSize: 10, color: trade.confidence === 'HIGH' ? '#00C853' : '#FFB300', border: `1px solid ${trade.confidence === 'HIGH' ? '#00C853' : '#FFB300'}`, padding: '2px 10px', letterSpacing: 2 }}>
              {trade.confidence}
            </div>
          </div>
          <div style={{ fontSize: 14, color: '#FFB300', fontWeight: 600, marginBottom: 10 }}>{trade.instrument}</div>
          <div style={{ display: 'flex', gap: 32, fontSize: 12 }}>
            <div><span style={S.dim}>LTP </span><span style={S.white}>₹{trade.ltp}</span></div>
            <div><span style={S.dim}>ENTRY </span><span style={S.amber}>₹{trade.entry}</span></div>
            <div><span style={S.dim}>SL </span><span style={S.red}>₹{trade.sl}</span></div>
            <div><span style={S.dim}>T1 </span><span style={S.green}>₹{trade.target1}</span></div>
            <div><span style={S.dim}>T2 </span><span style={S.green}>₹{trade.target2}</span></div>
            <div><span style={S.dim}>R:R </span><span style={S.white}>{trade.rr}</span></div>
          </div>
          {trade.reason && <div style={{ marginTop: 8, fontSize: 10, color: '#7A5600', fontStyle: 'italic' }}>{trade.reason}</div>}
        </div>
      )}

      {/* ── OI Sums Dashboard ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, background: '#1f1f1f', marginBottom: 20 }}>
        {/* CE Sums */}
        <div style={{ background: '#0f0f0f', padding: 16 }}>
          <div style={{ ...S.header, fontSize: 9, marginBottom: 10 }}>CALL OI SUMMARY</div>
          <div style={S.row}>
            <span style={{ flex: 1, ...S.label }}>OI ADDED</span>
            <span style={{ ...S.green, fontWeight: 600, fontSize: 13 }}>{chgSign(sums.ce_oi_added)}{fmt(sums.ce_oi_added)}</span>
          </div>
          <div style={S.row}>
            <span style={{ flex: 1, ...S.label }}>OI REMOVED</span>
            <span style={{ ...S.red, fontWeight: 600, fontSize: 13 }}>-{fmt(sums.ce_oi_removed)}</span>
          </div>
          <div style={{ ...S.row, borderBottom: 'none', paddingTop: 8 }}>
            <span style={{ flex: 1, ...S.label, fontWeight: 700 }}>NET CE OI</span>
            <span style={{ color: chgColor(sums.ce_net), fontWeight: 700, fontSize: 15 }}>{chgSign(sums.ce_net)}{fmt(sums.ce_net)}</span>
          </div>
          <div style={{ marginTop: 8, fontSize: 9, color: '#7A5600' }}>
            {(sums.ce_net || 0) > 0 ? '▲ CE OI building — writers adding = BEARISH ceiling' : (sums.ce_net || 0) < 0 ? '▼ CE OI cutting — writers covering = BULLISH' : '— No significant change'}
          </div>
        </div>

        {/* PE Sums */}
        <div style={{ background: '#0f0f0f', padding: 16 }}>
          <div style={{ ...S.header, fontSize: 9, marginBottom: 10 }}>PUT OI SUMMARY</div>
          <div style={S.row}>
            <span style={{ flex: 1, ...S.label }}>OI ADDED</span>
            <span style={{ ...S.green, fontWeight: 600, fontSize: 13 }}>{chgSign(sums.pe_oi_added)}{fmt(sums.pe_oi_added)}</span>
          </div>
          <div style={S.row}>
            <span style={{ flex: 1, ...S.label }}>OI REMOVED</span>
            <span style={{ ...S.red, fontWeight: 600, fontSize: 13 }}>-{fmt(sums.pe_oi_removed)}</span>
          </div>
          <div style={{ ...S.row, borderBottom: 'none', paddingTop: 8 }}>
            <span style={{ flex: 1, ...S.label, fontWeight: 700 }}>NET PE OI</span>
            <span style={{ color: chgColor(sums.pe_net), fontWeight: 700, fontSize: 15 }}>{chgSign(sums.pe_net)}{fmt(sums.pe_net)}</span>
          </div>
          <div style={{ marginTop: 8, fontSize: 9, color: '#7A5600' }}>
            {(sums.pe_net || 0) > 0 ? '▲ PE OI building — writers adding = BULLISH support' : (sums.pe_net || 0) < 0 ? '▼ PE OI cutting — writers covering = BEARISH' : '— No significant change'}
          </div>
        </div>
      </div>

      {/* ── Interpretations ── */}
      {interpretations.length > 0 && (
        <div style={{ background: '#0f0f0f', border: '1px solid #1f1f1f', padding: '12px 16px', marginBottom: 20 }}>
          <div style={{ ...S.header, fontSize: 9, marginBottom: 8 }}>INSTITUTIONAL INTERPRETATION</div>
          {interpretations.map((text, i) => (
            <div key={i} style={{ fontSize: 11, color: '#FFB300', padding: '3px 0' }}>→ {typeof text === 'string' ? text : JSON.stringify(text)}</div>
          ))}
        </div>
      )}

      {/* ── Strike-wise OI Change Table ── */}
      <div style={{ ...S.header, marginBottom: 8 }}>STRIKE-WISE OI CHANGES</div>

      {!hasData ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#444' }}>
          <div style={{ fontSize: 14, marginBottom: 8 }}>No OI data yet</div>
          <div style={{ fontSize: 10 }}>Login to Kite → OI changes will track in real-time</div>
        </div>
      ) : (
        <>
          {/* Table Header */}
          <div style={{ display: 'grid', gridTemplateColumns: '80px 90px 90px 80px 90px 90px 80px 80px', gap: 0, padding: '6px 0', borderBottom: '1px solid #1f1f1f', fontSize: 9, color: '#555', letterSpacing: 1, textTransform: 'uppercase' }}>
            <div>STRIKE</div>
            <div style={{ textAlign: 'right' }}>CE OI</div>
            <div style={{ textAlign: 'right' }}>CE CHANGE</div>
            <div style={{ textAlign: 'right' }}>CE LTP</div>
            <div style={{ textAlign: 'right' }}>PE OI</div>
            <div style={{ textAlign: 'right' }}>PE CHANGE</div>
            <div style={{ textAlign: 'right' }}>PE LTP</div>
            <div style={{ textAlign: 'right' }}>VOL</div>
          </div>

          {/* Table Rows */}
          {oiChanges.map((r, i) => {
            const isAtm = r.atm
            const bgColor = isAtm ? '#1a1400' : 'transparent'
            return (
              <div key={i} style={{
                display: 'grid', gridTemplateColumns: '80px 90px 90px 80px 90px 90px 80px 80px',
                gap: 0, padding: '5px 0', borderBottom: '1px solid #141414',
                fontSize: 11, background: bgColor,
              }}>
                <div style={{ color: isAtm ? '#FFB300' : '#E8E8E8', fontWeight: isAtm ? 700 : 400 }}>
                  {isAtm ? '★ ' : ''}{r.strike}
                </div>
                <div style={{ textAlign: 'right', color: '#E8E8E8' }}>{fmt(r.ce_oi)}</div>
                <div style={{ textAlign: 'right', color: chgColor(r.ce_change), fontWeight: 600 }}>
                  {chgSign(r.ce_change)}{fmt(r.ce_change)}
                </div>
                <div style={{ textAlign: 'right', color: '#E8E8E8' }}>₹{r.ce_ltp || '—'}</div>
                <div style={{ textAlign: 'right', color: '#E8E8E8' }}>{fmt(r.pe_oi)}</div>
                <div style={{ textAlign: 'right', color: chgColor(r.pe_change), fontWeight: 600 }}>
                  {chgSign(r.pe_change)}{fmt(r.pe_change)}
                </div>
                <div style={{ textAlign: 'right', color: '#E8E8E8' }}>₹{r.pe_ltp || '—'}</div>
                <div style={{ textAlign: 'right', color: '#555' }}>
                  {fmt((r.ce_volume || 0) + (r.pe_volume || 0))}
                </div>
              </div>
            )
          })}

          {oiChanges.length === 0 && (
            <div style={{ padding: 20, textAlign: 'center', color: '#444', fontSize: 11 }}>
              Building OI history... changes will appear after 2 cycles
            </div>
          )}
        </>
      )}

      {/* ── Volume Spikes ── */}
      {volumeSpikes.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <div style={{ ...S.header, fontSize: 9, marginBottom: 8 }}>VOLUME SPIKES</div>
          {volumeSpikes.map((v, i) => (
            <div key={i} style={{ fontSize: 10, color: '#FFB300', padding: '3px 0', borderBottom: '1px solid #141414' }}>
              ⚡ {v.strike} {v.type} — Volume {fmt(v.volume)} ({v.ratio}x avg)
            </div>
          ))}
        </div>
      )}

      {/* ── Recent Changes (last cycle) ── */}
      {recentChanges.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <div style={{ ...S.header, fontSize: 9, marginBottom: 8 }}>LAST 5 SECONDS — LIVE CHANGES</div>
          {recentChanges.map((r, i) => (
            <div key={i} style={{ display: 'flex', gap: 20, fontSize: 10, padding: '3px 0', borderBottom: '1px solid #141414' }}>
              <span style={S.white}>{r.strike}</span>
              <span style={{ color: chgColor(r.ce_delta) }}>CE: {chgSign(r.ce_delta)}{fmt(r.ce_delta)}</span>
              <span style={{ color: chgColor(r.pe_delta) }}>PE: {chgSign(r.pe_delta)}{fmt(r.pe_delta)}</span>
              <span style={S.dim}>CE ₹{r.ce_ltp} · PE ₹{r.pe_ltp}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
