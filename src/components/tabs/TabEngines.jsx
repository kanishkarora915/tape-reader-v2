import React from "react";

const ENGINE_ORDER = [
  "e01","e02","e03","e04","e05","e06","e07","e08",
  "e09","e10","e11","e12","e13","e14","e15","e16",
  "e17","e18","e19","e20","e21","e22","e23","e24",
];

const TIER_META = {
  1: { label: "CORE GATE", bg: "#FF3D00" },
  2: { label: "DIRECTION", bg: "#FFB300" },
  3: { label: "AMPLIFIER", bg: "#00C853" },
  4: { label: "BIG MOVE", bg: "#2196F3" },
};

const SECTION_HEADER = {
  fontSize: 10,
  color: "#FFB300",
  fontWeight: 600,
  letterSpacing: 3,
  textTransform: "uppercase",
  borderBottom: "1px solid #1f1f1f",
  paddingBottom: 8,
  marginBottom: 12,
};

function getValueLine(key, data) {
  if (!data) return "No data";
  switch (key) {
    case "e01": return data.writer_signal || "Monitoring OI...";
    case "e02": return `IVR: ${data.ivr ?? "\u2014"}/100`;
    case "e03": return data.regime || "Analyzing...";
    case "e04": return `${data.total_score ?? "\u2014"}/${data.max_score ?? "\u2014"} consensus`;
    case "e05": return data.total_gex != null ? `GEX ${data.total_gex > 0 ? "+" : ""}${data.total_gex.toFixed(0)}` : "Computing...";
    case "e06": return `PCR ${data.pcr || "\u2014"}`;
    case "e07": return data.traps?.length ? `${data.traps.length} trap(s)` : "No traps";
    case "e08": return data.position || "Computing VWAP...";
    case "e09": return data.summary || "Computing...";
    case "e10": return `MP: ${data.max_pain || "\u2014"}`;
    case "e11": return data.fii_3day_trend || "Fetching FII data...";
    case "e12": return data.bb_squeeze || "Normal";
    case "e13": return data.ignition_detected ? "Ignition FIRED" : "Monitoring...";
    case "e14": return `Delta: ${data.delta_shift || 0}`;
    case "e15": return data.stretched ? "STRETCHED" : "Normal range";
    case "e16": return data.aligned ? "ALIGNED" : "Not aligned";
    case "e17": return `USD/INR ${data.usdinr || "\u2014"}`;
    case "e18": return `${data.win_rate || 0}% over ${data.similar_setups || 0} setups`;
    case "e19": return data.active ? "UOA detected" : "Monitoring...";
    case "e20": return `Velocity: ${data.max_velocity || 0}`;
    case "e21": return data.active ? "Divergence found" : "Monitoring...";
    case "e22": return `Imbalance: ${data.imbalance_ratio || 50}%`;
    case "e23": return data.morning_bias || "Pre-market pending";
    case "e24": return data.rationale ? "Analysis ready" : "Waiting for signal...";
    default: return "\u2014";
  }
}

function getSignalLine(key, eng) {
  const { direction, verdict, tier, data } = eng;

  if (key === "e04" && data) {
    return { text: `SCORE: ${data.total_score ?? 0}/${data.max_score ?? 0}`, color: "#FFB300" };
  }
  if (key === "e02" && data) {
    const gs = data.gate_status;
    const c = gs === "OPEN" ? "#00C853" : gs === "PARTIAL" ? "#FFB300" : "#FF3D00";
    return { text: `GATE ${gs || "\u2014"}`, color: c };
  }
  if (key === "e12" && data?.bb_squeeze) {
    return { text: "SQUEEZE", color: "#FFB300" };
  }
  if (key === "e18" && data) {
    const wr = data.win_rate || 0;
    return { text: `${wr}% WIN`, color: wr > 60 ? "#00C853" : "#FFB300" };
  }
  if (tier === 4 && verdict === "PASS") {
    return { text: "ALERT \u2605", color: "#2196F3" };
  }

  if (direction === "BULLISH") return { text: "+1 CALL", color: "#00C853" };
  if (direction === "BEARISH") return { text: "+1 PUT", color: "#FF3D00" };
  return { text: "NEUTRAL", color: "#444" };
}

