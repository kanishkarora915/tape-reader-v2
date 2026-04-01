import React, { useState, useEffect } from 'react'

function IndexCard({ name, ltp, change, changePct }) {
  const isPositive = change >= 0
  const color = isPositive ? 'text-green-400' : 'text-red-400'
  return (
    <div className="flex flex-col items-center px-4 border-r border-border last:border-r-0">
      <span className="text-[10px] uppercase tracking-wider text-muted">{name}</span>
      <span className="text-base font-mono font-bold text-text">
        {ltp?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '—'}
      </span>
      <span className={`text-[10px] font-mono ${color}`}>
        {isPositive ? '+' : ''}{change?.toFixed(2) ?? '0.00'} ({isPositive ? '+' : ''}{changePct?.toFixed(2) ?? '0.00'}%)
      </span>
    </div>
  )
}

function VIXCard({ value }) {
  let color = 'text-green-400'
  if (value >= 20) color = 'text-red-400'
  else if (value >= 15) color = 'text-yellow-400'

  return (
    <div className="flex flex-col items-center px-4">
      <span className="text-[10px] uppercase tracking-wider text-muted">VIX</span>
      <span className={`text-base font-mono font-bold ${color}`}>
        {value?.toFixed(2) ?? '—'}
      </span>
    </div>
  )
}

function Clock() {
  const [time, setTime] = useState('')

  useEffect(() => {
    const update = () => {
      const now = new Date()
      setTime(
        now.toLocaleTimeString('en-IN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
          timeZone: 'Asia/Kolkata',
        })
      )
    }
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="flex items-center gap-1">
      <span className="font-mono text-sm text-text">{time}</span>
      <span className="text-[9px] text-muted">IST</span>
    </div>
  )
}

export default function TopBar({ tick = {}, connected = false }) {
  const { nifty = {}, banknifty = {}, sensex = {}, vix } = tick

  return (
    <div className="bg-bg2 border-b border-border h-14 px-6 flex items-center justify-between z-50 sticky top-0">
      {/* Left — Logo */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-neon font-black tracking-[6px] text-xl select-none">BUYBY</span>
        <span className="text-[9px] bg-neon/20 text-neon px-1.5 py-0.5 rounded font-semibold">v2.0</span>
      </div>

      {/* Center — Status + Index Cards */}
      <div className="flex items-center gap-4">
        {/* Connection dot */}
        <div className="flex items-center gap-1.5">
          <span
            className={`h-2 w-2 rounded-full ${
              connected ? 'bg-green-400 animate-pulse' : 'bg-red-500'
            }`}
          />
          <span className={`text-[10px] font-bold tracking-wider ${connected ? 'text-green-400' : 'text-red-500'}`}>
            {connected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>

        <div className="h-6 w-px bg-border" />

        {/* Index cards */}
        <IndexCard name="NIFTY" ltp={nifty.ltp} change={nifty.change} changePct={nifty.changePct} />
        <IndexCard name="BANKNIFTY" ltp={banknifty.ltp} change={banknifty.change} changePct={banknifty.changePct} />
        <IndexCard name="SENSEX" ltp={sensex.ltp} change={sensex.change} changePct={sensex.changePct} />

        <div className="h-6 w-px bg-border" />

        {/* VIX */}
        <VIXCard value={vix} />
      </div>

      {/* Right — Clock + User */}
      <div className="flex items-center gap-4 shrink-0">
        <Clock />
        <div className="h-7 w-7 rounded-full bg-neon/20 flex items-center justify-center">
          <span className="text-neon text-xs font-bold">K</span>
        </div>
      </div>
    </div>
  )
}
