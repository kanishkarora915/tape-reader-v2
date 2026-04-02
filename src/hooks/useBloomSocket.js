import { useState, useEffect, useRef, useCallback } from 'react'

// Deep sanitize: convert any nested object to string so React never gets an object to render
function deepSanitize(obj, depth = 0) {
  if (depth > 3) return typeof obj === 'object' ? JSON.stringify(obj) : obj
  if (obj === null || obj === undefined) return obj
  if (typeof obj !== 'object') return obj
  if (Array.isArray(obj)) return obj.map(x => deepSanitize(x, depth + 1))

  const clean = {}
  for (const [k, v] of Object.entries(obj)) {
    if (v === null || v === undefined) { clean[k] = v; continue }
    if (typeof v !== 'object') { clean[k] = v; continue }
    if (Array.isArray(v)) {
      // Keep arrays but sanitize items
      clean[k] = v.map(x => {
        if (typeof x === 'object' && x !== null) {
          // Keep objects in arrays (like chain rows, trap items) but sanitize their values
          return deepSanitize(x, depth + 1)
        }
        return x
      })
    } else {
      // For engine data sub-objects: keep them as objects (components access .data.pcr etc)
      // But also provide a _str version for safety
      clean[k] = deepSanitize(v, depth + 1)
    }
  }
  return clean
}

// Sanitize signal — flatten objects that would crash React
function sanitizeSignal(sig) {
  if (!sig || typeof sig !== 'object') return sig
  const clean = {}
  for (const [k, v] of Object.entries(sig)) {
    if (k === 'reasoning' && Array.isArray(v)) {
      clean[k] = v.map(r => typeof r === 'string' ? r : JSON.stringify(r))
    } else if (k === 'entry' && Array.isArray(v)) {
      clean[k] = v.join(' — ')
    } else if (k === 'engineVerdicts' && typeof v === 'object') {
      clean[k] = v // Keep as object but frontend shouldn't render it directly
    } else if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
      clean[k] = JSON.stringify(v)
    } else {
      clean[k] = v
    }
  }
  return clean
}

// Sanitize engines — keep structure but ensure no deeply nested objects crash React
function sanitizeEngines(enginesData) {
  if (!enginesData || typeof enginesData !== 'object') return enginesData
  const clean = {}
  for (const [eid, eng] of Object.entries(enginesData)) {
    if (!eng || typeof eng !== 'object') { clean[eid] = eng; continue }
    clean[eid] = {
      name: eng.name || eid,
      tier: eng.tier || 0,
      verdict: eng.verdict || 'NEUTRAL',
      direction: eng.direction || 'NEUTRAL',
      confidence: eng.confidence || 0,
      data: eng.data ? flattenDataForRender(eng.data) : {},
    }
  }
  return clean
}

// Flatten engine data — convert nested objects to strings, keep primitives
function flattenDataForRender(data) {
  if (!data || typeof data !== 'object') return {}
  const flat = {}
  for (const [k, v] of Object.entries(data)) {
    if (v === null || v === undefined) { flat[k] = '—'; continue }
    if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') {
      flat[k] = v
    } else if (Array.isArray(v)) {
      // Keep arrays of primitives, stringify arrays of objects
      flat[k] = v.map(item => {
        if (typeof item === 'object' && item !== null) {
          // Keep known array structures (traps, gex_by_strike, order_blocks, etc)
          const cleaned = {}
          for (const [ik, iv] of Object.entries(item)) {
            cleaned[ik] = typeof iv === 'object' ? JSON.stringify(iv) : iv
          }
          return cleaned
        }
        return item
      })
    } else if (typeof v === 'object') {
      // Nested object like {active: false, note: "..."} — flatten its values
      for (const [nk, nv] of Object.entries(v)) {
        flat[`${k}_${nk}`] = typeof nv === 'object' ? JSON.stringify(nv) : nv
      }
      // Also keep original key as string representation
      flat[k] = Object.entries(v).map(([nk, nv]) => `${nk}: ${nv}`).join(', ')
    }
  }
  return flat
}

export default function useBloomSocket() {
  const [connected, setConnected] = useState(false)
  const [tick, setTick] = useState({})
  const [engines, setEngines] = useState({})
  const [chain, setChain] = useState({})
  const [signal, setSignal] = useState(null)
  const [alerts, setAlerts] = useState([])
  const wsRef = useRef(null)
  const retryRef = useRef(0)

  const connect = useCallback(() => {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${proto}//${location.host}/ws/buyby`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      retryRef.current = 0
    }

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        const ch = msg.channel
        const d = msg.data
        if (!d || typeof d !== 'object') return

        if (ch === 'tick' || ch === 'ticks')  setTick(d)
        else if (ch === 'engines')             setEngines(sanitizeEngines(d))
        else if (ch === 'chain')               setChain(prev => ({ ...prev, [msg.index || 'NIFTY']: Array.isArray(d) ? d : [] }))
        else if (ch === 'signal')              setSignal(sanitizeSignal(d))
        else if (ch === 'alert')               setAlerts(prev => [d, ...prev].slice(0, 50))
      } catch {}
    }

    ws.onclose = () => {
      setConnected(false)
      const delay = Math.min(1000 * Math.pow(2, retryRef.current), 15000)
      retryRef.current++
      setTimeout(connect, delay)
    }

    ws.onerror = () => ws.close()
  }, [])

  useEffect(() => {
    connect()
    const iv = setInterval(() => {
      if (wsRef.current?.readyState === 1) wsRef.current.send('ping')
    }, 25000)
    return () => { clearInterval(iv); wsRef.current?.close() }
  }, [connect])

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === 1) wsRef.current.send(JSON.stringify(data))
  }, [])

  return { connected, tick, engines, chain, signal, alerts, send }
}