export default function TabEngines({ engines }) {
  if (!engines || Object.keys(engines).length === 0) {
    return (
      <div
        style={{
          fontFamily: "'IBM Plex Mono', monospace",
          background: "#0a0a0a",
          color: "#333",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: 400,
          fontSize: 12,
        }}
      >
        Waiting for engine data...
      </div>
    );
  }

  let active = 0, calls = 0, puts = 0, neutral = 0, t4alerts = 0;
  ENGINE_ORDER.forEach((k) => {
    const eng = engines[k];
    if (!eng) return;
    const isActive = eng.verdict === "PASS" || eng.verdict === "PARTIAL";
    if (isActive) active++;
    if (eng.direction === "BULLISH") calls++;
    else if (eng.direction === "BEARISH") puts++;
    else neutral++;
    if (eng.tier === 4 && eng.verdict === "PASS") t4alerts++;
  });

  return (
    <div
      style={{
        fontFamily: "'IBM Plex Mono', monospace",
        background: "#0a0a0a",
        padding: "16px 20px",
      }}
    >
      {/* ── section header ── */}
      <div style={SECTION_HEADER}>
        ALL 24 ENGINES \u2014 LIVE STATUS
      </div>

      {/* ── grid ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 1,
          background: "#1f1f1f",
        }}
      >
        {ENGINE_ORDER.map((k) => {
          const eng = engines[k];

          /* missing engine placeholder */
          if (!eng) {
            return (
              <div
                key={k}
                style={{
                  background: "#0f0f0f",
                  padding: "10px 14px",
                  fontSize: 10,
                  color: "#444",
                  fontFamily: "'IBM Plex Mono', monospace",
                }}
              >
                <span style={{ color: "#555", fontSize: 9 }}>[{k.toUpperCase()}]</span>{" "}
                <span style={{ color: "#444" }}>No data</span>
              </div>
            );
          }

          const { name, tier, verdict, data } = eng;
          const isActive = verdict === "PASS" || verdict === "PARTIAL";
          const isT1Fail = tier === 1 && verdict === "FAIL";
          const isT4Active = tier === 4 && verdict === "PASS";
          const dimmed = !isActive && tier !== 1;
          const tierMeta = TIER_META[tier] || { label: "UNKNOWN", bg: "#444" };
          const signal = getSignalLine(k, eng);

          let borderLeft = "none";
          if (isT4Active) borderLeft = "2px solid #2196F3";
          if (isT1Fail) borderLeft = "2px solid #FF3D00";

          return (
            <div
              key={k}
              style={{
                background: "#0f0f0f",
                padding: "10px 14px",
                fontFamily: "'IBM Plex Mono', monospace",
                opacity: dimmed ? 0.4 : 1,
                borderLeft: borderLeft,
              }}
            >
              {/* Line 1: ID + Name */}
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ color: "#555", fontSize: 9 }}>[{k.toUpperCase()}]</span>
                <span style={{ color: "#FFB300", fontWeight: 600, fontSize: 11 }}>{name}</span>
              </div>

              {/* Line 2: Tier badge */}
              <div style={{ marginTop: 4 }}>
                <span
                  style={{
                    display: "inline-block",
                    padding: "1px 7px",
                    fontSize: 8,
                    fontWeight: 700,
                    letterSpacing: 1,
                    color: "#000",
                    background: tierMeta.bg,
                  }}
                >
                  {tierMeta.label}
                </span>
              </div>

              {/* Line 3: Status */}
              <div style={{ marginTop: 4, fontSize: 10 }}>
                <span style={{ color: "#555" }}>STATUS:</span>{" "}
                <span style={{ color: isActive ? "#00C853" : "#444" }}>
                  {isActive ? "ACTIVE" : "INACTIVE"}
                </span>
              </div>

              {/* Line 4: Signal */}
              <div style={{ marginTop: 3, fontSize: 10 }}>
                <span style={{ color: signal.color }}>{signal.text}</span>
              </div>

              {/* Line 5: Value */}
              <div style={{ marginTop: 3, fontSize: 10 }}>
                <span style={{ color: "#444" }}>VALUE:</span>{" "}
                <span style={{ color: "#E8E8E8" }}>{getValueLine(k, data || {})}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── bottom summary row ── */}
      <div
        style={{
          marginTop: 12,
          fontSize: 11,
          color: "#FFB300",
          letterSpacing: 1,
          fontFamily: "'IBM Plex Mono', monospace",
        }}
      >
        ACTIVE: {active}/24 | CALL: {calls} | PUT: {puts} | NEUTRAL: {neutral} | BIG MOVE: {t4alerts}
      </div>
    </div>
  );
}
