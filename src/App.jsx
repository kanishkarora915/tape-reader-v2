import { useState, useEffect } from 'react'
import Login from './components/Login'
import Layout from './components/Layout'

export default function App() {
  const [auth, setAuth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/status')
      .then(r => r.json())
      .then(d => { if (d.authenticated) setAuth(d); })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bg">
        <div className="text-center">
          <div className="text-4xl font-black tracking-[6px] text-neon mb-3">BUYBY</div>
          <div className="text-sm tracking-[4px] text-text-dim">LOADING...</div>
        </div>
      </div>
    )
  }

  if (!auth) return <Login onAuth={setAuth} />
  return <Layout auth={auth} />
}
