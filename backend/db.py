"""
BuyBy Trading System — PostgreSQL Async Database Layer
Connection pool management and table initialization.
"""

import logging

import asyncpg

from config import DATABASE_URL

logger = logging.getLogger("buyby.db")

pool: asyncpg.Pool | None = None


# ── Table Definitions ───────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS signals (
    id          SERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    instrument  VARCHAR(20) NOT NULL,
    direction   VARCHAR(20) NOT NULL,
    strike      INT NOT NULL,
    expiry      DATE NOT NULL,
    entry_low   NUMERIC(12,2),
    entry_high  NUMERIC(12,2),
    sl          NUMERIC(12,2),
    t1          NUMERIC(12,2),
    t2          NUMERIC(12,2),
    score       INT,
    max_score   INT,
    mode        VARCHAR(20),
    reasoning   JSONB,
    engine_states JSONB,
    status      VARCHAR(20) DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS oi_snapshots (
    id          SERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    instrument  VARCHAR(20) NOT NULL,
    strike      INT NOT NULL,
    expiry      DATE NOT NULL,
    ce_oi       BIGINT,
    pe_oi       BIGINT,
    ce_ltp      NUMERIC(12,2),
    pe_ltp      NUMERIC(12,2),
    spot        NUMERIC(12,2)
);

CREATE TABLE IF NOT EXISTS iv_history (
    id          SERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    instrument  VARCHAR(20) NOT NULL,
    atm_iv      NUMERIC(8,2),
    ivr         INT
);

CREATE TABLE IF NOT EXISTS fii_dii (
    id              SERIAL PRIMARY KEY,
    date            DATE UNIQUE NOT NULL,
    fii_index_fut   NUMERIC(14,2),
    dii_index_fut   NUMERIC(14,2),
    fii_index_opt   NUMERIC(14,2),
    dii_index_opt   NUMERIC(14,2)
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id          SERIAL PRIMARY KEY,
    session_id  VARCHAR(64) UNIQUE NOT NULL,
    api_key     VARCHAR(32),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active TIMESTAMPTZ
);
"""


# ── Pool Management ─────────────────────────────────────────────────────

async def init_db() -> None:
    """Initialize the database connection pool and create tables."""
    global pool

    if not DATABASE_URL:
        logger.warning("[DB] DATABASE_URL not set — running without database")
        return

    try:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        async with pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)
        logger.info("[DB] Connected and tables initialized")
    except Exception as e:
        logger.error(f"[DB] Failed to initialize: {e}")
        pool = None


async def close_db() -> None:
    """Close the database connection pool."""
    global pool
    if pool:
        await pool.close()
        pool = None
        logger.info("[DB] Connection pool closed")


# ── Query Helpers ───────────────────────────────────────────────────────

async def execute(query: str, *args) -> str:
    """Execute a query (INSERT/UPDATE/DELETE)."""
    if not pool:
        return "no-db"
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def fetch(query: str, *args) -> list:
    """Fetch multiple rows."""
    if not pool:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def fetch_one(query: str, *args) -> dict | None:
    """Fetch a single row."""
    if not pool:
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None
