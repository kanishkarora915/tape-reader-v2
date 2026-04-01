import { useState, useEffect, Component } from 'react'
import Login from './components/Login'
import Layout from './components/Layout'

// Error Boundary — catches React render crashes, shows error instead of blank screen
class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  componentDidCatch(error, info) {
    console.error('[BLOOM] React crash caught:', error, info)
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          fontFamily: "'IBM Plex Mono', monospace",
          background: '#0a0a0a', color: '#FF3D00', minHeight: '100vh',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
          padding: 40,
        }}>
          <div style={{ color: '#FFB300', fontSize: 24, fontWeight: 700, letterSpacing: 4, marginBottom: 16 }}>
            BLOOM — RENDER ERROR
          </div>
          <div style={{ color: '#E8E8E8', fontSize: 12, marginBottom: 12 }}>
            A component crashed. This is usually caused by unexpected data from the server.
          </div>
          <div style={{ color: '#FF3D00', fontSize: 10, maxWidth: 600, wordBreak: 'break-all', marginBottom: 20 }}>
            {this.state.error?.message || 'Unknown error'}
          </div>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
            style={{
              background: '#FFB300', color: '#0a0a0a', border: 'none', padding: '10px 24px',
              fontWeight: 700, fontSize: 11, letterSpacing: 2, cursor: 'pointer',
              fontFamily: "'IBM Plex Mono', monospace",
            }}
          >
            RELOAD TERMINAL
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

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
      <div style={{
        fontFamily: "'IBM Plex Mono', monospace",
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        minHeight: '100vh', background: '#0a0a0a',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#FFB300', fontSize: 24, fontWeight: 700, letterSpacing: 4, marginBottom: 8 }}>BLOOM</div>
          <div style={{ color: '#444', fontSize: 10, letterSpacing: 3 }}>LOADING TERMINAL...</div>
        </div>
      </div>
    )
  }

  if (!auth) return <ErrorBoundary><Login onAuth={setAuth} /></ErrorBoundary>
  return <ErrorBoundary><Layout auth={auth} /></ErrorBoundary>
}
