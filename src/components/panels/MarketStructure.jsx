import Card from '../ui/Card'
import Badge from '../ui/Badge'

const REGIME_BADGE = {
  UPTREND: 'BULLISH',
  DOWNTREND: 'BEARISH',
  RANGE: 'NEUTRAL',
  BOS: 'BULLISH',
  CHoCH: 'BEARISH',
}

function LevelRow({ label, value, type }) {
  const color = type === 'support' ? 'text-bull' : type === 'resistance' ? 'text-bear' : 'text-purple'
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border/20">
      <span className="text-[10px] uppercase tracking-wider text-text-dim">{label}</span>
      <span className={`font-mono text-sm font-bold ${color}`}>{value ?? '---'}</span>
    </div>
  )
}

function TimelineEvent({ event }) {
  const color = event.type === 'BOS' ? 'bg-bull' : event.type === 'CHoCH' ? 'bg-bear' : 'bg-neon'
  return (
    <div className="flex items-start gap-2 py-1.5">
      <div className="flex flex-col items-center mt-1">
        <div className={`w-2 h-2 rounded-full ${color}`} />
        <div className="w-px h-full bg-border/30" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-text-dim">{event.time || '--:--'}</span>
          <Badge type={REGIME_BADGE[event.type] || 'NEUTRAL'} size="sm">{event.type}</Badge>
        </div>
        <span className="text-[10px] text-text-dim">{event.detail || ''}</span>
      </div>
    </div>
  )
}

export default function MarketStructure({ engines }) {
  const data = engines?.e03?.data
  const regime = data?.regime || null
  const support = data?.support ?? null
  const resistance = data?.resistance ?? null
  const orderBlock = data?.orderBlock ?? null
  const events = data?.events || []

  const hasData = regime !== null

  return (
    <Card title="Market Structure" icon="M" tier={1}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-neon animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">Awaiting structure data...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Regime */}
          <div className="flex items-center justify-center">
            <Badge type={REGIME_BADGE[regime] || 'NEUTRAL'} size="lg">
              {regime}
            </Badge>
          </div>

          {/* Key Levels */}
          <div>
            <div className="text-[9px] uppercase tracking-[2px] text-text-dim mb-1">Key Levels</div>
            <LevelRow label="Support" value={support} type="support" />
            <LevelRow label="Resistance" value={resistance} type="resistance" />
            <LevelRow label="Order Block" value={orderBlock} type="ob" />
          </div>

          {/* Timeline */}
          {events.length > 0 && (
            <div>
              <div className="text-[9px] uppercase tracking-[2px] text-text-dim mb-1">Recent Events</div>
              <div className="max-h-[140px] overflow-y-auto scrollbar-thin space-y-0.5">
                {events.slice(0, 8).map((evt, i) => (
                  <TimelineEvent key={i} event={evt} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
