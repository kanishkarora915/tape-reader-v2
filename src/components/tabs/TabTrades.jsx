import React, { useState, useEffect } from 'react';

const FONT = "'IBM Plex Mono', monospace";
const C = {
  bg: '#0a0a0a',
  panel: '#0f0f0f',
  border: '#1f1f1f',
  amber: '#FFB300',
  amberDim: '#7A5600',
  white: '#E8E8E8',
  green: '#00C853',
  red: '#FF3D00',
  blue: '#2196F3',
  gray: '#444',
};

export default function TabTrades({ signal, engines, tick }) {
  const [trades, setTrades] = useState([]);
  const [stats, setStats] = useState({});

  async function fetchTrades() {
    try {
      const r = await fetch('/api/trades');
      const d = await r.json();
      setTrades(d.trades || []);
    } catch {}
  }

  async function fetchStats() {
    try {
      const r = await fetch('/api/trade-stats');
      const d = await r.json();
      setStats(d);
    } catch {}
  }

  useEffect(() => {
    fetchTrades();
    fetchStats();
    const iv = setInterval(() => { fetchTrades(); fetchStats(); }, 30000);
    return () => clearInterval(iv);
  }, []);

  const pnlColor = (stats.today_pnl || 0) >= 0 ? C.green : C.red;
  const trendUp = stats.accuracy_trend === 'IMPROVING';

  return (
    <div style={{ fontFamily: FONT, background: C.bg, color: C.white, minHeight: '100%' }}>

      {/* ── SECTION 1: INTRADAY P&L SUMMARY ── */}
      <div style={{
        background: C.panel,
        padding: '16px 20px',
        borderBottom: `1px solid ${C.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: 40,
        flexWrap: 'wrap',
      }}>
        <div>
          <div style={{ fontSize: 9, color: '#555', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 4 }}>TODAY'S P&L</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: pnlColor }}>
            {(stats.today_pnl || 0) >= 0 ? '+' : ''}{'\u20B9'}{stats.today_pnl ?? 0}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 9, color: '#555', letterSpacing: 1, marginBottom: 4 }}>TOTAL TRADES</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: C.white }}>{stats.today_trades ?? 0}</div>
        </div>
        <div>
          <div style={{ fontSize: 9, color: '#555', letterSpacing: 1, marginBottom: 4 }}>WON</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: C.green }}>{stats.won ?? 0}</div>
        </div>
        <div>
          <div style={{ fontSize: 9, color: '#555', letterSpacing: 1, marginBottom: 4 }}>LOST</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: C.red }}>{stats.lost ?? 0}</div>
        </div>
        <div>
          <div style={{ fontSize: 9, color: '#555', letterSpacing: 1, marginBottom: 4 }}>WIN RATE</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: C.amber }}>{stats.win_rate ?? 0}%</div>
        </div>
        <div>
          <div style={{ fontSize: 9, color: '#555', letterSpacing: 1, marginBottom: 4 }}>AVG R:R</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: C.white }}>{stats.avg_rr ?? '—'}</div>
        </div>
        <div>
          <div style={{ fontSize: 9, color: '#555', letterSpacing: 1, marginBottom: 4 }}>ACCURACY TREND</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: trendUp ? C.green : C.red }}>
            {trendUp ? 'IMPROVING \u2191' : 'DECLINING \u2193'}
          </div>
        </div>
      </div>

      {/* ── SECTION 2: TRADE LOG ── */}
      <div style={{ padding: '16px 20px' }}>
        <div style={{
          fontSize: 10,
          color: C.amber,
          letterSpacing: 2,
          textTransform: 'uppercase',
          fontWeight: 700,
          marginBottom: 12,
          borderBottom: `1px solid ${C.border}`,
          paddingBottom: 8,
        }}>TRADE LOG</div>

        {/* Header */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '30px 70px 90px 90px 70px 70px 110px 110px 60px 1fr',
          fontSize: 9,
          color: '#555',
          letterSpacing: 1,
          borderBottom: `1px solid ${C.border}`,
          paddingBottom: 6,
          marginBottom: 4,
          textTransform: 'uppercase',
        }}>
          <span>#</span>
          <span>TIME</span>
          <span>SIGNAL</span>
          <span>STRIKE</span>
          <span>ENTRY</span>
          <span>EXIT</span>
          <span>P&L</span>
          <span>STATUS</span>
          <span>SL HIT?</span>
          <span>REASON</span>
        </div>

        {/* Rows */}
        {trades.length === 0 ? (
          <div style={{ fontSize: 11, color: '#333', padding: '20px 0' }}>
            No trades generated today — system analyzing market conditions
          </div>
        ) : (
          trades.map((t, i) => {
            const isProfit = (t.pnl_amount || 0) >= 0;
            const isBuyCall = (t.signal_type || '').toUpperCase().includes('CALL');
            let statusColor = C.gray;
            let statusLabel = t.status || 'UNKNOWN';
            if (statusLabel === 'WON') { statusColor = C.green; statusLabel = 'TARGET HIT \u2713'; }
            else if (statusLabel === 'LOST') { statusColor = C.red; statusLabel = 'SL HIT \u2717'; }
            else if (statusLabel === 'ACTIVE') { statusColor = C.amber; statusLabel = 'ACTIVE'; }
            else if (statusLabel === 'EXPIRED') { statusColor = C.gray; statusLabel = 'EXPIRED'; }

            return (
              <div key={t.id || i} style={{
                display: 'grid',
                gridTemplateColumns: '30px 70px 90px 90px 70px 70px 110px 110px 60px 1fr',
                fontSize: 11,
                padding: '6px 0',
                borderBottom: '1px solid #141414',
                alignItems: 'center',
              }}>
                <span style={{ color: C.gray }}>{i + 1}</span>
                <span style={{ color: '#555' }}>{t.timestamp || '—'}</span>
                <span style={{ fontWeight: 600, color: isBuyCall ? C.green : C.red }}>
                  {isBuyCall ? 'BUY CALL' : 'BUY PUT'}
                </span>
                <span style={{ color: C.white }}>{t.strike || '—'}</span>
                <span style={{ color: C.white }}>{t.entry_price != null ? `\u20B9${t.entry_price}` : '—'}</span>
                <span style={{ color: t.exit_price != null ? (isProfit ? C.green : C.red) : '#555' }}>
                  {t.exit_price != null ? `\u20B9${t.exit_price}` : '—'}
                </span>
                <span style={{ fontWeight: 600, color: isProfit ? C.green : C.red }}>
                  {t.pnl_amount != null
                    ? `${isProfit ? '+' : ''}\u20B9${t.pnl_amount} (${isProfit ? '+' : ''}${t.pnl_pct ?? 0}%)`
                    : '—'}
                </span>
                <span style={{ color: statusColor, fontWeight: 600, fontSize: 10 }}>{statusLabel}</span>
                <span style={{ color: t.sl_hit ? C.red : C.green, fontSize: 10 }}>
                  {t.sl_hit ? 'YES' : 'NO'}
                </span>
                <span style={{ color: C.amberDim, fontSize: 10 }}>{t.reason || '—'}</span>
              </div>
            );
          })
        )}
      </div>

      {/* ── SECTION 3: LEARNING INSIGHTS ── */}
      <div style={{ padding: '16px 20px' }}>
        <div style={{
          fontSize: 10,
          color: C.amber,
          letterSpacing: 2,
          textTransform: 'uppercase',
          fontWeight: 700,
          marginBottom: 12,
          borderBottom: `1px solid ${C.border}`,
          paddingBottom: 8,
        }}>LEARNING INSIGHTS</div>

        {(stats.learning_insights || []).length === 0 ? (
          <div style={{ fontSize: 11, color: '#333', padding: '8px 0' }}>
            Insights will appear after trade data accumulates
          </div>
        ) : (
          (stats.learning_insights || []).map((insight, i) => (
            <div key={i} style={{ fontSize: 11, padding: '4px 0', color: C.white }}>
              <span style={{ color: C.amber, marginRight: 8 }}>{'\u2192'}</span>
              {insight}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
