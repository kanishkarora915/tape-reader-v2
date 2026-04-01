"""
BuyBy Trading System — Configuration
Loads environment variables and defines index/instrument constants.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── API Keys ────────────────────────────────────────────────────────────

KITE_API_KEY = os.getenv("KITE_API_KEY", "")
KITE_API_SECRET = os.getenv("KITE_API_SECRET", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ── Environment ─────────────────────────────────────────────────────────

IS_PROD = os.getenv("RENDER") == "true"
PORT = int(os.getenv("PORT", 8000))

# ── Index Configuration ─────────────────────────────────────────────────

INDEX_CONFIG = {
    "NIFTY": {
        "exchange": "NFO",
        "spot_token": 256265,
        "strike_gap": 50,
        "lot_size": 25,
    },
    "BANKNIFTY": {
        "exchange": "NFO",
        "spot_token": 260105,
        "strike_gap": 100,
        "lot_size": 15,
    },
    "SENSEX": {
        "exchange": "BFO",
        "spot_token": 265,
        "strike_gap": 100,
        "lot_size": 10,
    },
}

VIX_TOKEN = 264969

# ── Paths ───────────────────────────────────────────────────────────────

FRONTEND_DIST = Path(__file__).parent.parent / "dist"
