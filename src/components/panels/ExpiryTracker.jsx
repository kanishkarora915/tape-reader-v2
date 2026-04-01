import Card from '../ui/Card'
import Badge from '../ui/Badge'

function DaysCircle({ days }) {
  const color = days <= 1 ? 'text-bear' : days <= 3 ? 'text-warn' : 'text-neon'
  const ringColor = days <= 1 ? 'border-bear/40' : days <= 3 ? 'border-warn/40' : 'border-neon/40'

  return (
    <div className={`w-20 h-20 rounded-full border-2 ${ringColor} flex flex-col items-center justify-center`}>
      <span className={`font-mono text-3xl font-bold ${color}`}>{days ?? '--'}</span>
      <span className="text-[8px] uppercase tracking-wider text-text-dim">Days</span>
    </div>
  )
}

export default function ExpiryTracker({ engines }) {
  const data = engines?.e10?.data
  const daysToExpiry = data?.daysToExpiry ?? null
  const maxPain = data?.maxPain ?? null
  const oiDrift = data?.oiDrift || null
  const weeklyOI = data?.weeklyOI ?? null
  const monthlyOI = data?.monthlyOI ?? null

  const hasData = daysToExpiry !== null

  const driftArrow = oiDrift === 'UP' ? '\u2191' : oiDrift === 'DOWN' ? '\u2193' : '\u2194'
  const driftType = oiDrift === 'UP' ? 'BULLISH' : oiDrift === 'DOWN' ? 'BEARISH' : 'NEUTRAL'

  return (
    <Card title="Expiry Tracker" icon="E" tier={2}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-neon animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">Awaiting expiry data...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Days + Max Pain */}
          <div className="flex items-center justify-around">
            <DaysCircle days={daysToExpiry} />
            <div className="text-center">
              <div className="text-[9px] uppercase tracking-wider text-text-dim">Max Pain</div>
              <div className="font-mono text-xl font-bold text-warn">{maxPain ?? '---'}</div>
            </div>
          </div>

          {/* OI Drift */}
          <div className="flex items-center justify-center gap-2">
            <span className="text-[9px] uppercase tracking-wider text-text-dim">OI Drift</span>
            <Badge type={driftType} size="md">
              {driftArrow} {oiDrift || 'FLAT'}
            </Badge>
          </div>

          {/* Weekly vs Monthly */}
          {(weeklyOI != null || monthlyOI != null) && (
            <div className="border-t border-border pt-3">
              <div className="text-[9px] uppercase tracking-[2px] text-text-dim mb-2">OI Distribution</div>
              <div className="flex gap-4">
                <div className="flex-1">
                  <div className="text-[10px] text-text-dim mb-1">Weekly</div>
                  <div className="h-3 bg-bg2 rounded-full overflow-hidden">
                    <div className="h-full bg-neon/60 rounded-full" style={{
                      width: `${weeklyOI && monthlyOI ? (weeklyOI / (weeklyOI + monthlyOI)) * 100 : 50}%`
                    }} />
                  </div>
                  <div className="font-mono text-xs text-text mt-0.5">{weeklyOI != null ? weeklyOI.toLocaleString() : '---'}</div>
                </div>
                <div className="flex-1">
                  <div className="text-[10px] text-text-dim mb-1">Monthly</div>
                  <div className="h-3 bg-bg2 rounded-full overflow-hidden">
                    <div className="h-full bg-purple/60 rounded-full" style={{
                      width: `${weeklyOI && monthlyOI ? (monthlyOI / (weeklyOI + monthlyOI)) * 100 : 50}%`
                    }} />
                  </div>
                  <div className="font-mono text-xs text-text mt-0.5">{monthlyOI != null ? monthlyOI.toLocaleString() : '---'}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
