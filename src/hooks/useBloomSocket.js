import { useState, useEffect, useRef, useCallback } from 'react'

const CHANNELS = ['tick', 'engines', 'chain', 'signal', 'alert']

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
        switch (msg.channel) {
          case 'tick':    setTick(msg.data); break
          case 'engines': setEngines(msg.data); break
          case 'chain':   setChain(prev => ({ ...prev, [msg.index]: msg.data })); break
          case 'signal':  setSignal(msg.data); break
          case 'alert':   setAlerts(prev => [msg.data, ...prev].slice(0, 50)); break
        }
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
