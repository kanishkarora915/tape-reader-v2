export default function Card({ title, icon, tier, accent, span, children, className = '' }) {
  const tierColors = {
    1: 'border-bear/20',
    2: 'border-warn/20',
    3: 'border-bull/20',
    4: 'border-purple/20',
  }
  const tierLabels = { 1: 'T1', 2: 'T2', 3: 'T3', 4: 'T4' }
  const tierBg = {
    1: 'bg-bear-dim text-bear',
    2: 'bg-warn-dim text-warn',
    3: 'bg-bull-dim text-bull',
    4: 'bg-purple-dim text-purple',
  }

  const borderClass = accent || (tier ? tierColors[tier] : 'border-border')
  const spanClass = span === 2 ? 'col-span-2' : span === 4 ? 'col-span-4' : ''

  return (
    <div className={`bg-surface border ${borderClass} rounded-xl overflow-hidden flex flex-col ${spanClass} ${className}`}>
      {title && (
        <div className="flex items-center justify-between px-4 py-2.5 bg-bg2 border-b border-border">
          <div className="flex items-center gap-2">
            {icon && <span className="text-text-dim text-sm">{icon}</span>}
            <span className="text-[11px] font-semibold tracking-[2px] text-text-dim uppercase">{title}</span>
          </div>
          {tier && (
            <span className={`text-[9px] font-bold tracking-wider px-1.5 py-0.5 rounded ${tierBg[tier]}`}>
              {tierLabels[tier]}
            </span>
          )}
        </div>
      )}
      <div className="flex-1 p-4">
        {children}
      </div>
    </div>
  )
}
