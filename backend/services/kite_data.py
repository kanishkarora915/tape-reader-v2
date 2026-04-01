"""
BuyBy Trading System — Kite REST API Wrappers
Convenience functions for fetching instruments, historical data, quotes, and option chains.
"""

import logging
from datetime import datetime, timedelta

from kiteconnect import KiteConnect

from config import INDEX_CONFIG

logger = logging.getLogger("buyby.kite_data")


def get_instruments(kite: KiteConnect, exchange: str) -> list[dict]:
    """Fetch all instruments for a given exchange."""
    try:
        return kite.instruments(exchange)
    except Exception as e:
        logger.error(f"[KITE] instruments({exchange}) failed: {e}")
        return []


def get_historical(
    kite: KiteConnect,
    token: int,
    from_date: datetime,
    to_date: datetime,
    interval: str = "5minute",
) -> list[dict]:
    """Fetch historical OHLCV data for an instrument token."""
    try:
        return kite.historical_data(
            instrument_token=token,
            from_date=from_date,
            to_date=to_date,
            interval=interval,
        )
    except Exception as e:
        logger.error(f"[KITE] historical_data({token}) failed: {e}")
        return []


def get_quote(kite: KiteConnect, instruments: list[str]) -> dict:
    """
    Fetch live quotes for given instruments.
    instruments: list of exchange:symbol strings, e.g. ["NSE:NIFTY 50", "NFO:NIFTY24DECFUT"]
    """
    try:
        return kite.quote(instruments)
    except Exception as e:
        logger.error(f"[KITE] quote() failed: {e}")
        return {}


def get_option_chain(kite: KiteConnect, index_name: str) -> list[dict]:
    """
    Fetch full option chain for the nearest expiry of an index.
    Returns list of instrument dicts with strike, type, expiry, tradingsymbol.
    """
    cfg = INDEX_CONFIG.get(index_name.upper())
    if not cfg:
        logger.error(f"[KITE] Unknown index: {index_name}")
        return []

    exchange = cfg["exchange"]
    prefix = index_name.upper()

    try:
        instruments = kite.instruments(exchange)
    except Exception as e:
        logger.error(f"[KITE] instruments({exchange}) failed: {e}")
        return []

    # Filter for this index's options
    options = [
        i for i in instruments
        if i["name"] == prefix
        and i["instrument_type"] in ("CE", "PE")
    ]

    if not options:
        return []

    # Find nearest expiry
    today = datetime.now().date()
    expiries = sorted(set(i["expiry"] for i in options if i["expiry"] >= today))

    if not expiries:
        return []

    nearest_expiry = expiries[0]

    # Return all options for nearest expiry
    chain = [
        {
            "instrument_token": i["instrument_token"],
            "tradingsymbol": i["tradingsymbol"],
            "strike": i["strike"],
            "instrument_type": i["instrument_type"],
            "expiry": str(i["expiry"]),
            "lot_size": i["lot_size"],
            "exchange": exchange,
        }
        for i in options
        if i["expiry"] == nearest_expiry
    ]

    return sorted(chain, key=lambda x: (x["strike"], x["instrument_type"]))
