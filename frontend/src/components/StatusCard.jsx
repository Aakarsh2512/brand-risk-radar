const BAND_STYLES = {
  Watch: { bg: "#ebfbee", fg: "#2f9e44" },
  Elevated: { bg: "#fff4e6", fg: "#e8590c" },
  Critical: { bg: "#fff5f5", fg: "#c92a2a" },
};

export default function StatusCard({ brand, latest }) {
  if (!latest) return null;
  const style = BAND_STYLES[latest.risk_band] ?? BAND_STYLES.Watch;

  return (
    <div className="status-card" style={{ background: style.bg, borderColor: style.fg }}>
      <div className="status-brand">{brand}</div>
      <div className="status-score" style={{ color: style.fg }}>
        {latest.risk_score.toFixed(0)}
        <span className="status-score-max">/100</span>
      </div>
      <div className="status-band" style={{ color: style.fg }}>
        {latest.risk_band}
      </div>
      <div className="status-date">as of {latest.date}</div>
    </div>
  );
}
