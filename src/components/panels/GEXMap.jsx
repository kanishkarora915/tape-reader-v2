import Card from '../ui/Card'

function GEXBar({ strike, callGEX, putGEX, maxVal, spotPrice }) {
  const callPct = maxVal ? Math.min(Math.abs(callGEX) / maxVal * 100, 100) : 0
  const putPct = maxVal ? Math.min(Math.abs(putGEX) / maxVal * 100, 100) : 0
  const isSpot = strike === spotPrice

  return (
    <div className={`flex items-center gap-1 py-0.5 ${isSpot ? 'bg-neon-dim/20 rounded' : ''}`}>
      {/* Put (left) */}
      <div className="flex-1 flex justify-end">
        <div
          className="h-4 bg-bear/60 rounded-l transition-all duration-300"
          style={{ width: `${putPct}%`, minWidth: putPct > 0 ? '2px' : '0' }}
        />
      </div>
      {/* Strike label */}
      <div className={`w-16 text-center font-mono text-[10px] font-bold shrink-0 ${
        isSpot ? 'text-neon' : 'text-text-dim'
      }`}>
        {strike}
        {isSpot && <span className="text-[7px] ml-0.5 text-neon">SPOT</span>}
      </div>
      {/* Call (right) */}
      <div className="flex-1 flex justify-start">
        <div
          className="h-4 bg-bull/60 rounded-r transition-all duration-300"
          style={{ width: `${callPct}%`, minWidth: callPct > 0 ? '2px' : '0' }}
        />
      </div>
    </div>
  )
}

export default function GEXMap({ engines }) {
  const data = engines?.e05?.data
  const strikes = data?.strikes || []
  const spotPrice = data?.spotPrice || null
  const callWall = data?.callWall || null
  const putWall = data?.putWall || null

  const maxVal = strikes.reduce((mx, s) => Math.max(mx, Math.abs(s.callGEX || 0), Math.abs(s.putGEX || 0)), 1)

  const hasData = strikes.length > 0

  return (
    <Card title="GEX Exposure" icon="G" tier={2}>
      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-8 gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-purple animate-pulse" />
          <span className="text-text-dim text-[10px] uppercase tracking-wider">Awaiting GEX data...</span>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Legend */}
          <div className="flex items-center justify-between text-[9px] uppercase tracking-wider text-text-dim">
            <div className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-bear/60" />
              <span>Put Gamma</span>
            </div>
            <div className="flex items-center gap-1">
              <span>Call Gamma</span>
              <span className="w-2.5 h-2.5 rounded-sm bg-bull/60" />
            </div>
          </div>

          {/* Walls */}
          <div className="flex justify-between text-[10px]">
            {putWall && (
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-bear" />
                <span className="text-text-dim">Put Wall:</span>
                <span className="font-mono font-bold text-bear">{putWall}</span>
              </div>
            )}
            {callWall && (
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-bull" />
                <span className="text-text-dim">Call Wall:</span>
                <span className="font-mono font-bold text-bull">{callWall}</span>
              </div>
            )}
          </div>

          {/* Bars */}
          <div className="space-y-0.5 max-h-[280px] overflow-y-auto scrollbar-thin">
            {strikes.map((s, i) => (
              <GEXBar
                key={s.strike || i}
                strike={s.strike}
                callGEX={s.callGEX || 0}
                putGEX={s.putGEX || 0}
                maxVal={maxVal}
                spotPrice={spotPrice}
              />
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}
