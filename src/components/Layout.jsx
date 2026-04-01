import { useState } from 'react'
import useBloomSocket from '../hooks/useBloomSocket'
import TopBar from './TopBar'
import TabSignal from './tabs/TabSignal'
import TabOIChain from './tabs/TabOIChain'
import TabEngines from './tabs/TabEngines'
import TabAICard from './tabs/TabAICard'
import TabLevels from './tabs/TabLevels'

const TABS = ['SIGNAL', 'OI CHAIN', 'ENGINES', 'AI CARD', 'LEVELS']

const TAB_COMPONENTS = {
  'SIGNAL': TabSignal,
  'OI CHAIN': TabOIChain,
  'ENGINES': TabEngines,
  'AI CARD': TabAICard,
  'LEVELS': TabLevels,
}

export default function Layout({ auth }) {
  const [activeTab, setActiveTab] = useState('SIGNAL')
  const { connected, tick, engines, chain, signal, alerts } = useBloomSocket()

  const ActiveComponent = TAB_COMPONENTS[activeTab]

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0a0a0a] font-mono">
      {/* Top Bar */}
      <TopBar tick={tick} connected={connected} mode={null} />

      {/* Tab Bar */}
      <div className="w-full h-8 bg-[#0f0f0f] border-b border-[#1f1f1f] flex items-center px-4 gap-0 font-mono">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 h-full text-[10px] tracking-[2px] uppercase font-bold cursor-pointer border-b-2 font-mono ${
              activeTab === tab
                ? 'text-[#FFB300] border-[#FFB300]'
                : 'text-[#444444] border-transparent hover:text-[#E8E8E8]'
            }`}
            style={{ borderRadius: 0, boxShadow: 'none', background: 'none' }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto bg-[#0a0a0a] font-mono">
        {ActiveComponent && (
          <ActiveComponent
            tick={tick}
            engines={engines}
            chain={chain}
            signal={signal}
            alerts={alerts}
            auth={auth}
          />
        )}
      </div>
    </div>
  )
}
