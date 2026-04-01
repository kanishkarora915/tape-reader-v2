import Card from '../ui/Card'
import Badge from '../ui/Badge'

function Section({ title, children }) {
  return (
    <div className="space-y-1.5">
      <div className="text-[9px] uppercase tracking-[2px] text-purple font-semibold">{title}</div>
      <div className="text-[11px] text-text-dim leading-relaxed">{children}</div>
    </div>
  )
}

function ConfidenceBar({ score }) {
  const pct = Math.max(0, Math.min(100, score || 0))
  const color = pct >= 70 ? 'bg-bull' : pct >= 40 ? 'bg-warn' : 'bg-bear'

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px]">
        <span className="text-text-dim">Confidence</span>
        <span className="font-mono font-bold text-text">{pct}%</span>
      </div>
      <div className="h-2.5 bg-bg2 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function LevelChip({ label, value, type }) {
  const colorMap = {
    entry: 'bg-neon-dim text-neon border-neon/30',
    sl: 'bg-bear-dim text-bear border-bear/30',
    target: 'bg-bull-dim text-bull border-bull/30',
  }
  return (
    <div className={`flex flex-col items-center px-4 py-2 rounded-lg border ${colorMap[type] || colorMap.entry}`}>
      <span className="text-[8px] uppercase tracking-wider opacity-70">{label}</span>
      <span className="font-mono text-sm font-bold">{value ?? '---'}</span>
    </div>
  )
}

export default function AITradeCard({ engines, signal }) {
  const data = engines?.e24?.data
  const analysis = data?.analysis || null
  const rationale = data?.rationale || analysis?.rationale || null
  const riskFactors = data?.riskFactors || analysis?.riskFactors || null
  const confidenceAssessment = data?.confidenceAssessment || analysis?.confidenceAssessment || null
  const confidence = data?.confidence ?? analysis?.confidence ?? null
  const entry = data?.entry ?? signal?.entry ?? null
  const sl = data?.sl ?? signal?.sl ?? null
  const t1 = data?.t1 ?? signal?.t1 ?? null
  const t2 = data?.t2 ?? signal?.t2 ?? null

  const hasAnalysis = rationale || riskFactors || confidenceAssessment

  return (
    <Card title="BuyBy AI Reasoning" icon="\u2728" span={4} accent="border-purple/30">
      {!hasAnalysis ? (
        <div className="flex flex-col items-center justify-center py-12 gap-4">
          <div className="relative">
            <div className="w-6 h-6 rounded-full bg-purple/20 animate-pulse" />
            <div className="absolute inset-0 w-6 h-6 rounded-full bg-purple/10 animate-ping" />
          </div>
          <div className="text-center">
            <div className="text-text-dim text-sm tracking-wider">AI engine will analyze when signal fires</div>
            <div className="text-text-muted text-[10px] mt-1">Powered by Claude | BuyBy AI Layer</div>
          </div>
        </div>
      ) : (
        <div className="space-y-5">
          {/* Header accent */}
          <div className="h-0.5 w-full bg-gradient-to-r from-purple via-neon to-purple opacity-40 rounded-full" />

          {/* Sections Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {rationale && (
              <Section title="Trade Rationale">
                {typeof rationale === 'string' ? rationale : JSON.stringify(rationale)}
              </Section>
            )}
            {riskFactors && (
              <Section title="Risk Factors">
                {Array.isArray(riskFactors) ? (
                  <ul className="list-disc list-inside space-y-0.5">
                    {riskFactors.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                ) : (
                  typeof riskFactors === 'string' ? riskFactors : JSON.stringify(riskFactors)
                )}
              </Section>
            )}
            {confidenceAssessment && (
              <Section title="Confidence Assessment">
                {typeof confidenceAssessment === 'string' ? confidenceAssessment : JSON.stringify(confidenceAssessment)}
              </Section>
            )}
          </div>

          {/* Confidence Bar */}
          {confidence != null && <ConfidenceBar score={confidence} />}

          {/* Bottom: Entry / SL / Targets */}
          <div className="border-t border-border pt-4">
            <div className="flex flex-wrap items-center justify-center gap-3">
              <LevelChip label="Entry" value={entry} type="entry" />
              <LevelChip label="Stop Loss" value={sl} type="sl" />
              <LevelChip label="Target 1" value={t1} type="target" />
              <LevelChip label="Target 2" value={t2} type="target" />
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}
