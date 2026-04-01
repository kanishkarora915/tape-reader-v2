export default function GaugeChart({ value = 0, min = 0, max = 100, label, zones }) {
  const pct = Math.max(0, Math.min(1, (value - min) / (max - min)))
  const angle = -90 + pct * 180
  const defaultZones = [
    { end: 50, color: '#00e676' },
    { end: 70, color: '#ffab00' },
    { end: 100, color: '#ff3d71' },
  ]
  const z = zones || defaultZones

  let zoneColor = z[z.length - 1].color
  for (const zone of z) {
    if (value <= zone.end) { zoneColor = zone.color; break }
  }

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 120" className="w-full max-w-[180px]">
        {/* Background arc */}
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#1a2232" strokeWidth="12" strokeLinecap="round" />
        {/* Zone arcs */}
        {z.map((zone, i) => {
          const startPct = i === 0 ? 0 : z[i-1].end / max
          const endPct = zone.end / max
          const startAng = -Math.PI + startPct * Math.PI
          const endAng = -Math.PI + endPct * Math.PI
          const x1 = 100 + 80 * Math.cos(startAng), y1 = 100 + 80 * Math.sin(startAng)
          const x2 = 100 + 80 * Math.cos(endAng), y2 = 100 + 80 * Math.sin(endAng)
          const large = endPct - startPct > 0.5 ? 1 : 0
          return <path key={i} d={`M ${x1} ${y1} A 80 80 0 ${large} 1 ${x2} ${y2}`}
                       fill="none" stroke={zone.color} strokeWidth="12" strokeLinecap="round" opacity="0.3" />
        })}
        {/* Needle */}
        <line x1="100" y1="100"
              x2={100 + 60 * Math.cos((angle * Math.PI) / 180)}
              y2={100 + 60 * Math.sin((angle * Math.PI) / 180)}
              stroke={zoneColor} strokeWidth="3" strokeLinecap="round" />
        <circle cx="100" cy="100" r="5" fill={zoneColor} />
        {/* Value */}
        <text x="100" y="90" textAnchor="middle" fill={zoneColor}
              fontFamily="JetBrains Mono" fontSize="28" fontWeight="700">
          {Math.round(value)}
        </text>
      </svg>
      {label && <div className="text-[10px] tracking-[2px] text-text-dim uppercase mt-1">{label}</div>}
    </div>
  )
}
