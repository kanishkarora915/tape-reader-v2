import Card from '../ui/Card'
import Badge from '../ui/Badge'

function VWAPRow({ label, value, position, stretched }) {
  const posType = position === 'ABOVE' ? 'BULLISH' : position === 'BELOW' ? 'BEARISH' : 'NEUTRAL'

  return (
    <div className="flex items-center justify-between py-2.5 border-b border-border/20">
      <div className="flex flex-col">
        <span className="text-[9px] uppercase tracking-wider text-text-dim">{label}</span>
        <span className="font-mono text-lg font-bold text-text">{value ?? '---'}</span>
      </div>
      <div className="flex items-center gap-2">
        {stretched && (
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-warn-dim text-warn font-bold tracking-wider animate-pulse">
            SNAP
          </span>
        )}
        <Badge type={posType} size="sm">{position || '---'}</Badge>
      </div>
    </div>
  )
}

function BandRow({ label, upper, lower }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-[10px] text-text-dim">{label}</span>
      <div className="flex items-center gap-3 font-mono text-xs">
        <span className="text-bull">{upper ?? '---'}</span>
        <span className="text-text-muted">/</span>
        <span className="text-bear">{lower ?? '---'}</span>
      </div>
    </div>
  )
}

export default function VWAPBoard({ engines }) {
  const data = engines?.e08?.data
  const dVwap = data?.dVwap ?? null
  const wVwap = data?.wVwap ?? null
  const dPosition = data?.dPosition || null
  const wPosition = data?.wPosition || null
  const sd1Upper = data?.sd1Upper ?? null
  const sd1Lower = data?.sd1Lower ?? null
  const sd2Upper = data?.sd2Upper ?? null
  const sd2Lower = data?.sd2Lower ?? null
  const snapAlert = data?.snapAlert || false

  const hasData = dVwap !== null || wVwap !== null

  return (
    <Card title="VWAP Zones" icon="V" tier={2}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-neon animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">Awaiting VWAP data...</span>
        </div>
      ) : (
        <div className="space-y-3">
          <VWAPRow label="Daily VWAP" value={dVwap} position={dPosition} stretched={snapAlert} />
          <VWAPRow label="Weekly VWAP" value={wVwap} position={wPosition} />

          <div className="border-t border-border pt-2">
            <div className="text-[9px] uppercase tracking-[2px] text-text-dim mb-1">SD Bands (Upper / Lower)</div>
            <BandRow label="SD1" upper={sd1Upper} lower={sd1Lower} />
            <BandRow label="SD2" upper={sd2Upper} lower={sd2Lower} />
          </div>
        </div>
      )}
    </Card>
  )
}
