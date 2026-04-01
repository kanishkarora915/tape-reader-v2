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
    <div className="flex items-center justify-center min-h-screen bg-bg font-mono">
      <div className="w-[400px] bg-panel border border-border p-8">
        <div className="text-center mb-6">
          <div className="text-3xl font-bold text-amber tracking-[6px] mb-1">BLOOM</div>
          <div className="text-[10px] text-gray tracking-[4px] uppercase">Trading Terminal v2.0</div>
        </div>

        <div className="flex justify-center gap-4 mb-6 text-[10px] text-gray tracking-widest">
          <span>NIFTY</span><span className="text-border">|</span>
          <span>BANKNIFTY</span><span className="text-border">|</span>
          <span>SENSEX</span>
        </div>

        <div className="flex justify-center gap-2 mb-6">
          {['24 ENGINES', '4 TIERS', '3 MODES'].map(t => (
            <span key={t} className="text-[9px] tracking-wider px-2 py-0.5 border border-amber text-amber">
              {t}
            </span>
          ))}
        </div>

        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full py-2.5 font-bold text-[11px] tracking-[3px] uppercase cursor-pointer
                     bg-amber text-bg border border-amber
                     hover:bg-amber/80 transition-colors
                     disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {loading ? 'CONNECTING...' : 'LOGIN WITH ZERODHA'}
        </button>

        {error && <div className="mt-3 text-red text-[10px] tracking-wider text-center">{error}</div>}

        <div className="mt-4 text-[9px] text-gray tracking-wider text-center">
          Kite Connect API | Options Buyer Intelligence
        </div>
      </div>
    </div>
  )
}
