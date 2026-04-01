import Card from '../ui/Card'
import Badge from '../ui/Badge'

const BIAS_MAP = {
  'BULLISH GAP': 'BULLISH',
  'BEARISH GAP': 'BEARISH',
  'FLAT': 'NEUTRAL',
}

function CueRow({ region, value, change }) {
  const isPositive = change > 0
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border/20">
      <span className="text-[10px] text-text-dim">{region}</span>
      <div className="flex items-center gap-2">
        <span className="font-mono text-xs text-text">{value ?? '---'}</span>
        {change != null && (
          <span className={`font-mono text-[10px] font-bold ${isPositive ? 'text-bull' : 'text-bear'}`}>
            {isPositive ? '+' : ''}{change.toFixed(2)}%
          </span>
        )}
      </div>
    </div>
  )
}

export default function PreMarketBrief({ engines }) {
  const data = engines?.e23?.data
  const bias = data?.bias || null
  const giftNifty = data?.giftNifty ?? null
  const gapFillTarget = data?.gapFillTarget ?? null
  const globalCues = data?.globalCues || {}

  const hasData = bias !== null || giftNifty !== null

  return (
    <Card title="Pre-Market Brief" icon="P" tier={4}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-purple animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">Awaiting pre-market data...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Morning Bias */}
          <div className="flex items-center justify-center">
            <Badge type={BIAS_MAP[bias] || 'NEUTRAL'} size="lg">{bias || 'FLAT'}</Badge>
          </div>

          {/* Gift Nifty + Gap */}
          <div className="flex items-center justify-around">
            <div className="text-center">
              <div className="text-[9px] uppercase tracking-wider text-text-dim">Gift Nifty</div>
              <div className="font-mono text-xl font-bold text-neon">{giftNifty ?? '---'}</div>
            </div>
            {gapFillTarget && (
              <div className="text-center">
                <div className="text-[9px] uppercase tracking-wider text-text-dim">Gap Fill</div>
                <div className="font-mono text-xl font-bold text-warn">{gapFillTarget}</div>
              </div>
            )}
          </div>

          {/* Global Cues */}
          <div className="border-t border-border pt-3">
            <div className="text-[9px] uppercase tracking-[2px] text-text-dim mb-1">Global Cues</div>
            {globalCues.us && (
              <CueRow region="US (S&P 500)" value={globalCues.us.value} change={globalCues.us.change} />
            )}
            {globalCues.asia && (
              <CueRow region="Asia (Nikkei)" value={globalCues.asia.value} change={globalCues.asia.change} />
            )}
            {globalCues.europe && (
              <CueRow region="Europe (DAX)" value={globalCues.europe.value} change={globalCues.europe.change} />
            )}
            {!globalCues.us && !globalCues.asia && !globalCues.europe && (
              <div className="text-center text-[10px] text-text-muted py-2">No global cues available</div>
            )}
          </div>
        </div>
      )}
    </Card>
  )
}
