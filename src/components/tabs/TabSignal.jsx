export default function TabSignal({ signal, engines, tick }) {
  // --- Helpers ---
  const safe = (obj, path, fallback = '--') => {
    try { return path.split('.').reduce((o, k) => o[k], obj) ?? fallback }
    catch { return fallback }
  }

  const signalColor = (type) => {
    if (!type) return 'text-gray'
    const t = type.toUpperCase()
    if (t.includes('CALL') || t.includes('BUY CALL')) return 'text-green'
    if (t.includes('PUT') || t.includes('BLOCK') || t.includes('BUY PUT')) return 'text-red'
    if (t.includes('SKIP')) return 'text-gray'
    return 'text-white'
  }

  const score = signal?.confluence_score ?? signal?.score ?? 0
  const totalDots = 7

  const scoreLabel = score >= 6
    ? { text: 'STRONG BUY', color: 'text-green' }
    : score >= 4
      ? { text: 'BUY', color: 'text-amber' }
      : { text: 'WAIT', color: 'text-gray' }

  // --- Tier vote logic ---
  const tierT1 = () => {
    const keys = ['e01', 'e02', 'e03', 'e04']
    const passed = keys.filter(k => engines?.[k]?.verdict === 'PASS' || engines?.[k]?.status === 'PASS').length
    const allPass = passed === 4
    return allPass
      ? { label: `\u2713 ${passed}/4 PASS`, color: 'text-green' }
      : { label: `\u2717 BLOCKED`, color: 'text-red' }
  }

  const tierT2 = () => {
    const keys = ['e05', 'e06', 'e07', 'e08', 'e09', 'e10', 'e11']
    let bull = 0, bear = 0
    keys.forEach(k => {
      const v = engines?.[k]?.verdict || engines?.[k]?.bias || ''
      if (v.toUpperCase().includes('BULL') || v.toUpperCase().includes('CALL')) bull++
      else if (v.toUpperCase().includes('BEAR') || v.toUpperCase().includes('PUT')) bear++
    })
    const total = keys.length
    return bull >= bear
      ? { label: `${bull}/${total} CALL`, color: 'text-amber' }
      : { label: `${bear}/${total} PUT`, color: 'text-amber' }
  }

  const tierT3 = () => {
    const keys = ['e12', 'e13', 'e14', 'e15', 'e16', 'e17', 'e18']
    const active = keys.filter(k => engines?.[k]?.verdict === 'PASS' || engines?.[k]?.status === 'ACTIVE').length
    return { label: `${active}/7 ACTIVE`, color: 'text-amber' }
  }

  const tierT4 = () => {
    const keys = ['e19', 'e20', 'e21', 'e22', 'e23', 'e24']
    const alertCount = keys.filter(k => engines?.[k]?.alert || engines?.[k]?.active).length
    return { label: `${alertCount} ALERTS \u2605`, color: 'text-blue' }
  }

  const tiers = [
    { badge: 'tier-1', code: 'T1 CORE', engines: 'E01-E04 Gate', ...tierT1() },
    { badge: 'tier-2', code: 'T2 DIR',  engines: 'E05-E11 Direction', ...tierT2() },
    { badge: 'tier-3', code: 'T3 AMP',  engines: 'E12-E18 Amplifier', ...tierT3() },
    { badge: 'tier-4', code: 'T4 BIG',  engines: 'E19-E24 Big Money', ...tierT4() },
  ]

  // --- E09 Technical votes ---
  const techVotes = engines?.e09?.data?.votes || {}
  const techIndicators = ['ema', 'rsi', 'macd', 'supertrend']

  const voteLine = (v) => {
    if (!v) return { signal: '--', reading: '--', vote: '--', color: 'text-gray' }
    const bull = (v.signal || v.direction || '').toUpperCase().includes('BULL')
    return {
      signal: bull ? 'BULLISH \u25B2' : 'BEARISH \u25BC',
      reading: v.value ?? v.reading ?? '--',
      vote: bull ? '+1 CALL' : '+1 PUT',
      color: bull ? 'text-green' : 'text-red',
    }
  }

  // --- E06 PCR ---
  const pcr = engines?.e06?.data
  const pcrValue = pcr?.pcr ?? '--'
  const pcrBias = pcr?.bias ?? pcr?.reading ?? '--'
  const pcrBull = (pcrBias || '').toUpperCase().includes('BULL') || (pcrBias || '').toUpperCase().includes('CALL')
  const pcrSignalText = pcrBull ? 'CONTRARIAN CALL \u2191' : 'CONTRARIAN PUT \u2193'
  const pcrSignalColor = pcrBull ? 'text-green' : 'text-red'
  const pcrInterpretation = pcr?.interpretation ?? pcr?.note ?? ''

  // --- E07 Writer traps ---
  const traps = (engines?.e07?.data?.traps || []).slice(0, 5)

  // --- Signal data table ---
  const dataRows = [
    { label: 'INSTRUMENT', value: signal?.instrument ?? safe(signal, 'strike_info') },
    { label: 'ENTRY', value: signal?.entry ?? '--', color: 'text-white' },
    { label: 'STOP LOSS', value: signal?.stop_loss ?? signal?.sl ?? '--', color: 'text-red' },
    { label: 'TARGET 1', value: signal?.target1 ?? signal?.t1 ?? '--', color: 'text-green' },
    { label: 'TARGET 2', value: signal?.target2 ?? signal?.t2 ?? '--', color: 'text-green' },
    { label: 'CONFIDENCE', value: signal?.confidence ?? '--', color: 'text-white' },
    { label: 'IV GATE', value: safe(engines, 'e02.data.iv_status', safe(engines, 'e02.verdict', '--')), color: 'text-white' },
    { label: 'STRUCTURE', value: safe(engines, 'e03.data.structure', safe(engines, 'e03.verdict', '--')), color: 'text-white' },
    { label: 'MODE', value: signal?.mode ?? 'INTRADAY', color: 'text-amber' },
  ]

  return (
    <div className="flex h-full w-full font-mono">
      {/* ========== LEFT SIDE ========== */}
      <div className="w-[340px] min-w-[340px] border-r border-border overflow-y-auto">

        {/* Box 1: SIGNAL COMMAND */}
        <div className="p-3">
          <div className="panel-title">SIGNAL COMMAND</div>

          {signal ? (
            <>
              {/* Big signal type */}
              <div className={`text-[32px] font-bold tracking-[2px] mb-2 ${signalColor(signal.type)}`}>
                {(signal.type || 'SIGNAL').toUpperCase()}
              </div>

              {/* Strike line */}
              <div className="text-amber text-xs tracking-[1px] mb-3">
                {signal.strike_label || `NIFTY ${signal.strike || '--'} ${signal.option_type || 'CE'} \u00B7 WEEKLY`}
              </div>

              {/* Confluence score */}
              <div className="mb-3">
                <span className="text-gray text-[10px] tracking-[1px] mr-2">CONFLUENCE: {score} / {totalDots}</span>
                <span className="inline-flex items-center gap-0 mr-2">
                  {Array.from({ length: totalDots }).map((_, i) => (
                    <span
                      key={i}
                      className={`score-dot ${i < score ? 'filled' : 'empty'}`}
                      style={{ animationDelay: `${i * 100}ms` }}
                    />
                  ))}
                </span>
                <span className={`text-[10px] font-bold tracking-[1px] ${scoreLabel.color}`}>
                  {scoreLabel.text}
                </span>
              </div>

              {/* Data table */}
              <div className="mb-3">
                {dataRows.map((row) => (
                  <div key={row.label} className="flex justify-between py-[3px] text-[11px]">
                    <span className="text-gray">{row.label}</span>
                    <span className={row.color || 'text-white'}>{row.value}</span>
                  </div>
                ))}
              </div>

              {/* Footer */}
              <div className="text-gray text-[10px] italic leading-tight">
                STOP LOSS RULE: Maximum 15-20% of entry premium. Hard rule, no exceptions.
              </div>
            </>
          ) : (
            <div className="text-gray text-xs tracking-[2px] py-8 text-center">
              WAITING FOR CONFLUENCE...
            </div>
          )}
        </div>

        {/* Box 2: TIER VOTE STATUS */}
        <div className="p-3 border-t border-border">
          <div className="panel-title">TIER VOTE STATUS</div>

          {tiers.map((tier) => (
            <div key={tier.code} className="flex items-center gap-2 py-[5px]">
              <span className={`tier-badge ${tier.badge}`}>{tier.code}</span>
              <span className="text-gray text-[10px] flex-1">{tier.engines}</span>
              <span className={`text-[10px] font-bold ${tier.color}`}>{tier.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ========== RIGHT SIDE ========== */}
      <div className="flex-1 flex flex-col gap-0 overflow-y-auto">

        {/* Panel 1: TECHNICAL ENGINE E9 */}
        <div className="border-b border-border p-3">
          <div className="panel-title">TECHNICAL ENGINE &mdash; E9</div>

          <table className="w-full">
            <thead>
              <tr className="text-gray text-[10px] tracking-[1px] text-left">
                <th className="pb-1 font-normal">INDICATOR</th>
                <th className="pb-1 font-normal">SIGNAL</th>
                <th className="pb-1 font-normal">READING</th>
                <th className="pb-1 font-normal">VOTE</th>
              </tr>
            </thead>
            <tbody>
              {techIndicators.map((ind) => {
                const v = voteLine(techVotes[ind])
                return (
                  <tr key={ind} className="data-row text-[10px]">
                    <td className="py-[3px] text-white uppercase">{ind}</td>
                    <td className={`py-[3px] ${v.color}`}>{v.signal}</td>
                    <td className="py-[3px] text-white">{v.reading}</td>
                    <td className={`py-[3px] font-bold ${v.color}`}>{v.vote}</td>
                  </tr>
                )
              })}
              {!engines?.e09?.data?.votes && (
                <tr><td colSpan={4} className="text-gray text-[10px] py-3">Awaiting technical data...</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Panel 2: PCR FLOW ENGINE E6 */}
        <div className="border-b border-border p-3">
          <div className="panel-title">PCR FLOW ENGINE &mdash; E6</div>

          {pcr ? (
            <>
              <div className="flex items-center gap-3 text-[11px] mb-1">
                <span className="text-white">PCR: {pcrValue}</span>
                <span className="text-gray">|</span>
                <span className="text-amber">READING: {pcrBias}</span>
                <span className="text-gray">|</span>
                <span className={pcrSignalColor}>SIGNAL: {pcrSignalText}</span>
              </div>
              {pcrInterpretation && (
                <div className="text-amber-dim text-[10px] italic">{pcrInterpretation}</div>
              )}
            </>
          ) : (
            <div className="text-gray text-[10px] py-2">Awaiting PCR flow data...</div>
          )}
        </div>

        {/* Panel 3: WRITER TRAP FEED E7 */}
        <div className="p-3">
          <div className="panel-title">WRITER TRAP FEED &mdash; E7</div>

          {traps.length > 0 ? (
            <div className="flex flex-col gap-[2px]">
              {traps.map((trap, i) => (
                <div key={i} className="text-amber text-[10px] leading-snug">
                  <span className="text-gray mr-1">[{trap.timestamp || trap.time || '--:--'}]</span>
                  {trap.emoji || '\u26A0'} {trap.strike || ''} {trap.description || trap.text || ''}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray text-[10px]">No writer traps detected &mdash; monitoring...</div>
          )}
        </div>
      </div>
    </div>
  )
}
