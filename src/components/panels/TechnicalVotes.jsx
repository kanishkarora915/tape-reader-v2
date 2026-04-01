import Card from '../ui/Card'
import Badge from '../ui/Badge'

const INDICATORS = [
  { key: 'ema', label: 'EMA Cross' },
  { key: 'rsi', label: 'RSI' },
  { key: 'macd', label: 'MACD' },
  { key: 'supertrend', label: 'Supertrend' },
]

function IndicatorRow({ label, value, vote }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-border/20">
      <span className="text-[11px] font-semibold text-text-dim uppercase tracking-wider">{label}</span>
      <div className="flex items-center gap-3">
        <span className="font-mono text-sm text-text">{value ?? '---'}</span>
        <Badge type={vote || 'NEUTRAL'} size="sm">{vote || 'NEUTRAL'}</Badge>
      </div>
    </div>
  )
}

export default function TechnicalVotes({ engines }) {
  const data = engines?.e09?.data
  const indicators = data?.indicators || {}

  const hasData = Object.keys(indicators).length > 0

  const votes = INDICATORS.map(ind => ({
    ...ind,
    value: indicators[ind.key]?.value ?? null,
    vote: indicators[ind.key]?.vote || 'NEUTRAL',
  }))

  const bullCount = votes.filter(v => v.vote === 'BULLISH').length
  const bearCount = votes.filter(v => v.vote === 'BEARISH').length
  const summaryText = bullCount >= bearCount
    ? `${bullCount}/4 BULLISH`
    : `${bearCount}/4 BEARISH`
  const summaryType = bullCount > bearCount ? 'BULLISH' : bearCount > bullCount ? 'BEARISH' : 'NEUTRAL'

  return (
    <Card title="Technical Votes" icon="T" tier={2}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-bull animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">Awaiting technical data...</span>
        </div>
      ) : (
        <div className="space-y-1">
          {votes.map(v => (
            <IndicatorRow key={v.key} label={v.label} value={v.value} vote={v.vote} />
          ))}

          {/* Summary */}
          <div className="flex items-center justify-center pt-3">
            <Badge type={summaryType} size="md">{summaryText}</Badge>
          </div>
        </div>
      )}
    </Card>
  )
}
