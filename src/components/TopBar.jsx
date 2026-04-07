import { useState, useEffect } from 'react'

const ROOT_FONT = "'IBM Plex Mono', monospace"

const numFmt = new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const intFmt = new Intl.NumberFormat('en-IN')

const fmt = (n) => (n == null || n === 0) ? '\u2014' : numFmt.format(Number(n))
const fmtInt = (n) => (n == null || n === 0) ? '\u2014' : intFmt.format(Number(n))

const sign = (val) => (Number(val) >= 0 ? '+' : '')
const changeColor = (val) => {
  if (val == null) return '#E8E8E8'
  return Number(val) >= 0 ? '#00C853' : '#FF3D00'
}

function Ticker({ label, data }) {
  const placeholder = (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      <span style={{ color: '#555', fontSize: 10 }}>{label}</span>
      <span style={{ color: '#E8E8E8', fontSize: 13, fontWeight: 600 }}>{'\u2014'}</span>
    </span>
  )
  if (!data || typeof data !== 'object') return placeholder
  const ltp = typeof data.ltp === 'number' ? data.ltp : 0
  const change = typeof data.change === 'number' ? data.change : 0
  const changePct = typeof data.changePct === 'number' ? data.changePct : 0
  if (!ltp && ltp !== 0) return placeholder
  const clr = changeColor(change)

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      <span style={{ color: '#555', fontSize: 10 }}>{label}</span>
      <span style={{ color: '#E8E8E8', fontSize: 13, fontWeight: 600 }}>{fmt(ltp)}</span>
      <span style={{ color: clr, fontSize: 10 }}>
        {sign(change)}{fmtInt(change)} ({sign(changePct)}{fmt(changePct)}%)
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

  return <span style={{ color: '#E8E8E8', fontSize: 12 }}>{time}</span>
}

const SEP_STYLE = { color: '#1f1f1f', userSelect: 'none', padding: '0 2px' }

export default function TopBar({ tick = {}, connected = false, mode }) {
  const sep = <span style={SEP_STYLE}>|</span>

  return (
    <div
      style={{
        fontFamily: ROOT_FONT,
        position: 'sticky',
        top: 0,
        zIndex: 50,
        width: '100%',
        height: 38,
        background: '#0a0a0a',
        borderBottom: '1px solid #1f1f1f',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        boxSizing: 'border-box',
        borderRadius: 0,
        boxShadow: 'none',
      }}
    >
      {/* Left group */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        <span style={{ color: '#FFB300', fontSize: 16, fontWeight: 700, letterSpacing: 5 }}>BLOOM</span>
        {sep}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Ticker label="NIFTY" data={tick?.nifty} />
          {sep}
          <Ticker label="BANKNIFTY" data={tick?.banknifty} />
          {sep}
          <Ticker label="SENSEX" data={tick?.sensex} />
        </div>
        {sep}
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <span style={{ color: '#555', fontSize: 10 }}>VIX</span>
          <span style={{ color: '#FF3D00', fontSize: 13, fontWeight: 600 }}>
            {typeof tick?.vix === 'number' && tick.vix !== 0 ? fmt(tick.vix) : '\u2014'}
          </span>
        </span>
      </div>

      {/* Right group */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <span
          className="live-dot"
          style={{
            width: 6,
            height: 6,
            background: '#00C853',
            borderRadius: 0,
            display: 'inline-block',
          }}
        />
        <span style={{ color: '#00C853', fontSize: 9, letterSpacing: 2 }}>LIVE</span>
        <Clock />
        <button
          onClick={() => { fetch('/api/logout', {method:'POST'}).then(() => window.location.href = '/') }}
          style={{
            border: '1px solid #FF3D00',
            padding: '2px 10px',
            color: '#FF3D00',
            fontSize: 9,
            letterSpacing: 2,
            borderRadius: 0,
            background: 'none',
            cursor: 'pointer',
            fontFamily: "'IBM Plex Mono', monospace",
          }}
        >
          LOGOUT
        </button>
      </div>
    </div>
  )
}
