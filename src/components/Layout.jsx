import React from 'react'
import useBloomSocket from '../hooks/useBloomSocket'
import TopBar from './TopBar'

// Row 1
import SignalCommand from './panels/SignalCommand'
import OIChainLive from './panels/OIChainLive'
// Row 2
import GEXMap from './panels/GEXMap'
import IVRegimeGauge from './panels/IVRegimeGauge'
import MarketStructure from './panels/MarketStructure'
import WriterTrapFeed from './panels/WriterTrapFeed'
// Row 3
import VWAPBoard from './panels/VWAPBoard'
import TechnicalVotes from './panels/TechnicalVotes'
import ExpiryTracker from './panels/ExpiryTracker'
import FIIDIIBoard from './panels/FIIDIIBoard'
// Row 4
import BigMoveRadar from './panels/BigMoveRadar'
import VolatilityPanel from './panels/VolatilityPanel'
import PreMarketBrief from './panels/PreMarketBrief'
import StatisticalEdge from './panels/StatisticalEdge'
// Row 5
import AITradeCard from './panels/AITradeCard'

export default function Layout() {
  const { connected, tick, engines, chain, signal, alerts } = useBloomSocket()

  return (
    <div className="min-h-screen bg-bg1 text-text">
      <TopBar tick={tick} connected={connected} />

      <div className="grid grid-cols-4 gap-3 p-4">
        {/* Row 1 */}
        <div className="col-span-2">
          <SignalCommand signal={signal} alerts={alerts} engines={engines} />
        </div>
        <div className="col-span-2">
          <OIChainLive chain={chain} tick={tick} />
        </div>

        {/* Row 2 */}
        <GEXMap engines={engines} tick={tick} />
        <IVRegimeGauge engines={engines} tick={tick} />
        <MarketStructure engines={engines} tick={tick} />
        <WriterTrapFeed engines={engines} alerts={alerts} />

        {/* Row 3 */}
        <VWAPBoard engines={engines} tick={tick} />
        <TechnicalVotes engines={engines} tick={tick} />
        <ExpiryTracker engines={engines} tick={tick} />
        <FIIDIIBoard engines={engines} />

        {/* Row 4 */}
        <BigMoveRadar engines={engines} alerts={alerts} />
        <VolatilityPanel engines={engines} tick={tick} />
        <PreMarketBrief engines={engines} />
        <StatisticalEdge engines={engines} tick={tick} />

        {/* Row 5 */}
        <div className="col-span-4">
          <AITradeCard signal={signal} engines={engines} tick={tick} />
        </div>
      </div>
    </div>
  )
}
