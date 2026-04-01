import Card from '../ui/Card'
import Badge from '../ui/Badge'

const ENGINE_LIST = [
  { id: 'e01', name: 'OI Surge', tier: 1 },
  { id: 'e02', name: 'IV Gate', tier: 1 },
  { id: 'e03', name: 'Market Structure', tier: 1 },
  { id: 'e04', name: 'PCR Flow', tier: 1 },
  { id: 'e05', name: 'GEX Gamma', tier: 2 },
  { id: 'e06', name: 'OI Buildup', tier: 2 },
  { id: 'e07', name: 'Writer Trap', tier: 2 },
  { id: 'e08', name: 'VWAP Zone', tier: 2 },
  { id: 'e09', name: 'Technical Vote', tier: 2 },
  { id: 'e10', name: 'Expiry OI', tier: 2 },
  { id: 'e11', name: 'FII/DII Flow', tier: 3 },
  { id: 'e12', name: 'Volatility', tier: 3 },
  { id: 'e13', name: 'Order Flow', tier: 3 },
  { id: 'e14', name: 'Tape Speed', tier: 3 },
  { id: 'e15', name: 'Dark Pool', tier: 3 },
  { id: 'e16', name: 'Spread Track', tier: 3 },
  { id: 'e17', name: 'Multi-TF', tier: 3 },
  { id: 'e18', name: 'Stat Edge', tier: 3 },
  { id: 'e19', name: 'Breakout Scan', tier: 4 },
  { id: 'e20', name: 'Squeeze Detect', tier: 4 },
  { id: 'e21', name: 'Momentum Shift', tier: 4 },
  { id: 'e22', name: 'Reversal Trap', tier: 4 },
  { id: 'e23', name: 'Pre-Market', tier: 4 },
  { id: 'e24', name: 'AI Reason', tier: 4 },
]

const TIER_LABELS = { 1: 'T1', 2: 'T2', 3: 'T3', 4: 'T4' }
const TIER_DOT = { 1: 'bg-bear', 2: 'bg-warn', 3: 'bg-bull', 4: 'bg-purple' }

function LevelBox({ label, value, color }) {
  const colorMap = {
    green: 'border-bull/40 text-bull bg-bull-dim',
    red: 'border-bear/40 text-bear bg-bear-dim',
    neon: 'border-neon/40 text-neon bg-neon-dim',
  }
  return (
    <div className={`flex flex-col items-center px-3 py-2 rounded-lg border ${colorMap[color] || colorMap.neon}`}>
      <span className="text-[9px] uppercase tracking-wider text-text-dim">{label}</span>
      <span className="font-mono text-sm font-bold">{value ?? '---'}</span>
    </div>
  )
}

function ScoreBar({ score, max = 9 }) {
  const pct = Math.round((score / max) * 100)
  const color = pct >= 70 ? 'bg-bull' : pct >= 40 ? 'bg-warn' : 'bg-bear'
  return (
    <div className="flex items-center gap-2 w-full">
      <span className="font-mono text-lg font-bold text-text">{score}/{max}</span>
      <div className="flex-1 h-2 bg-bg2 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function SignalCommand({ signal, engines }) {
  const hasSignal = signal && signal.type && signal.type !== 'WAIT'

  if (!hasSignal) {
    return (
      <Card title="Signal Command" icon="S" span={2} accent="border-neon/30">
        <div className="flex flex-col items-center justify-center py-10 gap-3">
          <div className="w-3 h-3 rounded-full bg-neon animate-pulse" />
          <span className="text-text-dim text-sm tracking-wider uppercase">Analyzing... Waiting for confluence</span>
          <div className="flex gap-1 mt-2">
            {[1,2,3,4,5].map(i => (
              <div key={i} className="w-8 h-1 bg-surface2 rounded animate-pulse" style={{ animationDelay: `${i * 150}ms` }} />
            ))}
          </div>
        </div>
      </Card>
    )
  }

  const { type, instrument, strike, expiry, entry, sl, t1, t2, t3, score, riskReward, mode } = signal

  return (
    <Card title="Signal Command" icon="S" span={2} accent="border-neon/30">
      <div className="space-y-4">
        {/* Signal Type */}
        <div className="flex items-center justify-between">
          <Badge type={type} size="lg">{type?.replace(/_/g, ' ')}</Badge>
          {mode && (
            <Badge type={mode === 'VOLATILE' ? 'PARTIAL' : mode === 'SUDDEN' ? 'BEARISH' : 'NEUTRAL'} size="sm">
              {mode}
            </Badge>
          )}
        </div>

        {/* Instrument Info */}
        <div className="font-mono text-xl font-bold text-text tracking-wide">
          {instrument || 'NIFTY'} <span className="text-neon">{strike || '---'}</span>{' '}
          <span className="text-text-dim text-sm">{expiry || '---'}</span>
        </div>

        {/* Levels */}
        <div className="flex gap-2 flex-wrap">
          <LevelBox label="Entry" value={entry} color="neon" />
          <LevelBox label="SL" value={sl} color="red" />
          <LevelBox label="T1" value={t1} color="green" />
          <LevelBox label="T2" value={t2} color="green" />
          <LevelBox label="T3" value={t3} color="green" />
        </div>

        {/* Score + R:R */}
        <div className="flex items-center gap-6">
          <div className="flex-1">
            <div className="text-[9px] uppercase tracking-wider text-text-dim mb-1">Confluence Score</div>
            <ScoreBar score={score ?? 0} max={9} />
          </div>
          <div className="text-center">
            <div className="text-[9px] uppercase tracking-wider text-text-dim mb-1">Risk : Reward</div>
            <span className="font-mono text-lg font-bold text-neon">{riskReward || '---'}</span>
          </div>
        </div>

        {/* Engine Verdicts */}
        <div className="border-t border-border pt-3">
          <div className="text-[9px] uppercase tracking-[2px] text-text-dim mb-2">Engine Verdicts</div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 max-h-[260px] overflow-y-auto scrollbar-thin">
            {ENGINE_LIST.map(eng => {
              const engineData = engines?.[eng.id]
              const verdict = engineData?.verdict || 'NEUTRAL'
              return (
                <div key={eng.id} className="flex items-center justify-between py-1 border-b border-border/30">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${TIER_DOT[eng.tier]}`} />
                    <span className="text-[10px] text-text-dim">{eng.name}</span>
                  </div>
                  <Badge type={verdict} size="sm">{verdict}</Badge>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </Card>
  )
}
