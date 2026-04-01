import React, { useState, useMemo } from "react";

/* ── helpers ── */
function formatOI(n) {
  if (n == null || isNaN(n)) return "\u2014";
  if (n >= 10000000) return `${(n / 10000000).toFixed(2)}Cr`;
  if (n >= 100000) return `${(n / 100000).toFixed(1)}L`;
  return n.toLocaleString("en-IN");
}

function formatPct(n) {
  if (n == null || isNaN(n)) return "\u2014";
  const sign = n >= 0 ? "+" : "";
  return `${sign}${n.toFixed(1)}%`;
}

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

const GRID_COLS = "1fr 70px 70px 80px 90px 80px 70px 70px 1fr";

/* ── component ── */
export default function TabOIChain({ chain, engines }) {
  const [selectedIndex, setSelectedIndex] = useState("NIFTY");

  /* derived data */
  const pcr = engines?.e06?.data?.pcr ?? "\u2014";
  const maxPain = engines?.e10?.data?.max_pain ?? "\u2014";
  const callWall = engines?.e05?.data?.call_wall ?? "\u2014";
  const putWall = engines?.e05?.data?.put_wall ?? "\u2014";

  const rows = chain?.[selectedIndex] ?? [];

  const { maxOI, totalCallOI, totalPutOI } = useMemo(() => {
    let mx = 1;
    let tc = 0;
    let tp = 0;
    for (const r of rows) {
      const ce = Number(r.ce_oi) || 0;
      const pe = Number(r.pe_oi) || 0;
      if (ce > mx) mx = ce;
      if (pe > mx) mx = pe;
      tc += ce;
      tp += pe;
    }
    return { maxOI: mx, totalCallOI: tc, totalPutOI: tp };
  }, [rows]);

  /* interpretation generator */
  const interpretation = useMemo(() => {
    if (!rows.length) return "";
    let maxCeChg = { strike: 0, val: -Infinity };
    let maxPeChg = { strike: 0, val: -Infinity };
    let minCeChg = { strike: 0, val: Infinity };
    let minPeChg = { strike: 0, val: Infinity };
    for (const r of rows) {
      const ceC = Number(r.ce_chg) || 0;
      const peC = Number(r.pe_chg) || 0;
      if (ceC > maxCeChg.val) maxCeChg = { strike: r.strike, val: ceC };
      if (peC > maxPeChg.val) maxPeChg = { strike: r.strike, val: peC };
      if (ceC < minCeChg.val) minCeChg = { strike: r.strike, val: ceC };
      if (peC < minPeChg.val) minPeChg = { strike: r.strike, val: peC };
    }
    const parts = [];
    parts.push(
      `Highest CALL OI build-up at ${maxCeChg.strike} (${formatPct(maxCeChg.val)}), indicating strong resistance.`
    );
    parts.push(
      `Highest PUT OI build-up at ${maxPeChg.strike} (${formatPct(maxPeChg.val)}), indicating strong support.`
    );
    if (minCeChg.val < 0)
      parts.push(
        `Call writers unwinding at ${minCeChg.strike} (${formatPct(minCeChg.val)}) \u2014 potential breakout zone.`
      );
    if (minPeChg.val < 0)
      parts.push(
        `Put writers covering at ${minPeChg.strike} (${formatPct(minPeChg.val)}) \u2014 support weakening.`
      );
    if (maxPain !== "\u2014")
      parts.push(`Max pain at ${maxPain} \u2014 price gravitates here near expiry.`);
    return parts.join(" ");
  }, [rows, maxPain]);

  /* no data */
  if (!chain || !Object.keys(chain).length) {
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
        Connect to Kite to view live option chain
      </div>
    );
  }

  const indices = ["NIFTY", "BANKNIFTY", "SENSEX"];

  const statItems = [
    { label: "PCR", value: pcr },
    { label: "MAX PAIN", value: maxPain },
    { label: "CALL WALL", value: callWall },
    { label: "PUT WALL", value: putWall },
    { label: "TOTAL CE OI", value: formatOI(totalCallOI) },
    { label: "TOTAL PE OI", value: formatOI(totalPutOI) },
  ];

  const headerCols = [
    { label: "CE OI", align: "right" },
    { label: "CE \u0394", align: "right" },
    { label: "CE LTP", align: "right" },
    { label: "CE BAR", align: "right" },
    { label: "STRIKE", align: "center" },
    { label: "PUT BAR", align: "left" },
    { label: "PUT LTP", align: "left" },
    { label: "PE \u0394", align: "left" },
    { label: "PE OI", align: "left" },
  ];

  return (
    <div
      style={{
        fontFamily: "'IBM Plex Mono', monospace",
        background: "#0a0a0a",
        color: "#E8E8E8",
        padding: "16px 20px",
        width: "100%",
      }}
    >
      {/* ── section header ── */}
      <div style={SECTION_HEADER}>
        LIVE OPTIONS CHAIN \u2014 {selectedIndex} WEEKLY EXPIRY
      </div>

      {/* ── sub-header stats row ── */}
      <div
        style={{
          display: "flex",
          gap: 24,
          fontSize: 10,
          marginBottom: 12,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        {statItems.map((item, i) => (
          <React.Fragment key={item.label}>
            {i > 0 && (
              <span style={{ color: "#1f1f1f", fontSize: 10 }}>|</span>
            )}
            <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
              <span style={{ color: "#555" }}>{item.label}</span>
              <span style={{ color: "#FFB300" }}>{item.value}</span>
            </span>
          </React.Fragment>
        ))}
      </div>

      {/* ── index tabs ── */}
      <div style={{ display: "flex", gap: 0, marginBottom: 12 }}>
        {indices.map((idx) => (
          <button
            key={idx}
            onClick={() => setSelectedIndex(idx)}
            style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 9,
              fontWeight: 700,
              letterSpacing: 1,
              textTransform: "uppercase",
              padding: "4px 12px",
              border: "1px solid #1f1f1f",
              borderRadius: 0,
              boxShadow: "none",
              background: selectedIndex === idx ? "#1a1400" : "#0f0f0f",
              color: selectedIndex === idx ? "#FFB300" : "#555",
              cursor: "pointer",
              outline: "none",
              marginRight: -1,
            }}
          >
            {idx}
          </button>
        ))}
      </div>

      {/* ── table header ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: GRID_COLS,
          background: "#0f0f0f",
          padding: "6px 0",
          borderBottom: "1px solid #1f1f1f",
        }}
      >
        {headerCols.map((col) => (
          <div
            key={col.label}
            style={{
              color: "#555",
              fontSize: 9,
              letterSpacing: 1,
              textTransform: "uppercase",
              fontWeight: 600,
              textAlign: col.align,
              padding: "0 4px",
            }}
          >
            {col.label}
          </div>
        ))}
      </div>

      {/* ── data rows ── */}
      <div style={{ overflowY: "auto" }}>
        {rows.map((row, i) => {
          const isATM = !!row.atm;
          const isMP = row.strike == maxPain;
          const isCW = row.strike == callWall;
          const isPW = row.strike == putWall;

          const ceChg = Number(row.ce_chg) || 0;
          const peChg = Number(row.pe_chg) || 0;
          const ceBarW = ((Number(row.ce_oi) || 0) / maxOI) * 100;
          const peBarW = ((Number(row.pe_oi) || 0) / maxOI) * 100;

          let rowBg = "transparent";
          if (isATM) rowBg = "#1a1400";
          if (isMP) rowBg = "#001020";

          let strikeSuffix = "";
          if (isMP) strikeSuffix = " MP";
          if (isCW) strikeSuffix += " \uD83E\uDDF1";
          if (isPW) strikeSuffix += " \uD83D\uDEE1";

          return (
            <div
              key={row.strike ?? i}
              style={{
                display: "grid",
                gridTemplateColumns: GRID_COLS,
                padding: "4px 0",
                borderBottom: "1px solid #141414",
                fontSize: 11,
                background: rowBg,
              }}
              onMouseEnter={(e) => {
                if (!isATM && !isMP) e.currentTarget.style.background = "#161616";
              }}
              onMouseLeave={(e) => {
                if (!isATM && !isMP) e.currentTarget.style.background = "transparent";
              }}
            >
              {/* CE OI */}
              <div style={{ color: "#E8E8E8", textAlign: "right", padding: "0 4px" }}>
                {formatOI(row.ce_oi)}
              </div>

              {/* CE delta */}
              <div
                style={{
                  color: ceChg >= 0 ? "#00C853" : "#FF3D00",
                  textAlign: "right",
                  padding: "0 4px",
                }}
              >
                {formatPct(row.ce_chg)}
              </div>

              {/* CE LTP */}
              <div style={{ color: "#E8E8E8", textAlign: "right", padding: "0 4px" }}>
                {row.ce_ltp ?? "\u2014"}
              </div>

              {/* CE BAR */}
              <div style={{ padding: "0 4px", display: "flex", justifyContent: "flex-end", alignItems: "center" }}>
                <div
                  style={{
                    width: `${ceBarW}%`,
                    height: 12,
                    background: "#FF3D00",
                    minWidth: ceBarW > 0 ? 1 : 0,
                  }}
                />
              </div>

              {/* STRIKE */}
              <div
                style={{
                  textAlign: "center",
                  fontWeight: 700,
                  padding: "0 4px",
                  color: isATM ? "#FFB300" : isMP ? "#2196F3" : "#E8E8E8",
                  background: isATM ? "#1a1400" : isMP ? "#001020" : "transparent",
                }}
              >
                {isATM && "\u2605 "}
                {row.strike}
                {strikeSuffix}
              </div>

              {/* PUT BAR */}
              <div style={{ padding: "0 4px", display: "flex", justifyContent: "flex-start", alignItems: "center" }}>
                <div
                  style={{
                    width: `${peBarW}%`,
                    height: 12,
                    background: "#00C853",
                    minWidth: peBarW > 0 ? 1 : 0,
                  }}
                />
              </div>

              {/* PUT LTP */}
              <div style={{ color: "#E8E8E8", textAlign: "left", padding: "0 4px" }}>
                {row.pe_ltp ?? "\u2014"}
              </div>

              {/* PE delta */}
              <div
                style={{
                  color: peChg >= 0 ? "#00C853" : "#FF3D00",
                  textAlign: "left",
                  padding: "0 4px",
                }}
              >
                {formatPct(row.pe_chg)}
              </div>

              {/* PE OI */}
              <div style={{ color: "#E8E8E8", textAlign: "left", padding: "0 4px" }}>
                {formatOI(row.pe_oi)}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── OI interpretation ── */}
      {interpretation && (
        <div style={{ marginTop: 16 }}>
          <div
            style={{
              fontSize: 10,
              color: "#FFB300",
              fontWeight: 600,
              letterSpacing: 3,
              textTransform: "uppercase",
              borderBottom: "1px solid #1f1f1f",
              paddingBottom: 8,
              marginBottom: 12,
            }}
          >
            OI INTERPRETATION:
          </div>
          <div
            style={{
              fontSize: 10,
              color: "#7A5600",
              fontStyle: "italic",
              lineHeight: 1.8,
            }}
          >
            {interpretation}
          </div>
        </div>
      )}
    </div>
  );
}
