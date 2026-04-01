import { useState, useEffect, useRef, useCallback } from 'react'

// Ensure all signal values are primitives (no objects/arrays that crash React)
function sanitizeSignal(sig) {
  if (!sig || typeof sig !== 'object') return sig
  const clean = {}
  for (const [k, v] of Object.entries(sig)) {
    if (Array.isArray(v)) clean[k] = v.map(x => typeof x === 'object' ? JSON.stringify(x) : x)
    else if (v && typeof v === 'object') clean[k] = JSON.stringify(v)
    else clean[k] = v
  }
  // Keep entry as joined string
  if (Array.isArray(sig.entry)) clean.entry = sig.entry.join(' — ')
  // Keep reasoning as array of strings
  if (Array.isArray(sig.reasoning)) clean.reasoning = sig.reasoning.map(r => typeof r === 'string' ? r : JSON.stringify(r))
  return clean
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
        else if (ch === 'engines')             setEngines(d)
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
    // Keepalive ping
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
