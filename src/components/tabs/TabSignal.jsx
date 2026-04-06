export default function TabSignal({ signal, engines, tick }) {
  // --- Helpers ---
  const safe = (obj, path, fallback = '--') => {
    try { return path.split('.').reduce((o, k) => o[k], obj) ?? fallback }
    catch { return fallback }
  }

  const signalTypeColor = (type) => {
    if (!type) return '#444'
    const t = type.toUpperCase()
    if (t.includes('CALL') || t.includes('BUY CALL')) return '#00C853'
    if (t.includes('PUT') || t.includes('BLOCK') || t.includes('BUY PUT')) return '#FF3D00'
    if (t.includes('SKIP') || t.includes('WAIT')) return '#444'
    return '#E8E8E8'
  }

  const score = signal?.confluence_score ?? signal?.score ?? 0
  const totalDots = 7

  const scoreLabel = score >= 6
    ? { text: 'STRONG BUY', color: '#00C853' }
    : score >= 4
      ? { text: 'BUY', color: '#FFB300' }
      : { text: 'WAIT', color: '#444' }

  // --- Tier vote logic ---
  const tierT1 = () => {
    const keys = ['e01', 'e02', 'e03', 'e04']
    const passed = keys.filter(k => engines?.[k]?.verdict === 'PASS' || engines?.[k]?.status === 'PASS').length
    const allPass = passed === 4
    return allPass
      ? { label: `\u2713 ${passed}/4 PASS`, color: '#00C853' }
      : { label: `\u2717 BLOCKED`, color: '#FF3D00' }
  }

  const tierT2 = () => {
    const keys = ['e05', 'e06', 'e07', 'e08', 'e09', 'e10', 'e11']
    let bull = 0, bear = 0
    keys.forEach(k => {
      const eng = engines?.[k]
      if (!eng) return
      const v = eng.verdict || eng.direction || eng.bias || eng.data?.direction || eng.data?.bias || ''
      const vs = (typeof v === 'string' ? v : String(v)).toUpperCase()
      if (vs.includes('BULL') || vs.includes('CALL') || vs.includes('LONG')) bull++
      else if (vs.includes('BEAR') || vs.includes('PUT') || vs.includes('SHORT')) bear++
    })
    const total = keys.length
    return bull >= bear
      ? { label: `${bull}/${total} CALL`, color: bull > 0 ? '#00C853' : '#FFB300' }
      : { label: `${bear}/${total} PUT`, color: '#FF3D00' }
  }

  const tierT3 = () => {
    const keys = ['e12', 'e13', 'e14', 'e15', 'e16', 'e17', 'e18']
    const active = keys.filter(k => engines?.[k]?.verdict === 'PASS' || engines?.[k]?.status === 'ACTIVE').length
    return { label: `${active}/7 ACTIVE`, color: '#FFB300' }
  }

  const tierT4 = () => {
    const keys = ['e19', 'e20', 'e21', 'e22', 'e23', 'e24']
    const alertCount = keys.filter(k => engines?.[k]?.alert || engines?.[k]?.active).length
    return { label: `${alertCount} ALERTS \u2605`, color: '#2196F3' }
  }

  const tiers = [
    { badge: 'T1', badgeBg: '#FF3D00', code: 'T1 CORE', engines: 'E01-E04 Gate', ...tierT1() },
    { badge: 'T2', badgeBg: '#FFB300', code: 'T2 DIR',  engines: 'E05-E11 Direction', ...tierT2() },
    { badge: 'T3', badgeBg: '#00C853', code: 'T3 AMP',  engines: 'E12-E18 Amplifier', ...tierT3() },
    { badge: 'T4', badgeBg: '#2196F3', code: 'T4 BIG',  engines: 'E19-E24 Big Money', ...tierT4() },
  ]

  // --- E09 Technical votes ---
  const techData09 = engines?.e09?.data || {}
  let rawVotes = techData09.votes
  if (typeof rawVotes === 'string') {
    try { rawVotes = JSON.parse(rawVotes) } catch { rawVotes = null }
  }
  const techVotes = (rawVotes && typeof rawVotes === 'object') ? rawVotes : {}
  const techIndicators = ['ema', 'rsi', 'macd', 'supertrend']

  const voteLine = (v) => {
    if (!v) return { signal: '--', reading: '--', vote: '--', color: '#444' }
    const bull = (v.signal || v.direction || '').toUpperCase().includes('BULL')
    return {
      signal: bull ? 'BULLISH \u25B2' : 'BEARISH \u25BC',
      reading: v.value ?? v.reading ?? '--',
      vote: bull ? '+1 CALL' : '+1 PUT',
      color: bull ? '#00C853' : '#FF3D00',
    }
  }

  // --- E06 PCR ---
  const pcr = engines?.e06?.data
  const pcrValue = pcr?.pcr ?? '--'
  const pcrBias = pcr?.bias ?? pcr?.reading ?? '--'
  const pcrBull = (pcrBias || '').toUpperCase().includes('BULL') || (pcrBias || '').toUpperCase().includes('CALL')
  const pcrSignalText = pcrBull ? 'CONTRARIAN CALL \u2191' : 'CONTRARIAN PUT \u2193'
  const pcrSignalColor = pcrBull ? '#00C853' : '#FF3D00'
  const pcrInterpretation = pcr?.interpretation ?? pcr?.note ?? ''

  // --- E07 Writer traps ---
  const fmtTime = (ts) => {
    if (!ts) return ''
    if (typeof ts === 'number' && ts > 1000000000) {
      const d = new Date(ts * 1000)
      return d.toLocaleTimeString('en-IN', {hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false})
    }
    return String(ts)
  }
  const traps = (engines?.e07?.data?.traps || []).slice(0, 5)

  // --- IV Gate color ---
  const ivGateColor = (val) => {
    if (!val || val === '--') return '#E8E8E8'
    const v = val.toUpperCase()
    if (v === 'OPEN') return '#00C853'
    if (v === 'PARTIAL') return '#FFB300'
    if (v === 'BLOCKED') return '#FF3D00'
    return '#E8E8E8'
  }

  const ivGateVal = safe(engines, 'e02.data.iv_status', safe(engines, 'e02.verdict', '--'))

  // --- Signal data table ---
  const dataRows = [
    { label: 'INSTRUMENT', value: signal?.instrument ?? safe(signal, 'strike_info'), color: '#E8E8E8' },
    { label: 'ENTRY', value: Array.isArray(signal?.entry) ? signal.entry.join(' — ') : (signal?.entry ?? '--'), color: '#E8E8E8' },
    { label: 'STOP LOSS', value: typeof signal?.sl === 'object' ? JSON.stringify(signal.sl) : (signal?.stop_loss ?? signal?.sl ?? '--'), color: '#FF3D00' },
    { label: 'TARGET 1', value: typeof signal?.t1 === 'object' ? JSON.stringify(signal.t1) : (signal?.target1 ?? signal?.t1 ?? '--'), color: '#00C853' },
    { label: 'TARGET 2', value: typeof signal?.t2 === 'object' ? JSON.stringify(signal.t2) : (signal?.target2 ?? signal?.t2 ?? '--'), color: '#00C853' },
    { label: 'CONFIDENCE', value: signal?.confidence ?? '--', color: '#E8E8E8' },
    { label: 'IV GATE', value: ivGateVal, color: ivGateColor(ivGateVal) },
    { label: 'STRUCTURE', value: safe(engines, 'e03.data.structure', safe(engines, 'e03.verdict', '--')), color: '#E8E8E8' },
    { label: 'MODE', value: signal?.mode ?? 'INTRADAY', color: '#FFB300' },
  ]

  // --- Keyframes injected once ---
  const pulseKeyframes = `
    @keyframes signalPulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }
    @keyframes dotFadeIn {
      from { opacity: 0; transform: scale(0.5); }
      to { opacity: 1; transform: scale(1); }
    }
  `

  // --- Styles ---
  const S = {
    root: {
      display: 'flex',
      gap: 0,
      height: '100%',
      width: '100%',
      fontFamily: "'IBM Plex Mono', monospace",
      background: '#0a0a0a',
      color: '#E8E8E8',
      lineHeight: 1.6,
    },
    left: {
      width: 360,
      minWidth: 360,
      borderRight: '1px solid #1f1f1f',
      overflowY: 'auto',
      background: '#0a0a0a',
    },
    right: {
      flex: 1,
      overflowY: 'auto',
      padding: 16,
      background: '#0a0a0a',
    },
    sectionHeader: {
      fontSize: 10,
      color: '#FFB300',
      fontWeight: 600,
      letterSpacing: 3,
      textTransform: 'uppercase',
      borderBottom: '1px solid #1f1f1f',
      paddingBottom: 8,
      marginBottom: 16,
      lineHeight: 1.6,
    },
    section: {
      padding: '16px 20px',
      borderBottom: '1px solid #1f1f1f',
    },
    dataRow: {
      display: 'flex',
      justifyContent: 'space-between',
      padding: '5px 0',
      borderBottom: '1px solid #141414',
    },
    dataLabel: {
      color: '#555',
      fontSize: 10,
      letterSpacing: 1,
    },
    dataValue: {
      fontSize: 11,
      fontWeight: 500,
    },
  }

  return (
    <div style={S.root}>
      <style>{pulseKeyframes}</style>

      {/* ========== LEFT SIDE ========== */}
      <div style={S.left}>

        {/* Section 1: SIGNAL COMMAND */}
        <div style={S.section}>
          <div style={S.sectionHeader}>SIGNAL COMMAND</div>

          {signal && signal.type ? (
            <>
              {/* Big signal type */}
              <div style={{
                fontSize: 28,
                fontWeight: 700,
                letterSpacing: 2,
                color: signalTypeColor(signal.type),
                lineHeight: 1.2,
              }}>
                {(signal.type || 'SIGNAL').toUpperCase()}
              </div>

              {/* Strike line */}
              <div style={{
                color: '#FFB300',
                fontSize: 12,
                marginTop: 4,
                letterSpacing: 1,
              }}>
                {signal.strike_label || `NIFTY ${signal.strike || '--'} ${signal.option_type || 'CE'} \u00B7 WEEKLY`}
              </div>

              {/* Confluence score */}
              <div style={{ marginTop: 16 }}>
                <span style={{ color: '#555', fontSize: 10, letterSpacing: 1 }}>CONFLUENCE:</span>
                <span style={{ color: '#E8E8E8', fontSize: 12, fontWeight: 600, marginLeft: 6 }}>{score} / {totalDots}</span>

                <span style={{ display: 'inline-flex', alignItems: 'center', marginLeft: 10, verticalAlign: 'middle' }}>
                  {Array.from({ length: totalDots }).map((_, i) => (
                    <span
                      key={i}
                      style={{
                        display: 'inline-block',
                        width: 10,
                        height: 10,
                        marginRight: 3,
                        background: i < score ? '#FFB300' : '#333',
                        animation: 'dotFadeIn 0.3s ease forwards',
                        animationDelay: `${i * 100}ms`,
                      }}
                    />
                  ))}
                </span>

                <span style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: 1,
                  marginLeft: 8,
                  color: scoreLabel.color,
                }}>
                  {scoreLabel.text}
                </span>
              </div>

              {/* Data table */}
              <div style={{ marginTop: 16 }}>
                {dataRows.map((row) => (
                  <div key={row.label} style={S.dataRow}>
                    <span style={S.dataLabel}>{row.label}</span>
                    <span style={{ ...S.dataValue, color: row.color || '#E8E8E8' }}>{row.value}</span>
                  </div>
                ))}
              </div>

              {/* Footer */}
              <div style={{
                fontStyle: 'italic',
                color: '#333',
                fontSize: 9,
                marginTop: 16,
                lineHeight: 1.6,
              }}>
                STOP LOSS RULE: Maximum 15-20% of entry premium. Hard rule, no exceptions.
              </div>
            </>
          ) : (
            <div style={{
              color: '#444',
              fontSize: 14,
              textAlign: 'center',
              padding: '40px 0',
              letterSpacing: 2,
              animation: 'signalPulse 2s ease-in-out infinite',
            }}>
              WAITING FOR CONFLUENCE...
            </div>
          )}
        </div>

        {/* Section 2: TIER VOTE STATUS */}
        <div style={S.section}>
          <div style={S.sectionHeader}>TIER VOTE STATUS</div>

          {tiers.map((tier) => (
            <div key={tier.code} style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '8px 0',
              borderBottom: '1px solid #141414',
            }}>
              <span style={{
                display: 'inline-block',
                padding: '2px 8px',
                fontWeight: 700,
                fontSize: 9,
                letterSpacing: 1,
                color: '#000',
                background: tier.badgeBg,
              }}>
                {tier.code}
              </span>
              <span style={{ color: '#555', fontSize: 10, flex: 1 }}>{tier.engines}</span>
              <span style={{ fontSize: 11, fontWeight: 600, color: tier.color }}>{tier.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ========== RIGHT SIDE ========== */}
      <div style={S.right}>

        {/* Panel 1: TECHNICAL ENGINE E9 */}
        <div style={{ marginBottom: 20 }}>
          <div style={S.sectionHeader}>TECHNICAL ENGINE &mdash; E9</div>

          {/* Table header */}
          <div style={{
            display: 'flex',
            color: '#555',
            fontSize: 9,
            letterSpacing: 1,
            borderBottom: '1px solid #1f1f1f',
            paddingBottom: 6,
            marginBottom: 2,
          }}>
            <span style={{ flex: 2 }}>INDICATOR</span>
            <span style={{ flex: 2 }}>SIGNAL</span>
            <span style={{ flex: 2 }}>READING</span>
            <span style={{ flex: 1, textAlign: 'right' }}>VOTE</span>
          </div>

          {/* Table rows */}
          {Object.keys(techVotes).length > 0 ? (
            techIndicators.map((ind) => {
              const v = voteLine(techVotes[ind])
              return (
                <div key={ind} style={{
                  display: 'flex',
                  fontSize: 11,
                  padding: '6px 0',
                  borderBottom: '1px solid #141414',
                  alignItems: 'center',
                }}>
                  <span style={{ flex: 2, color: '#E8E8E8', textTransform: 'uppercase', fontWeight: 500 }}>{ind}</span>
                  <span style={{ flex: 2, color: v.color }}>{v.signal}</span>
                  <span style={{ flex: 2, color: '#E8E8E8' }}>{v.reading}</span>
                  <span style={{ flex: 1, textAlign: 'right', fontWeight: 700, color: v.color }}>{v.vote}</span>
                </div>
              )
            })
          ) : engines?.e09?.data ? (
            <div style={{ fontSize: 11, padding: '8px 0', color: '#FFB300' }}>
              {techData09.direction || techData09.summary || 'Technical data received — votes parsing...'}
            </div>
          ) : (
            <div style={{ color: '#333', fontSize: 11, padding: '12px 0' }}>
              Awaiting technical data...
            </div>
          )}
        </div>

        {/* Panel 2: PCR FLOW ENGINE E6 */}
        <div style={{ marginBottom: 20 }}>
          <div style={S.sectionHeader}>PCR FLOW ENGINE &mdash; E6</div>

          {pcr ? (
            <>
              <div style={{ fontSize: 12, lineHeight: 1.8 }}>
                <span style={{ color: '#555' }}>PCR: </span>
                <span style={{ color: '#E8E8E8', fontWeight: 600 }}>{pcrValue}</span>
                <span style={{ color: '#333', margin: '0 8px' }}>|</span>
                <span style={{ color: '#555' }}>READING: </span>
                <span style={{ color: '#FFB300' }}>{pcrBias}</span>
                <span style={{ color: '#333', margin: '0 8px' }}>|</span>
                <span style={{ color: pcrSignalColor }}>{pcrSignalText}</span>
              </div>
              {pcrInterpretation && (
                <div style={{
                  fontSize: 10,
                  color: '#7A5600',
                  fontStyle: 'italic',
                  marginTop: 6,
                  lineHeight: 1.6,
                }}>
                  {pcrInterpretation}
                </div>
              )}
            </>
          ) : (
            <div style={{ color: '#333', fontSize: 11, padding: '8px 0' }}>
              Awaiting PCR flow data...
            </div>
          )}
        </div>

        {/* Panel 3: WRITER TRAP FEED E7 */}
        <div>
          <div style={S.sectionHeader}>WRITER TRAP FEED &mdash; E7</div>

          {traps.length > 0 ? (
            traps.map((trap, i) => (
              <div key={i} style={{
                fontSize: 10,
                padding: '4px 0',
                borderBottom: '1px solid #141414',
                color: trap.active !== false ? '#FFB300' : '#444',
                lineHeight: 1.6,
              }}>
                <span style={{ color: '#555', marginRight: 4 }}>[{fmtTime(trap.timestamp) || fmtTime(trap.time) || '--:--'}]</span>
                {trap.strike || ''} &mdash; {trap.description || trap.text || ''}
              </div>
            ))
          ) : (
            <div style={{ color: '#333', fontSize: 11, padding: '8px 0' }}>
              No writer traps detected &mdash; monitoring...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
