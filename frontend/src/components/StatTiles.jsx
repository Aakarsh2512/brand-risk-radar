import { BAND_ROLE } from "../theme";

function Tile({ label, value, unit, sub, children }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      {children ?? (
        <div className="stat-value num">
          {value}
          {unit ? <span className="unit">{unit}</span> : null}
        </div>
      )}
      {sub ? <div className="stat-sub">{sub}</div> : null}
    </div>
  );
}

export default function StatTiles({ latest, peak }) {
  if (!latest) return null;

  const band = latest.risk_band ?? "Watch";
  const drift = latest.drift_z ?? 0;
  const sentiment = latest.mean_sentiment ?? 0;
  const sentimentWord = sentiment > 0.05 ? "net positive" : sentiment < -0.05 ? "net negative" : "neutral";

  return (
    <div className="stat-grid">
      <Tile label="Risk score" value={Math.round(latest.risk_score ?? 0)} unit="/100" />

      <Tile label="Status" sub={`as of ${latest.date}`}>
        <div className="stat-value" style={{ fontSize: "1.375rem" }}>
          <span className="band">
            <i className={`band-dot ${BAND_ROLE[band] ?? "good"}`} />
            {band}
          </span>
        </div>
      </Tile>

      <Tile
        label="Narrative drift"
        value={`${drift >= 0 ? "+" : ""}${drift.toFixed(1)}`}
        unit="σ"
        sub={
          peak
            ? `peak ${peak.drift_z >= 0 ? "+" : ""}${peak.drift_z.toFixed(1)}σ on ${peak.date}`
            : "vs this brand's own baseline"
        }
      />

      <Tile
        label="Coverage (7d)"
        value={latest.window_mentions ?? 0}
        sub={`sentiment ${sentimentWord}`}
      />
    </div>
  );
}
