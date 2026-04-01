const styles = {
  BUY_CALL:       'bg-bull-dim text-bull border-bull/30',
  STRONG_BUY_CALL:'bg-bull-dim text-bull border-bull/30',
  BUY_PUT:        'bg-bear-dim text-bear border-bear/30',
  STRONG_BUY_PUT: 'bg-bear-dim text-bear border-bear/30',
  BIG_MOVE:       'bg-purple-dim text-purple border-purple/30',
  VOLATILE_BUY:   'bg-warn-dim text-warn border-warn/30',
  HARD_BLOCK:     'bg-bear-dim text-bear border-bear/30',
  SKIP:           'bg-surface2 text-text-dim border-border',
  WAIT:           'bg-surface2 text-text-dim border-border',
  PASS:           'bg-bull-dim text-bull border-bull/30',
  FAIL:           'bg-bear-dim text-bear border-bear/30',
  NEUTRAL:        'bg-surface2 text-text-dim border-border',
  PARTIAL:        'bg-warn-dim text-warn border-warn/30',
  BULLISH:        'bg-bull-dim text-bull border-bull/30',
  BEARISH:        'bg-bear-dim text-bear border-bear/30',
}

export default function Badge({ type, size = 'sm', children }) {
  const cls = styles[type] || styles.NEUTRAL
  const sz = size === 'lg' ? 'text-sm px-4 py-1.5' : size === 'md' ? 'text-xs px-3 py-1' : 'text-[10px] px-2 py-0.5'
  return (
    <span className={`inline-flex items-center font-bold tracking-wider rounded border ${cls} ${sz}`}>
      {children || type}
    </span>
  )
}
