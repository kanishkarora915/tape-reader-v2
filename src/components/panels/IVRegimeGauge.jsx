import Card from '../ui/Card'
import Badge from '../ui/Badge'
import GaugeChart from '../ui/GaugeChart'

const GATE_STYLES = {
  OPEN: 'PASS',
  PARTIAL: 'PARTIAL',
  BLOCKED: 'FAIL',
}

export default function IVRegimeGauge({ engines }) {
  const data = engines?.e02?.data
  const ivr = data?.ivr ?? null
  const gateStatus = data?.gateStatus || 'OPEN'
  const callIV = data?.callIV ?? null
  const putIV = data?.putIV ?? null
  const ivSkew = data?.ivSkew ?? null

  const hasData = ivr !== null

  const zones = [
    { end: 50, color: '#00e676' },
    { end: 70, color: '#ffab00' },
    { end: 100, color: '#ff3d71' },
  ]

  return (
    <Card title="IV Regime Gate" icon="IV" tier={1}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-warn animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">Awaiting IV data...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Gauge */}
          <GaugeChart value={ivr} min={0} max={100} label="IV Rank" zones={zones} />

          {/* Gate Status */}
          <div className="flex items-center justify-center gap-2">
            <span className="text-[9px] uppercase tracking-wider text-text-dim">Gate:</span>
            <Badge type={GATE_STYLES[gateStatus] || 'NEUTRAL'} size="md">{gateStatus}</Badge>
          </div>

          {/* IV Skew */}
          {(callIV !== null || putIV !== null) && (
            <div className="border-t border-border pt-3 space-y-2">
              <div className="text-[9px] uppercase tracking-[2px] text-text-dim">IV Skew</div>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-bull">Call IV</span>
                    <span className="font-mono text-bull">{callIV != null ? `${callIV}%` : '---'}</span>
                  </div>
                  <div className="h-2 bg-bg2 rounded-full overflow-hidden">
                    <div className="h-full bg-bull/60 rounded-full" style={{ width: `${Math.min((callIV || 0), 100)}%` }} />
                  </div>
                </div>
                <span className="text-text-dim text-[10px]">vs</span>
                <div className="flex-1">
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-bear">Put IV</span>
                    <span className="font-mono text-bear">{putIV != null ? `${putIV}%` : '---'}</span>
                  </div>
                  <div className="h-2 bg-bg2 rounded-full overflow-hidden">
                    <div className="h-full bg-bear/60 rounded-full" style={{ width: `${Math.min((putIV || 0), 100)}%` }} />
                  </div>
                </div>
              </div>
              {ivSkew != null && (
                <div className="text-center text-[10px] text-text-dim">
                  Skew: <span className="font-mono font-bold text-text">{ivSkew > 0 ? '+' : ''}{ivSkew.toFixed(2)}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
