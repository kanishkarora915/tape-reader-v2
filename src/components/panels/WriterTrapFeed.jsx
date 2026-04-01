import Card from '../ui/Card'
import Badge from '../ui/Badge'

function TrapItem({ item }) {
  const isCallTrap = item.side === 'Call'
  const accentColor = isCallTrap ? 'border-l-bull' : 'border-l-bear'
  const sideType = isCallTrap ? 'BULLISH' : 'BEARISH'

  return (
    <div className={`flex items-center gap-3 px-3 py-2 bg-bg2/50 rounded-lg border-l-2 ${accentColor}`}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-text-dim">{item.timestamp || '--:--:--'}</span>
          <Badge type={sideType} size="sm">{item.side} Trap</Badge>
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className="font-mono text-sm font-bold text-text">{item.strike || '---'}</span>
          <span className="text-[10px] text-text-dim">
            OI Drop: <span className={`font-mono font-bold ${isCallTrap ? 'text-bull' : 'text-bear'}`}>
              {item.oiDrop != null ? `-${item.oiDrop.toLocaleString()}` : '---'}
            </span>
          </span>
          <span className="text-[10px] text-text-dim">
            Prem: <span className="font-mono font-bold text-warn">
              {item.premiumSpike != null ? `+${item.premiumSpike}%` : '---'}
            </span>
          </span>
        </div>
      </div>
    </div>
  )
}

export default function WriterTrapFeed({ engines, alerts }) {
  const data = engines?.e07?.data
  const traps = data?.traps || alerts?.writerTraps || []

  const hasData = traps.length > 0

  return (
    <Card title="Writer Trap Feed" icon="W" tier={2}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-warn animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">No traps detected</span>
        </div>
      ) : (
        <div className="space-y-1.5 max-h-[320px] overflow-y-auto scrollbar-thin">
          {traps.map((trap, i) => (
            <TrapItem key={i} item={trap} />
          ))}
        </div>
      )}
    </Card>
  )
}
