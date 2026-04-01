import Card from '../ui/Card'
import Badge from '../ui/Badge'

const T4_ENGINES = [
  { id: 'e19', name: 'Breakout Scanner', icon: '\u26A1' },
  { id: 'e20', name: 'Squeeze Detect', icon: '\u2B55' },
  { id: 'e21', name: 'Momentum Shift', icon: '\u21C5' },
  { id: 'e22', name: 'Reversal Trap', icon: '\u21BA' },
  { id: 'e23', name: 'Pre-Market Intel', icon: '\u2600' },
]

function RadarRow({ name, icon, data }) {
  const active = data?.active || false
  const alert = data?.alert || null
  const confidence = data?.confidence ?? null

  return (
    <div className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
      active ? 'bg-purple-dim/30 border border-purple/20' : 'bg-bg2/30'
    }`}>
      {/* Status Dot */}
      <div className="relative">
        <div className={`w-3 h-3 rounded-full ${active ? 'bg-purple' : 'bg-surface2'}`} />
        {active && (
          <div className="absolute inset-0 w-3 h-3 rounded-full bg-purple animate-ping opacity-40" />
        )}
      </div>

      {/* Icon + Name */}
      <span className="text-sm">{icon}</span>
      <span className={`text-[11px] font-semibold flex-1 ${active ? 'text-text' : 'text-text-dim'}`}>
        {name}
      </span>

      {/* Alert / Status */}
      {active && alert ? (
        <div className="flex items-center gap-2">
          {confidence != null && (
            <span className="font-mono text-[10px] text-purple">{confidence}%</span>
          )}
          <Badge type="BIG_MOVE" size="sm">{alert}</Badge>
        </div>
      ) : (
        <span className="text-[10px] text-text-muted uppercase tracking-wider">Inactive</span>
      )}
    </div>
  )
}

export default function BigMoveRadar({ engines, alerts }) {
  const activeCount = T4_ENGINES.filter(e => engines?.[e.id]?.data?.active).length
  const activeAlerts = alerts?.bigMove || []

  return (
    <Card title="Big Move Radar" icon="R" tier={4}>
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${activeCount > 0 ? 'bg-purple animate-pulse' : 'bg-surface2'}`} />
            <span className="text-[10px] text-text-dim uppercase tracking-wider">
              {activeCount} / {T4_ENGINES.length} Active
            </span>
          </div>
          {activeCount > 0 && (
            <Badge type="BIG_MOVE" size="sm">ALERT</Badge>
          )}
        </div>

        {/* Engine Rows */}
        <div className="space-y-1.5">
          {T4_ENGINES.map(eng => (
            <RadarRow
              key={eng.id}
              name={eng.name}
              icon={eng.icon}
              data={engines?.[eng.id]?.data}
            />
          ))}
        </div>

        {/* Active Alerts Feed */}
        {activeAlerts.length > 0 && (
          <div className="border-t border-border pt-2">
            <div className="text-[9px] uppercase tracking-[2px] text-text-dim mb-1">Live Alerts</div>
            <div className="space-y-1 max-h-[80px] overflow-y-auto scrollbar-thin">
              {activeAlerts.slice(0, 5).map((a, i) => (
                <div key={i} className="flex items-center gap-2 text-[10px]">
                  <span className="font-mono text-text-dim">{a.time || '--:--'}</span>
                  <span className="text-purple font-bold">{a.message || a}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}
