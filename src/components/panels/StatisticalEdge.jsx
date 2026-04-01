import Card from '../ui/Card'
import Badge from '../ui/Badge'

function WinRateCircle({ rate }) {
  const color = rate >= 60 ? 'text-bull' : rate >= 40 ? 'text-warn' : 'text-bear'
  const ringColor = rate >= 60 ? 'border-bull/40' : rate >= 40 ? 'border-warn/40' : 'border-bear/40'
  const bgColor = rate >= 60 ? 'bg-bull-dim' : rate >= 40 ? 'bg-warn-dim' : 'bg-bear-dim'

  return (
    <div className={`w-20 h-20 rounded-full border-2 ${ringColor} ${bgColor} flex flex-col items-center justify-center`}>
      <span className={`font-mono text-2xl font-bold ${color}`}>{rate}%</span>
      <span className="text-[7px] uppercase tracking-wider text-text-dim">Win Rate</span>
    </div>
  )
}

function StatRow({ label, value, sub }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border/20">
      <span className="text-[10px] text-text-dim uppercase tracking-wider">{label}</span>
      <div className="text-right">
        <span className="font-mono text-sm font-bold text-text">{value ?? '---'}</span>
        {sub && <div className="text-[9px] text-text-muted">{sub}</div>}
      </div>
    </div>
  )
}

function PatternBar({ matchPct }) {
  const pct = Math.max(0, Math.min(100, matchPct || 0))
  const color = pct >= 70 ? 'bg-bull' : pct >= 40 ? 'bg-warn' : 'bg-bear'

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px]">
        <span className="text-text-dim">Pattern Match</span>
        <span className="font-mono text-text">{pct}%</span>
      </div>
      <div className="h-2 bg-bg2 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function StatisticalEdge({ engines }) {
  const data = engines?.e18?.data
  const winRate = data?.winRate ?? null
  const monteCarloScore = data?.monteCarloScore ?? null
  const similarSetups = data?.similarSetups ?? null
  const patternMatch = data?.patternMatch ?? null

  const hasData = winRate !== null

  return (
    <Card title="Statistical Edge" icon="#" tier={3}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-bull animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">Awaiting stat data...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Win Rate */}
          <div className="flex items-center justify-center">
            <WinRateCircle rate={winRate} />
          </div>

          {/* Stats */}
          <StatRow label="Monte Carlo" value={monteCarloScore} sub="confidence score" />
          <StatRow label="Similar Setups" value={similarSetups} sub="past matches" />

          {/* Pattern Match Bar */}
          {patternMatch != null && <PatternBar matchPct={patternMatch} />}
        </div>
      )}
    </Card>
  )
}
