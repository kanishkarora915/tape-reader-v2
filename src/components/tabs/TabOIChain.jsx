import React, { useState, useMemo } from "react";

/* ── helpers ── */
function formatOI(n) {
  if (n == null || isNaN(n)) return "—";
  if (n >= 10000000) return `${(n / 10000000).toFixed(2)}Cr`;
  if (n >= 100000) return `${(n / 100000).toFixed(1)}L`;
  return n.toLocaleString("en-IN");
}

function formatPct(n) {
  if (n == null || isNaN(n)) return "—";
  const sign = n >= 0 ? "+" : "";
  return `${sign}${n.toFixed(1)}%`;
}

/* ── component ── */
export default function TabOIChain({ chain, engines }) {
  const [selectedIndex, setSelectedIndex] = useState("NIFTY");

  /* derived data */
  const pcr = engines?.e06?.data?.pcr ?? "—";
  const maxPain = engines?.e10?.data?.max_pain ?? "—";
  const callWall = engines?.e05?.data?.call_wall ?? "—";
  const putWall = engines?.e05?.data?.put_wall ?? "—";

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
        `Call writers unwinding at ${minCeChg.strike} (${formatPct(minCeChg.val)}) — potential breakout zone.`
      );
    if (minPeChg.val < 0)
      parts.push(
        `Put writers covering at ${minPeChg.strike} (${formatPct(minPeChg.val)}) — support weakening.`
      );
    if (maxPain !== "—") parts.push(`Max pain at ${maxPain} — price gravitates here near expiry.`);
    return parts.join(" ");
  }, [rows, maxPain]);

  /* no data */
  if (!chain || !Object.keys(chain).length) {
    return (
      <div
        style={{
          fontFamily: "monospace",
          background: "#0a0a0a",
          color: "#444444",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: 400,
          fontSize: 12,
        }}
      >
        Login with Kite to see live OI chain
      </div>
    );
  }

  const indices = Object.keys(chain);

  return (
    <div style={{ fontFamily: "monospace", background: "#0a0a0a", color: "#E8E8E8", width: "100%" }}>
      {/* ── panel ── */}
      <div style={{ background: "#0f0f0f", border: "1px solid #1f1f1f", borderRadius: 0, padding: 8 }}>

        {/* header */}
        <div
          style={{
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#FFB300",
            marginBottom: 6,
          }}
        >
          LIVE OPTIONS CHAIN — {selectedIndex} WEEKLY EXPIRY
        </div>

        {/* sub-header stats */}
        <div
          style={{
            display: "flex",
            gap: 16,
            flexWrap: "wrap",
            fontSize: 10,
            marginBottom: 8,
            lineHeight: 1.6,
          }}
        >
          <span>
            <span style={{ color: "#444444" }}>PCR:</span>{" "}
            <span style={{ color: "#FFB300" }}>{pcr}</span>
          </span>
          <span style={{ color: "#444444" }}>|</span>
          <span>
            <span style={{ color: "#444444" }}>MAX PAIN:</span>{" "}
            <span style={{ color: "#FFB300" }}>{maxPain}</span>
          </span>
          <span style={{ color: "#444444" }}>|</span>
          <span>
            <span style={{ color: "#444444" }}>CALL WALL:</span>{" "}
            <span style={{ color: "#FFB300" }}>{callWall}</span>
          </span>
          <span style={{ color: "#444444" }}>|</span>
          <span>
            <span style={{ color: "#444444" }}>PUT WALL:</span>{" "}
            <span style={{ color: "#FFB300" }}>{putWall}</span>
          </span>
          <span style={{ color: "#444444" }}>|</span>
          <span>
            <span style={{ color: "#444444" }}>TOTAL CALL OI:</span>{" "}
            <span style={{ color: "#FFB300" }}>{formatOI(totalCallOI)}</span>
          </span>
          <span style={{ color: "#444444" }}>|</span>
          <span>
            <span style={{ color: "#444444" }}>TOTAL PUT OI:</span>{" "}
            <span style={{ color: "#FFB300" }}>{formatOI(totalPutOI)}</span>
          </span>
        </div>

        {/* index tabs */}
        {indices.length > 1 && (
          <div style={{ display: "flex", gap: 4, marginBottom: 8 }}>
            {indices.map((idx) => (
              <button
                key={idx}
                onClick={() => setSelectedIndex(idx)}
                style={{
                  fontFamily: "monospace",
                  fontSize: 9,
                  fontWeight: 700,
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  padding: "2px 8px",
                  border: "1px solid #1f1f1f",
                  borderRadius: 0,
                  background: selectedIndex === idx ? "#1a1400" : "#0f0f0f",
                  color: selectedIndex === idx ? "#FFB300" : "#444444",
                  cursor: "pointer",
                  outline: "none",
                  boxShadow: "none",
                }}
              >
                {idx}
              </button>
            ))}
          </div>
        )}

        {/* table */}
        <div style={{ overflowX: "auto" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontFamily: "monospace",
              fontSize: 10,
            }}
          >
            <thead>
              <tr
                style={{
                  background: "#0f0f0f",
                  color: "#444444",
                  fontSize: 9,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  position: "sticky",
                  top: 0,
                  zIndex: 2,
                }}
              >
                {["CE OI", "CE OI \u0394", "CE LTP", "CE BAR", "STRIKE", "PUT BAR", "PUT LTP", "PE OI \u0394", "PE OI"].map(
                  (h) => (
                    <th
                      key={h}
                      style={{
                        padding: "4px 4px",
                        fontWeight: 600,
                        borderBottom: "1px solid #1f1f1f",
                        textAlign: h === "STRIKE" ? "center" : h.startsWith("CE") ? "right" : "left",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => {
                const isATM = !!row.atm;
                const isMP = row.strike === maxPain;
                let rowBg = "transparent";
                let rowColor = "#E8E8E8";
                if (isATM) {
                  rowBg = "#1a1400";
                  rowColor = "#FFB300";
                }
                if (isMP) {
                  rowBg = "#001020";
                  rowColor = "#2196F3";
                }

                const ceChg = Number(row.ce_chg) || 0;
                const peChg = Number(row.pe_chg) || 0;
                const ceBarW = ((Number(row.ce_oi) || 0) / maxOI) * 100;
                const peBarW = ((Number(row.pe_oi) || 0) / maxOI) * 100;

                return (
                  <tr
                    key={row.strike ?? i}
                    className="data-row"
                    style={{ background: rowBg, color: rowColor }}
                    onMouseEnter={(e) => {
                      if (!isATM && !isMP) e.currentTarget.style.background = "#161616";
                    }}
                    onMouseLeave={(e) => {
                      if (!isATM && !isMP) e.currentTarget.style.background = "transparent";
                    }}
                  >
                    {/* CE OI */}
                    <td style={{ padding: "2px 4px", textAlign: "right", whiteSpace: "nowrap" }}>
                      {formatOI(row.ce_oi)}
                    </td>
                    {/* CE OI delta */}
                    <td
                      style={{
                        padding: "2px 4px",
                        textAlign: "right",
                        fontSize: 10,
                        color: ceChg >= 0 ? "#00C853" : "#FF3D00",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {formatPct(row.ce_chg)}
                    </td>
                    {/* CE LTP */}
                    <td style={{ padding: "2px 4px", textAlign: "right", whiteSpace: "nowrap" }}>
                      {row.ce_ltp ?? "—"}
                    </td>
                    {/* CE BAR */}
                    <td style={{ padding: "2px 4px", textAlign: "right", width: 80 }}>
                      <div style={{ display: "flex", justifyContent: "flex-end" }}>
                        <div
                          className="oi-bar call"
                          style={{
                            width: `${ceBarW}%`,
                            height: 6,
                            background: "#FF3D00",
                            borderRadius: 0,
                            minWidth: ceBarW > 0 ? 1 : 0,
                          }}
                        />
                      </div>
                    </td>
                    {/* STRIKE */}
                    <td
                      style={{
                        padding: "2px 4px",
                        textAlign: "center",
                        fontWeight: 700,
                        whiteSpace: "nowrap",
                        background: isATM ? "#1a1400" : isMP ? "#001020" : "transparent",
                        color: isATM ? "#FFB300" : isMP ? "#2196F3" : "#E8E8E8",
                      }}
                    >
                      {isATM && <span style={{ color: "#FFB300", marginRight: 2 }}>{"\u2605"}</span>}
                      {row.strike}
                      {isMP && (
                        <span
                          style={{
                            color: "#2196F3",
                            fontSize: 8,
                            marginLeft: 3,
                            background: "#001020",
                            padding: "0 2px",
                          }}
                        >
                          MP
                        </span>
                      )}
                      {row.strike === callWall && <span style={{ marginLeft: 2 }}>{"\uD83E\uDDF1"}</span>}
                      {row.strike === putWall && <span style={{ marginLeft: 2 }}>{"\uD83D\uDEE1"}</span>}
                    </td>
                    {/* PUT BAR */}
                    <td style={{ padding: "2px 4px", textAlign: "left", width: 80 }}>
                      <div style={{ display: "flex", justifyContent: "flex-start" }}>
                        <div
                          className="oi-bar put"
                          style={{
                            width: `${peBarW}%`,
                            height: 6,
                            background: "#00C853",
                            borderRadius: 0,
                            minWidth: peBarW > 0 ? 1 : 0,
                          }}
                        />
                      </div>
                    </td>
                    {/* PUT LTP */}
                    <td style={{ padding: "2px 4px", textAlign: "left", whiteSpace: "nowrap" }}>
                      {row.pe_ltp ?? "—"}
                    </td>
                    {/* PE OI delta */}
                    <td
                      style={{
                        padding: "2px 4px",
                        textAlign: "left",
                        fontSize: 10,
                        color: peChg >= 0 ? "#00C853" : "#FF3D00",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {formatPct(row.pe_chg)}
                    </td>
                    {/* PE OI */}
                    <td style={{ padding: "2px 4px", textAlign: "left", whiteSpace: "nowrap" }}>
                      {formatOI(row.pe_oi)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* OI interpretation */}
        {interpretation && (
          <div style={{ marginTop: 10 }}>
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "#FFB300",
                marginBottom: 4,
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
    </div>
  );
}
