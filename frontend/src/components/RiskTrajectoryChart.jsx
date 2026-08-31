import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const BAND_COLORS = { Watch: "#2f9e44", Elevated: "#e8590c", Critical: "#c92a2a" };

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="tooltip">
      <strong>{label}</strong>
      <div>
        risk: {d.risk_score.toFixed(1)} ({d.risk_band})
      </div>
      <div>drift: {d.drift_component.toFixed(0)}</div>
      <div>volume: {d.volume_component.toFixed(0)}</div>
      <div>sentiment: {d.sentiment_component.toFixed(0)}</div>
      {d.is_changepoint ? <div className="changepoint-flag">⚠ narrative changepoint</div> : null}
    </div>
  );
}

export default function RiskTrajectoryChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={40} stroke={BAND_COLORS.Elevated} strokeDasharray="4 4" />
        <ReferenceLine y={70} stroke={BAND_COLORS.Critical} strokeDasharray="4 4" />
        <Line
          type="monotone"
          dataKey="risk_score"
          stroke="#1971c2"
          strokeWidth={2}
          dot={(props) => {
            const isCp = props.payload.is_changepoint;
            return (
              <circle
                key={props.cx}
                cx={props.cx}
                cy={props.cy}
                r={isCp ? 6 : 3}
                fill={isCp ? "#c92a2a" : "#1971c2"}
              />
            );
          }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
