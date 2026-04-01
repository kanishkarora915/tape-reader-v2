import Card from '../ui/Card'
import Badge from '../ui/Badge'

const SQUEEZE_MAP = {
  COMPRESSED: { label: 'COMPRESSED', type: 'BEARISH', color: 'bg-bear' },
  NORMAL: { label: 'NORMAL', type: 'NEUTRAL', color: 'bg-text-dim' },
  EXPANDING: { label: 'EXPANDING', type: 'BULLISH', color: 'bg-bull' },
}

function MiniSparkline({ values = [] }) {
  if (values.length < 2) return null
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const w = 120
  const h = 30
  const step = w / (values.length - 1)

  const points = values.map((v, i) => `${i * step},${h - ((v - min) / range) * h}`).join(' ')

  return (
    <svg width={w} height={h} className="opacity-60">
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.5" className="text-warn" />
    </svg>
  )
}

export default function VolatilityPanel({ engines }) {
  const data = engines?.e12?.data
  const vix = data?.vix ?? null
  const vixHistory = data?.vixHistory || []
  const bbSqueeze = data?.bbSqueeze || null
  const atrRatio = data?.atrRatio ?? null
  const volatileMode = data?.volatileMode || false

  const hasData = vix !== null

  const squeezeInfo = SQUEEZE_MAP[bbSqueeze] || SQUEEZE_MAP.NORMAL

  return (
    <Card title="Volatility" icon="\u03C3" tier={3}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-warn animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">Awaiting volatility data...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {/* VIX */}
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[9px] uppercase tracking-wider text-text-dim">India VIX</div>
              <div className="font-mono text-2xl font-bold text-warn">{vix?.toFixed(2) ?? '---'}</div>
            </div>
            <MiniSparkline values={vixHistory} />
          </div>

          {/* Volatile Mode */}
          {volatileMode && (
            <div className="flex items-center justify-center">
              <Badge type="PARTIAL" size="md">VOLATILE MODE ACTIVE</Badge>
            </div>
          )}

          {/* BB Squeeze */}
          <div className="flex items-center justify-between py-2.5 border-t border-border">
            <div>
              <div className="text-[9px] uppercase tracking-wider text-text-dim">BB Squeeze</div>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex gap-0.5">
                  {[1,2,3].map(i => (
                    <div key={i} className={`w-2 h-6 rounded-sm transition-all duration-300 ${
                      bbSqueeze === 'COMPRESSED' ? 'bg-bear' :
                      bbSqueeze === 'EXPANDING' ? 'bg-bull' : 'bg-text-dim/30'
                    }`} style={{
                      height: bbSqueeze === 'COMPRESSED' ? '12px' :
                              bbSqueeze === 'EXPANDING' ? `${12 + i * 5}px` : '16px'
                    }} />
                  ))}
                </div>
              </div>
            </div>
            <Badge type={squeezeInfo.type} size="sm">{squeezeInfo.label}</Badge>
          </div>

          {/* ATR Ratio */}
          <div className="flex items-center justify-between py-2.5 border-t border-border">
            <span className="text-[9px] uppercase tracking-wider text-text-dim">ATR Ratio</span>
            <span className="font-mono text-sm font-bold text-text">{atrRatio?.toFixed(2) ?? '---'}</span>
          </div>
        </div>
      )}
    </Card>
  )
}
