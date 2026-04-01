export default function TabAICard({ engines, signal }) {
  // --- Helpers ---
  const e24 = engines?.e24?.data || {}
  const confidence = e24.confidence ?? 0
  const rationale = e24.rationale || ''
  const riskFactors = e24.risk_factors || []
  const tradeRec = e24.trade_recommendation || ''

  const now = new Date()
  const istTime = now.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })

  const confLabel = confidence > 75
    ? { text: 'HIGH', color: '#00C853' }
    : confidence >= 50
      ? { text: 'MEDIUM', color: '#FFB300' }
      : { text: 'LOW', color: '#FF3D00' }

  const isCall = (signal?.type || tradeRec || '').toUpperCase().includes('CALL')
  const isPut = (signal?.type || tradeRec || '').toUpperCase().includes('PUT')
  const signalColor = isCall ? '#00C853' : isPut ? '#FF3D00' : '#E8E8E8'

  const signalText = tradeRec
    || (signal
      ? `${(signal.type || 'BUY CALL').toUpperCase()} — ${signal.instrument || 'NIFTY'} ${signal.strike || ''} CE WEEKLY`
      : '')

  const entryArr = Array.isArray(signal?.entry) ? signal.entry : (signal?.entry ? [signal.entry] : [])
  const entryStr = entryArr.length ? entryArr.join(' / ') : '--'
  const sl = signal?.sl ?? '--'
  const t1 = signal?.t1 ?? '--'
  const t2 = signal?.t2 ?? '--'

  // Supporting engines: those with PASS verdict
  const engineKeys = Array.from({ length: 24 }, (_, i) => `e${String(i + 1).padStart(2, '0')}`)
  const engineDescriptions = {
    e01: 'OI Change Analysis',
    e02: 'PCR Trend Monitor',
    e03: 'Support/Resistance Levels',
    e04: 'IV Skew Scanner',
    e05: 'Volume Surge Detector',
    e06: 'Price Action Engine',
    e07: 'VWAP Deviation Tracker',
    e08: 'Momentum Oscillator',
    e09: 'Delivery % Filter',
    e10: 'FII/DII Flow Engine',
    e11: 'Sector Rotation Map',
    e12: 'Breadth Thrust Monitor',
    e13: 'Futures Premium Engine',
    e14: 'Max Pain Calculator',
    e15: 'Gamma Exposure Map',
    e16: 'Historical Pattern Match',
    e17: 'News Sentiment NLP',
    e18: 'Correlation Matrix',
    e19: 'Volatility Regime',
    e20: 'Time Decay Analyzer',
    e21: 'Liquidity Depth Scanner',
    e22: 'Block Deal Tracker',
    e23: 'Global Cue Aggregator',
    e24: 'Claude AI Reasoning',
  }

  const passingEngines = engineKeys.filter(k => {
    const eng = engines?.[k]
    if (!eng) return false
    const verdict = (eng.verdict || eng.status || '').toUpperCase()
    return verdict === 'PASS'
  })

  // Entry details
  const strikeVal = signal?.strike || '--'
  const typeVal = isCall ? 'ATM Call' : isPut ? 'ATM Put' : '--'
  const entryZone = entryArr.length >= 2
    ? `${entryArr[0]} - ${entryArr[entryArr.length - 1]}`
    : entryStr

  // SL calculation
  const entryPrice = entryArr.length ? Number(entryArr[0]) : 0
  const slPrice = signal?.sl ?? (entryPrice ? (entryPrice * 0.85).toFixed(1) : '--')
  const supportLevel = engines?.e03?.data?.support || engines?.e03?.support || '--'

  // No data state
  const hasData = signal || (e24 && (rationale || tradeRec))

  if (!hasData) {
    return (
      <div style={{
        fontFamily: "'IBM Plex Mono', monospace",
        background: '#0a0a0a',
        width: '100%',
        maxWidth: 900,
        margin: '0 auto',
        padding: 16,
        minHeight: 400,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
      }}>
        <div style={{ color: '#444444', fontSize: 14, fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase' }}>
          BLOOM AI ANALYSIS NOT YET AVAILABLE
        </div>
        <div style={{ color: '#444444', fontSize: 10 }}>
          Login and wait for signal confluence to trigger AI reasoning engine
        </div>
      </div>
    )
  }

  return (
    <div style={{
      fontFamily: "'IBM Plex Mono', monospace",
      background: '#0a0a0a',
      width: '100%',
      maxWidth: 900,
      margin: '0 auto',
      padding: 16,
    }}>
      {/* Title */}
      <div style={{ color: '#FFB300', fontSize: 16, fontWeight: 700, letterSpacing: 3, marginBottom: 2 }}>
        BLOOM AI — TRADE REASONING ENGINE
      </div>

      {/* Sub */}
      <div style={{ color: '#444444', fontSize: 10, marginBottom: 20 }}>
        Powered by Claude MCP · Generated: {istTime} IST · Confidence:{' '}
        <span style={{ color: confLabel.color, fontWeight: 700 }}>{confLabel.text}</span>
      </div>

      {/* Sections */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

        {/* 1. TRADE SIGNAL */}
        <Section title="TRADE SIGNAL">
          <div style={{ color: signalColor, fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
            {signalText || '--'}
          </div>
          <div style={{ color: '#E8E8E8', fontSize: 12 }}>
            Entry: {entryStr} · SL: <span style={{ color: '#FF3D00' }}>{sl}</span> · T1: {t1} · T2: {t2}
          </div>
        </Section>

        {/* 2. WHY THIS TRADE */}
        <Section title="WHY THIS TRADE">
          {rationale ? (
            <div style={{ color: '#7A5600', fontSize: 11, lineHeight: 1.8 }}>
              {rationale}
            </div>
          ) : (
            <div style={{ color: '#444444', fontSize: 11 }}>
              AI engine will generate reasoning when signal fires...
            </div>
          )}
        </Section>

        {/* 3. SUPPORTING ENGINES */}
        <Section title="SUPPORTING ENGINES">
          {passingEngines.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {passingEngines.map(k => (
                <div key={k} style={{ fontSize: 11 }}>
                  <span style={{ color: '#444444' }}>{k.toUpperCase()}</span>
                  <span style={{ color: '#E8E8E8' }}> — {engineDescriptions[k] || 'Engine'}</span>
                  <span style={{ color: '#00C853', marginLeft: 6 }}>&#10003;</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: '#444444', fontSize: 11 }}>No engines currently passing</div>
          )}
        </Section>

        {/* 4. WHAT TO WATCH (RISKS) */}
        <Section title="WHAT TO WATCH (RISKS)">
          {riskFactors.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {riskFactors.map((r, i) => (
                <div key={i} style={{ color: '#FF3D00', fontSize: 11 }}>
                  → {r}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <div style={{ color: '#FF3D00', fontSize: 11 }}>→ Expiry day theta decay accelerates after 1:30 PM</div>
              <div style={{ color: '#FF3D00', fontSize: 11 }}>→ Global cues may override domestic setup</div>
              <div style={{ color: '#FF3D00', fontSize: 11 }}>→ Low liquidity after 3:00 PM can widen spreads</div>
            </div>
          )}
        </Section>

        {/* 5. ENTRY EXECUTION */}
        <Section title="ENTRY EXECUTION">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Row label="Strike" value={strikeVal} />
            <Row label="Type" value={typeVal} />
            <Row label="Lot Size" value="25" />
            <Row label="Entry Zone" value={entryZone} />
          </div>
        </Section>

        {/* 6. STOP LOSS LOGIC */}
        <Section title="STOP LOSS LOGIC">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <div style={{ fontSize: 11 }}>
              <span style={{ color: '#FFB300' }}>Primary: </span>
              <span style={{ color: '#E8E8E8' }}>15% of entry premium = if entered at ₹{entryArr[0] || '--'}, SL = </span>
              <span style={{ color: '#FF3D00', fontWeight: 700 }}>₹{slPrice}</span>
            </div>
            <div style={{ fontSize: 11 }}>
              <span style={{ color: '#FFB300' }}>Structure: </span>
              <span style={{ color: '#E8E8E8' }}>Exit if 15m candle closes below {supportLevel}</span>
            </div>
            <div style={{ fontSize: 11 }}>
              <span style={{ color: '#FFB300' }}>Score: </span>
              <span style={{ color: '#E8E8E8' }}>Exit if confluence score drops to 3 or below</span>
            </div>
            <div style={{ fontSize: 11 }}>
              <span style={{ color: '#FFB300' }}>Rule: </span>
              <span style={{ color: '#FF3D00', fontWeight: 700 }}>NEVER average down on a losing options position</span>
            </div>
          </div>
        </Section>

      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div style={{
      background: '#0f0f0f',
      border: '1px solid #1f1f1f',
      borderRadius: 0,
      padding: 12,
    }}>
      <div style={{
        color: '#FFB300',
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: 2,
        textTransform: 'uppercase',
        marginBottom: 8,
        fontFamily: "'IBM Plex Mono', monospace",
      }}>
        {title}
      </div>
      <div style={{ fontFamily: "'IBM Plex Mono', monospace" }}>
        {children}
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div style={{ fontSize: 11 }}>
      <span style={{ color: '#FFB300' }}>{label}: </span>
      <span style={{ color: '#E8E8E8' }}>{value}</span>
    </div>
  )
}
