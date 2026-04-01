import Card from '../ui/Card'
import Badge from '../ui/Badge'

function FlowBar({ buy, sell, label }) {
  const total = (buy || 0) + (sell || 0)
  const buyPct = total > 0 ? (buy / total) * 100 : 50

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px]">
        <span className="text-bull font-mono">Buy: {buy != null ? `${buy.toLocaleString()} Cr` : '---'}</span>
        <span className="text-bear font-mono">Sell: {sell != null ? `${sell.toLocaleString()} Cr` : '---'}</span>
      </div>
      <div className="flex h-3 rounded-full overflow-hidden bg-bg2">
        <div className="h-full bg-bull/60 transition-all duration-500" style={{ width: `${buyPct}%` }} />
        <div className="h-full bg-bear/60 transition-all duration-500" style={{ width: `${100 - buyPct}%` }} />
      </div>
    </div>
  )
}

function TrendArrow({ trend }) {
  if (!trend || trend.length === 0) return <span className="text-text-muted">---</span>
  return (
    <div className="flex items-center gap-0.5">
      {trend.map((val, i) => {
        const isUp = val > 0
        return (
          <span key={i} className={`text-xs ${isUp ? 'text-bull' : 'text-bear'}`}>
            {isUp ? '\u25B2' : '\u25BC'}
          </span>
        )
      })}
    </div>
  )
}

export default function FIIDIIBoard({ engines }) {
  const data = engines?.e11?.data
  const fiiNet = data?.fiiNet ?? null
  const fiiBuy = data?.fiiBuy ?? null
  const fiiSell = data?.fiiSell ?? null
  const fiiTrend = data?.fiiTrend || []
  const diiCash = data?.diiCash ?? null
  const diiBuy = data?.diiBuy ?? null
  const diiSell = data?.diiSell ?? null

  const hasData = fiiNet !== null || diiCash !== null

  const fiiDirection = fiiNet > 0 ? 'BULLISH' : fiiNet < 0 ? 'BEARISH' : 'NEUTRAL'

  return (
    <Card title="FII / DII Flow" icon="F" tier={3}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-purple animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">Awaiting FII/DII data...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {/* FII Section */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[9px] uppercase tracking-[2px] text-text-dim font-semibold">FII Futures</span>
              <div className="flex items-center gap-2">
                <TrendArrow trend={fiiTrend} />
                <Badge type={fiiDirection} size="sm">
                  {fiiNet != null ? `${fiiNet > 0 ? '+' : ''}${fiiNet.toLocaleString()} Cr` : '---'}
                </Badge>
              </div>
            </div>
            <FlowBar buy={fiiBuy} sell={fiiSell} />
          </div>

          {/* DII Section */}
          <div className="border-t border-border pt-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[9px] uppercase tracking-[2px] text-text-dim font-semibold">DII Cash</span>
              <span className="font-mono text-sm font-bold text-text">
                {diiCash != null ? `${diiCash > 0 ? '+' : ''}${diiCash.toLocaleString()} Cr` : '---'}
              </span>
            </div>
            <FlowBar buy={diiBuy} sell={diiSell} />
          </div>
        </div>
      )}
    </Card>
  )
}
