import { useState } from 'react'

export default function Login({ onAuth }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleLogin() {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/login', { method: 'POST' })
      const data = await res.json()
      if (data.login_url) {
        window.location.href = data.login_url
      } else if (data.authenticated) {
        onAuth(data)
      } else {
        setError(data.error || 'Login failed')
      }
    } catch (e) {
      setError('Server unreachable')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-bg">
      <div className="w-[420px] bg-surface border border-border rounded-2xl p-10 text-center">
        {/* Logo */}
        <div className="mb-8">
          <div className="text-5xl font-black tracking-[8px] text-neon mb-2"
               style={{textShadow: '0 0 30px rgba(0,212,255,0.3)'}}>
            BUYBY
          </div>
          <div className="text-xs tracking-[6px] text-text-dim uppercase">
            Trading Intelligence v2.0
          </div>
          <div className="mt-4 flex justify-center gap-2">
            {['24 ENGINES', '4 TIERS', '3 MODES'].map(t => (
              <span key={t} className="text-[10px] tracking-wider px-2 py-0.5 rounded bg-neon-dim text-neon border border-border-bright">
                {t}
              </span>
            ))}
          </div>
        </div>

        {/* Instruments */}
        <div className="flex justify-center gap-6 mb-8 text-text-dim text-xs tracking-widest">
          <span>NIFTY</span>
          <span className="text-text-muted">|</span>
          <span>BANKNIFTY</span>
          <span className="text-text-muted">|</span>
          <span>SENSEX</span>
        </div>

        {/* Login Button */}
        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full py-3.5 rounded-lg font-bold text-sm tracking-[3px] uppercase
                     bg-gradient-to-r from-neon/90 to-neon/70 text-bg
                     hover:shadow-[0_0_25px_rgba(0,212,255,0.35)] transition-all duration-300
                     disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          {loading ? 'CONNECTING...' : 'LOGIN WITH ZERODHA'}
        </button>

        {error && (
          <div className="mt-4 text-bear text-xs tracking-wider">{error}</div>
        )}

        <div className="mt-6 text-[10px] text-text-muted tracking-wider">
          Kite Connect API | Options Buyer Intelligence
        </div>
      </div>
    </div>
  )
}
