from .base import BaseEngine, EngineResult
from .e01_oi_pulse import OIPulseEngine
from .e02_iv_regime import IVRegimeEngine
from .e03_market_structure import MarketStructureEngine
from .e04_confluence_scorer import ConfluenceScorerEngine
from .e05_gex_wall import GEXWallEngine
from .e06_pcr_flow import PCRFlowEngine
from .e07_writer_trap import WriterTrapEngine
from .e08_vwap_confluence import VWAPConfluenceEngine
from .e09_technical import TechnicalEngine
from .e10_expiry_flow import ExpiryFlowEngine
from .e11_fii_dii import FIIDIIEngine
from .e12_volatility_explosion import VolatilityExplosionEngine
from .e13_momentum_ignition import MomentumIgnitionEngine
from .e14_delta_spike import DeltaSpikeEngine
from .e15_vwap_snapback import VWAPSnapbackEngine
from .e16_multi_timeframe import MultiTimeframeEngine
from .e17_cross_asset import CrossAssetEngine
from .e18_statistical_edge import StatisticalEdgeEngine
from .e19_unusual_activity import UnusualActivityEngine
from .e20_flow_velocity import FlowVelocityEngine
from .e21_hidden_divergence import HiddenDivergenceEngine
from .e22_microstructure import MicrostructureEngine
from .e23_premarket import PreMarketEngine
from .e24_ai_reasoning import AIReasoningEngine

ALL_ENGINES = {
    "e01": OIPulseEngine, "e02": IVRegimeEngine, "e03": MarketStructureEngine,
    "e04": ConfluenceScorerEngine, "e05": GEXWallEngine, "e06": PCRFlowEngine,
    "e07": WriterTrapEngine, "e08": VWAPConfluenceEngine, "e09": TechnicalEngine,
    "e10": ExpiryFlowEngine, "e11": FIIDIIEngine, "e12": VolatilityExplosionEngine,
    "e13": MomentumIgnitionEngine, "e14": DeltaSpikeEngine, "e15": VWAPSnapbackEngine,
    "e16": MultiTimeframeEngine, "e17": CrossAssetEngine, "e18": StatisticalEdgeEngine,
    "e19": UnusualActivityEngine, "e20": FlowVelocityEngine, "e21": HiddenDivergenceEngine,
    "e22": MicrostructureEngine, "e23": PreMarketEngine, "e24": AIReasoningEngine,
}

def create_all_engines() -> dict:
    return {k: v() for k, v in ALL_ENGINES.items()}
