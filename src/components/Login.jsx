import { useState, useMemo } from 'react'

function getMarketStatus() {
  const now = new Date()
  const h = now.getHours()
  const m = now.getMinutes()
  const day = now.getDay()
  if (day === 0 || day === 6) return { label: 'CLOSED', color: '#FF3D00' }
  const t = h * 60 + m
  if (t >= 555 && t < 915) return { label: 'OPEN', color: '#00C853' }
  if (t >= 540 && t < 555) return { label: 'PRE-MARKET', color: '#FFB300' }
  return { label: 'CLOSED', color: '#FF3D00' }
}

const instruments = [
  { name: 'NIFTY 50', exchange: 'NSE INDEX' },
  { name: 'BANK NIFTY', exchange: 'NFO INDEX' },
  { name: 'SENSEX', exchange: 'BSE INDEX' },
]

export default function Login({ onAuth }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const market = useMemo(() => getMarketStatus(), [])

  async function handleLogin() {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/login', { method: 'POST' })
      const data = await res.json()
      if (data.login_url) window.location.href = data.login_url
      else if (data.authenticated) onAuth(data)
      else setError(data.error || 'Login failed')
    } catch (e) {
      setError('Server unreachable')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="font-mono"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#0a0a0a',
      }}
    >
      <div
        style={{
          width: 480,
          background: '#0f0f0f',
          border: '1px solid #1f1f1f',
          padding: 48,
        }}
      >
        {/* ── Top Section ── */}
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              color: '#FFB300',
              fontSize: 42,
              fontWeight: 700,
              letterSpacing: 8,
              lineHeight: 1,
            }}
          >
            BLOOM
          </div>
          <div
            style={{
              width: 60,
              height: 2,
              background: '#FFB300',
              margin: '12px auto',
            }}
          />
          <div
            style={{
              color: '#444',
              fontSize: 10,
              letterSpacing: 5,
            }}
          >
            INSTITUTIONAL TRADING TERMINAL
          </div>
          <div
            style={{
              color: '#444',
              fontSize: 9,
              letterSpacing: 2,
              marginTop: 8,
            }}
          >
            v2.0 &middot; 24 Engines &middot; 4 Tiers &middot; 3 Modes
          </div>
        </div>

        {/* ── Instrument Badges ── */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 12,
            marginTop: 40,
          }}
        >
          {instruments.map((inst) => (
            <div
              key={inst.name}
              style={{
                border: '1px solid #1f1f1f',
                padding: '6px 16px',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  color: '#FFB300',
                  fontSize: 10,
                  fontWeight: 700,
                }}
              >
                {inst.name}
              </div>
              <div style={{ color: '#444', fontSize: 8 }}>{inst.exchange}</div>
            </div>
          ))}
        </div>

        {/* ── Status Section ── */}
        <div style={{ marginTop: 32 }}>
          <StatusRow label="CONNECTION">
            <span style={{ color: '#00C853', fontSize: 10, letterSpacing: 1 }}>
              KITE API CONFIGURED{' '}
              <span style={{ color: '#00C853' }}>{'\u25CF'}</span>
            </span>
          </StatusRow>
          <StatusRow label="MARKET STATUS">
            <span
              style={{ color: market.color, fontSize: 10, letterSpacing: 1 }}
            >
              {market.label}
            </span>
          </StatusRow>
          <StatusRow label="DATA FEED">
            <span style={{ color: '#E8E8E8', fontSize: 10, letterSpacing: 1 }}>
              ZERODHA KITE CONNECT
            </span>
          </StatusRow>
        </div>

        {/* ── Connect Button ── */}
        <button
          onClick={handleLogin}
          disabled={loading}
          className="premium-btn"
          style={{
            marginTop: 32,
            width: '100%',
            height: 44,
            background: '#FFB300',
            color: '#0a0a0a',
            fontWeight: 700,
            fontSize: 12,
            letterSpacing: 3,
            border: 'none',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.3 : 1,
            fontFamily: 'inherit',
          }}
        >
          <span className={loading ? 'text-pulse' : ''}>
            {loading ? 'AUTHENTICATING...' : 'CONNECT TO ZERODHA KITE \u2192'}
          </span>
        </button>

        {/* ── Error ── */}
        {error && (
          <div
            style={{
              marginTop: 10,
              color: '#FF3D00',
              fontSize: 10,
              textAlign: 'center',
              letterSpacing: 1,
            }}
          >
            {error}
          </div>
        )}

        {/* ── Footer ── */}
        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <div style={{ color: '#333', fontSize: 8, letterSpacing: 3 }}>
            SECURE &middot; ENCRYPTED &middot; OAUTH 2.0
          </div>
          <div
            style={{
              color: '#333',
              fontSize: 8,
              letterSpacing: 1,
              marginTop: 4,
            }}
          >
            Kite Connect API &middot; Zerodha Broking
          </div>
        </div>
      </div>
    </div>
  )
}

function StatusRow({ label, children }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '6px 0',
        borderBottom: '1px solid #1a1a1a',
      }}
    >
      <span style={{ color: '#444', fontSize: 9, letterSpacing: 2 }}>
        {label}
      </span>
      {children}
    </div>
  )
}
