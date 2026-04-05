import { useState } from 'react'
import useBloomSocket from '../hooks/useBloomSocket'
import TopBar from './TopBar'
import TabSignal from './tabs/TabSignal'
import TabOIChain from './tabs/TabOIChain'
import TabEngines from './tabs/TabEngines'
import TabTrades from './tabs/TabTrades'
import TabAICard from './tabs/TabAICard'
import TabLevels from './tabs/TabLevels'
import TabUOA from './tabs/TabUOA'

const ROOT_FONT = "'IBM Plex Mono', monospace"

const TABS = ['SIGNAL', 'OI CHAIN', 'UOA', 'ENGINES', 'TRADES', 'AI CARD', 'LEVELS']

const TAB_COMPONENTS = {
  'SIGNAL': TabSignal,
  'OI CHAIN': TabOIChain,
  'UOA': TabUOA,
  'ENGINES': TabEngines,
  'TRADES': TabTrades,
  'AI CARD': TabAICard,
  'LEVELS': TabLevels,
}

const TAB_PROPS = {
  'SIGNAL': (d) => ({ signal: d.signal, engines: d.engines, tick: d.tick }),
  'OI CHAIN': (d) => ({ chain: d.chain, engines: d.engines }),
  'UOA': (d) => ({ engines: d.engines }),
  'ENGINES': (d) => ({ engines: d.engines }),
  'TRADES': (d) => ({ signal: d.signal, engines: d.engines, tick: d.tick }),
  'AI CARD': (d) => ({ engines: d.engines, signal: d.signal }),
  'LEVELS': (d) => ({ engines: d.engines, tick: d.tick }),
}

export default function Layout({ auth }) {
  const [activeTab, setActiveTab] = useState('SIGNAL')
  const [hovered, setHovered] = useState(null)
  const { connected, tick, engines, chain, signal, alerts } = useBloomSocket()

  const ActiveComponent = TAB_COMPONENTS[activeTab]
  const data = { tick, engines, chain, signal, alerts, auth }
  const activeProps = TAB_PROPS[activeTab] ? TAB_PROPS[activeTab](data) : {}

  return (
    <div
      style={{
        fontFamily: ROOT_FONT,
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        background: '#0a0a0a',
        borderRadius: 0,
        boxShadow: 'none',
      }}
    >
      {/* Top Bar */}
      <TopBar tick={tick} connected={connected} mode={null} />

      {/* Tab Bar */}
      <div
        style={{
          width: '100%',
          height: 34,
          background: '#0f0f0f',
          borderBottom: '1px solid #1f1f1f',
          display: 'flex',
          alignItems: 'stretch',
          borderRadius: 0,
          boxShadow: 'none',
        }}
      >
        {TABS.map((tab) => {
          const isActive = activeTab === tab
          const isHover = hovered === tab && !isActive
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              onMouseEnter={() => setHovered(tab)}
              onMouseLeave={() => setHovered(null)}
              style={{
                fontFamily: 'inherit',
                padding: '0 20px',
                fontSize: 10,
                fontWeight: 600,
                letterSpacing: 2,
                cursor: 'pointer',
                color: isActive ? '#FFB300' : isHover ? '#888' : '#444',
                borderBottom: isActive ? '2px solid #FFB300' : '2px solid transparent',
                background: 'none',
                border: 'none',
                borderBottomWidth: 2,
                borderBottomStyle: 'solid',
                borderBottomColor: isActive ? '#FFB300' : 'transparent',
                borderRadius: 0,
                boxShadow: 'none',
                outline: 'none',
              }}
            >
              {tab}
            </button>
          )
        })}
      </div>

      {/* Content Area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          background: '#0a0a0a',
          borderRadius: 0,
          boxShadow: 'none',
        }}
      >
        {ActiveComponent && <ActiveComponent {...activeProps} />}
      </div>
    </div>
  )
}
