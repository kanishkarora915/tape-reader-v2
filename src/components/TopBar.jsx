import { useState, useEffect } from 'react'

const fmt = (n) => {
  if (n == null) return '--'
  return Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const fmtInt = (n) => {
  if (n == null) return '--'
  return Number(n).toLocaleString('en-IN')
}

const changeColor = (val) => {
  if (val == null) return 'text-[#E8E8E8]'
  return Number(val) >= 0 ? 'text-[#00C853]' : 'text-[#FF3D00]'
}

const sign = (val) => (Number(val) >= 0 ? '+' : '')

function Ticker({ label, data }) {
  if (!data) {
    return (
      <span className="flex items-center gap-1 font-mono">
        <span className="text-[#444444] text-[10px]">{label}</span>
        <span className="text-[#E8E8E8] text-xs font-bold">--</span>
      </span>
    )
  }
  const { ltp, change, changePct } = data
  return (
    <span className="flex items-center gap-1 font-mono">
      <span className="text-[#444444] text-[10px]">{label}</span>
      <span className="text-[#E8E8E8] text-xs font-bold">{fmt(ltp)}</span>
      <span className={`text-[10px] ${changeColor(change)}`}>
        {sign(change)}{fmtInt(change)}({sign(changePct)}{fmt(changePct)}%)
      </span>
    </span>
  )
}

function Clock() {
  const [time, setTime] = useState('')

  useEffect(() => {
    const update = () => {
      const now = new Date()
      const ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }))
      const h = String(ist.getHours()).padStart(2, '0')
      const m = String(ist.getMinutes()).padStart(2, '0')
      const s = String(ist.getSeconds()).padStart(2, '0')
      setTime(`${h}:${m}:${s} IST`)
    }
    update()
    const iv = setInterval(update, 1000)
    return () => clearInterval(iv)
  }, [])

  return <span className="text-[#E8E8E8] text-xs font-mono">{time}</span>
}

export default function TopBar({ tick = {}, connected = false, mode }) {
  const sep = <span className="text-[#1f1f1f] font-mono select-none">|</span>

  return (
    <div className="sticky top-0 z-50 w-full h-9 bg-[#0a0a0a] border-b border-[#1f1f1f] flex items-center px-4 font-mono">
      {/* Left side */}
      <div className="flex items-center gap-2">
        <span className="text-[#FFB300] text-lg font-bold font-mono">BLOOM</span>
        {sep}
        <Ticker label="NIFTY" data={tick?.nifty} />
        {sep}
        <Ticker label="BANKNIFTY" data={tick?.banknifty} />
        {sep}
        <Ticker label="SENSEX" data={tick?.sensex} />
        {sep}
        <span className="flex items-center gap-1 font-mono">
          <span className="text-[#444444] text-[10px]">VIX</span>
          <span className="text-[#FF3D00] text-xs">{tick?.vix != null ? fmt(tick.vix) : '--'}</span>
        </span>
      </div>

      {/* Right side */}
      <div className="ml-auto flex items-center gap-3">
        <div className="flex items-center gap-1">
          <span className="live-dot" />
          <span className="text-[#00C853] text-[10px] tracking-wider font-mono">LIVE</span>
        </div>
        <Clock />
        <span className="text-[#FFB300] text-[9px] tracking-wider border border-[#FFB300] px-2 py-0.5 font-mono">
          {mode ? String(mode).toUpperCase() + ' MODE' : 'NORMAL MODE'}
        </span>
      </div>
    </div>
  )
}
