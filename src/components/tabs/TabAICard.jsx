export default function TabAICard({ engines, signal }) {
  const e24 = engines?.e24?.data || {};
  const confidence = e24.confidence ?? 0;
  const rationale = e24.rationale || '';
  const riskFactors = e24.risk_factors || [];
  const tradeRec = e24.trade_recommendation || '';

  const confLabel = confidence > 75
    ? { text: 'HIGH', color: '#00C853' }
    : confidence >= 50
      ? { text: 'MEDIUM', color: '#FFB300' }
      : { text: 'LOW', color: '#FF3D00' };

  const isCall = (signal?.type || tradeRec || '').toUpperCase().includes('CALL');
  const isPut = (signal?.type || tradeRec || '').toUpperCase().includes('PUT');
  const signalColor = isCall ? '#00C853' : isPut ? '#FF3D00' : '#E8E8E8';

  const signalText = tradeRec
    || (signal
      ? `${(signal.type || 'BUY CALL').toUpperCase()} — ${signal.instrument || 'NIFTY'} ${signal.strike || ''} CE WEEKLY`
      : '');

  const entryArr = Array.isArray(signal?.entry) ? signal.entry : (signal?.entry ? [signal.entry] : []);
  const entryStr = entryArr.length ? entryArr.join(' / ') : '--';
  const sl = signal?.sl ?? '--';
  const t1 = signal?.t1 ?? '--';
  const t2 = signal?.t2 ?? '--';

  const engineKeys = Array.from({ length: 24 }, (_, i) => `e${String(i + 1).padStart(2, '0')}`);
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
  };

  const passingEngines = engineKeys.filter(k => {
    const eng = engines?.[k];
    if (!eng) return false;
    const verdict = (eng.verdict || eng.status || '').toUpperCase();
    return verdict === 'PASS';
  });

  const strikeVal = signal?.strike || '--';
  const typeVal = isCall ? 'ATM Call' : isPut ? 'ATM Put' : '--';
  const entryZone = entryArr.length >= 2
    ? `${entryArr[0]} - ${entryArr[entryArr.length - 1]}`
    : entryStr;

  const entryPrice = entryArr.length ? Number(entryArr[0]) : 0;
  const slPrice = signal?.sl ?? (entryPrice ? (entryPrice * 0.85).toFixed(1) : '--');
  const supportLevel = engines?.e03?.data?.support || engines?.e03?.support || '--';

  const hasData = signal || (e24 && (rationale || tradeRec));

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
        padding: '20px 24px',
        maxWidth: 920,
        margin: '0 auto',
        minHeight: 400,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
      }}>
        <div style={{ color: '#333', fontSize: 14, fontWeight: 700, letterSpacing: 4, textTransform: 'uppercase' }}>
          AI ANALYSIS PENDING
        </div>
        <div style={{ color: '#333', fontSize: 10, letterSpacing: 1, fontFamily: "'IBM Plex Mono', monospace" }}>
          Login and wait for signal confluence to trigger AI reasoning engine
        </div>
      </div>
    );
  }

  return (
    <div style={{
      fontFamily: "'IBM Plex Mono', monospace",
      background: '#0a0a0a',
      padding: '20px 24px',
      maxWidth: 920,
      margin: '0 auto',
    }}>
      {/* Title */}
      <div style={{ color: '#FFB300', fontSize: 15, fontWeight: 700, letterSpacing: 4, fontFamily: "'IBM Plex Mono', monospace" }}>
        BLOOM AI — TRADE REASONING ENGINE
      </div>

      {/* Sub */}
      <div style={{ color: '#444', fontSize: 9, marginTop: 4, marginBottom: 28, fontFamily: "'IBM Plex Mono', monospace" }}>
        Powered by Claude · Confidence:{' '}
        <span style={{ color: confLabel.color, fontWeight: 700 }}>{confLabel.text}</span>
      </div>

      {/* Sections */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

        {/* 1. TRADE SIGNAL */}
        <div>
          <div style={sectionHeader}>TRADE SIGNAL</div>
          <div style={{ color: signalColor, fontSize: 22, fontWeight: 700, marginBottom: 8, fontFamily: "'IBM Plex Mono', monospace" }}>
            {signalText || '--'}
          </div>
          <div style={{ color: '#E8E8E8', fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
            Entry: {entryStr} · SL: <span style={{ color: '#FF3D00' }}>{sl}</span> · T1: {t1} · T2: {t2}
          </div>
        </div>

        {/* 2. WHY THIS TRADE */}
        <div>
          <div style={sectionHeader}>WHY THIS TRADE</div>
          {rationale ? (
            <div style={{ color: '#7A5600', fontSize: 11, lineHeight: 1.8, fontStyle: 'italic', fontFamily: "'IBM Plex Mono', monospace" }}>
              {rationale}
            </div>
          ) : (
            <div style={{ color: '#444', fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
              AI engine will generate reasoning when signal fires...
            </div>
          )}
        </div>

        {/* 3. SUPPORTING ENGINES */}
        <div>
          <div style={sectionHeader}>SUPPORTING ENGINES</div>
          {passingEngines.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {passingEngines.map(k => (
                <div key={k} style={{ fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
                  <span style={{ color: '#444' }}>{k.toUpperCase()}</span>
                  <span style={{ color: '#E8E8E8' }}> — {engineDescriptions[k] || 'Engine'}</span>
                  <span style={{ color: '#00C853', marginLeft: 8 }}>&#10003;</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: '#444', fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>No engines currently passing</div>
          )}
        </div>

        {/* 4. WHAT TO WATCH */}
        <div>
          <div style={sectionHeader}>WHAT TO WATCH</div>
          {riskFactors.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {riskFactors.map((r, i) => (
                <div key={i} style={{ color: '#FF3D00', fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
                  {'\u2192'} {r}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div style={{ color: '#FF3D00', fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>{'\u2192'} Expiry day theta decay accelerates after 1:30 PM</div>
              <div style={{ color: '#FF3D00', fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>{'\u2192'} Global cues may override domestic setup</div>
              <div style={{ color: '#FF3D00', fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>{'\u2192'} Low liquidity after 3:00 PM can widen spreads</div>
            </div>
          )}
        </div>

        {/* 5. ENTRY EXECUTION */}
        <div>
          <div style={sectionHeader}>ENTRY EXECUTION</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div style={{ fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
              <span style={{ color: '#FFB300' }}>Strike: </span>
              <span style={{ color: '#E8E8E8' }}>{strikeVal}</span>
            </div>
            <div style={{ fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
              <span style={{ color: '#FFB300' }}>Type: </span>
              <span style={{ color: '#E8E8E8' }}>{typeVal}</span>
            </div>
            <div style={{ fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
              <span style={{ color: '#FFB300' }}>Lot Size: </span>
              <span style={{ color: '#E8E8E8' }}>25</span>
            </div>
            <div style={{ fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
              <span style={{ color: '#FFB300' }}>Entry Zone: </span>
              <span style={{ color: '#E8E8E8' }}>{entryZone}</span>
            </div>
          </div>
        </div>

        {/* 6. STOP LOSS LOGIC */}
        <div>
          <div style={sectionHeader}>STOP LOSS LOGIC</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div style={{ fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
              <span style={{ color: '#FFB300' }}>Primary: </span>
              <span style={{ color: '#E8E8E8' }}>15% of entry premium = if entered at </span>
              <span style={{ color: '#FF3D00', fontWeight: 700 }}>{entryArr[0] || '--'}</span>
              <span style={{ color: '#E8E8E8' }}>, SL = </span>
              <span style={{ color: '#FF3D00', fontWeight: 700 }}>{slPrice}</span>
            </div>
            <div style={{ fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
              <span style={{ color: '#FFB300' }}>Structure: </span>
              <span style={{ color: '#FF3D00' }}>Exit if 15m candle closes below {supportLevel}</span>
            </div>
            <div style={{ fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
              <span style={{ color: '#FFB300' }}>Score: </span>
              <span style={{ color: '#FF3D00' }}>Exit if confluence score drops to 3 or below</span>
            </div>
            <div style={{ fontSize: 11, fontFamily: "'IBM Plex Mono', monospace" }}>
              <span style={{ color: '#FFB300' }}>Rule: </span>
              <span style={{ color: '#FF3D00', fontWeight: 700 }}>NEVER average down on a losing options position</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
