import { useState } from 'react'
import Card from '../ui/Card'
import Badge from '../ui/Badge'

const TABS = ['NIFTY', 'BANKNIFTY', 'SENSEX']

function SkeletonRow() {
  return (
    <tr>
      {Array.from({ length: 9 }).map((_, i) => (
        <td key={i} className="px-2 py-2">
          <div className="h-3 bg-surface2 rounded animate-pulse" />
        </td>
      ))}
    </tr>
  )
}

function formatOI(val) {
  if (val == null) return '---'
  if (val >= 100000) return `${(val / 100000).toFixed(1)}L`
  if (val >= 1000) return `${(val / 1000).toFixed(1)}K`
  return val.toLocaleString()
}

function OIChangeCell({ value }) {
  if (value == null) return <span className="text-text-muted">---</span>
  const isPositive = value > 0
  return (
    <span className={`font-mono text-xs ${isPositive ? 'text-bull' : 'text-bear'}`}>
      {isPositive ? '+' : ''}{formatOI(value)}
    </span>
  )
}

export default function OIChainLive({ chain, engines }) {
  const [activeTab, setActiveTab] = useState('NIFTY')

  const data = chain?.[activeTab] || chain?.data || null
  const rows = data?.strikes || []
  const atmStrike = data?.atm || null
  const maxPain = data?.maxPain || engines?.e10?.data?.maxPain || null

  return (
    <Card title="OI Chain Live" icon="O" span={2} tier={1}>
      <div className="space-y-3">
        {/* Tabs */}
        <div className="flex gap-1">
          {TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1 text-[10px] font-bold tracking-wider rounded transition-colors ${
                activeTab === tab
                  ? 'bg-neon-dim text-neon border border-neon/30'
                  : 'bg-surface2 text-text-dim border border-border hover:border-border-bright'
              }`}
            >
              {tab}
            </button>
          ))}
          {maxPain && (
            <div className="ml-auto flex items-center gap-1.5">
              <span className="text-[9px] uppercase tracking-wider text-text-dim">Max Pain</span>
              <span className="font-mono text-xs font-bold text-warn">{maxPain}</span>
            </div>
          )}
        </div>

        {/* Table */}
        <div className="overflow-auto max-h-[480px] scrollbar-thin rounded-lg border border-border">
          <table className="w-full text-xs">
            <thead className="sticky top-0 z-10 bg-bg2">
              <tr className="text-[9px] uppercase tracking-wider text-text-dim">
                <th className="px-2 py-2 text-right font-semibold">CE OI</th>
                <th className="px-2 py-2 text-right font-semibold">CE Chg</th>
                <th className="px-2 py-2 text-right font-semibold">CE LTP</th>
                <th className="px-2 py-2 text-right font-semibold">CE IV</th>
                <th className="px-2 py-2 text-center font-semibold border-x border-border">Strike</th>
                <th className="px-2 py-2 text-left font-semibold">PE IV</th>
                <th className="px-2 py-2 text-left font-semibold">PE LTP</th>
                <th className="px-2 py-2 text-left font-semibold">PE Chg</th>
                <th className="px-2 py-2 text-left font-semibold">PE OI</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                Array.from({ length: 12 }).map((_, i) => <SkeletonRow key={i} />)
              ) : (
                rows.map((row, i) => {
                  const isATM = row.strike === atmStrike
                  const isMaxPain = row.strike === maxPain
                  return (
                    <tr
                      key={row.strike || i}
                      className={`border-b border-border/20 transition-colors hover:bg-surface2/50 ${
                        isATM ? 'bg-neon-dim/20 border-l-2 border-l-neon' : ''
                      } ${isMaxPain ? 'border-r-2 border-r-warn' : ''}`}
                    >
                      <td className="px-2 py-1.5 text-right font-mono text-text-dim">{formatOI(row.ceOI)}</td>
                      <td className="px-2 py-1.5 text-right"><OIChangeCell value={row.ceOIChg} /></td>
                      <td className="px-2 py-1.5 text-right font-mono text-text">{row.ceLTP ?? '---'}</td>
                      <td className="px-2 py-1.5 text-right font-mono text-text-dim">{row.ceIV ? `${row.ceIV}%` : '---'}</td>
                      <td className={`px-2 py-1.5 text-center font-mono font-bold border-x border-border/30 ${
                        isATM ? 'text-neon' : 'text-text'
                      }`}>
                        {row.strike}
                        {isATM && <span className="ml-1 text-[8px] text-neon">ATM</span>}
                      </td>
                      <td className="px-2 py-1.5 text-left font-mono text-text-dim">{row.peIV ? `${row.peIV}%` : '---'}</td>
                      <td className="px-2 py-1.5 text-left font-mono text-text">{row.peLTP ?? '---'}</td>
                      <td className="px-2 py-1.5 text-left"><OIChangeCell value={row.peOIChg} /></td>
                      <td className="px-2 py-1.5 text-left font-mono text-text-dim">{formatOI(row.peOI)}</td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  )
}
