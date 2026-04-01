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
        <div className="text-center font-mono">
          <div className="text-2xl font-bold text-amber tracking-[4px] mb-2">BLOOM</div>
          <div className="text-xs text-gray tracking-[3px]">LOADING TERMINAL...</div>
        </div>
      </div>
    )
  }

  if (!auth) return <Login onAuth={setAuth} />
  return <Layout auth={auth} />
}
