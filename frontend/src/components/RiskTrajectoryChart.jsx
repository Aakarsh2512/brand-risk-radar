import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useThemeColors } from "../theme";

const fmtDate = (iso) =>
  new Date(iso + "T00:00:00Z").toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });

function ChartTooltip({ active, payload, label, colors }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="tooltip">
      <div className="tooltip-date">{fmtDate(label)}</div>
      <div className="tooltip-row">
        <span>Risk</span>
        <strong>
          {d.risk_score?.toFixed(0)} · {d.risk_band}
        </strong>
      </div>
      <div className="tooltip-row">
        <span>Narrative drift</span>
        <strong>{d.drift_z >= 0 ? "+" : ""}{(d.drift_z ?? 0).toFixed(1)}σ</strong>
      </div>
      <div className="tooltip-row">
        <span>Articles (7d)</span>
        <strong>{d.window_mentions ?? "—"}</strong>
      </div>
      {d.is_changepoint ? (
        <div className="tooltip-flag" style={{ color: colors.critical }}>
          Narrative changepoint
        </div>
      ) : null}
    </div>
  );
}

// Only changepoints get a visible marker -- a dot on every point is noise.
function PointMarker({ cx, cy, payload, colors }) {
  if (!payload.is_changepoint) return null;
  return (
    <circle
      cx={cx}
      cy={cy}
      r={5}
      fill={colors.critical}
      stroke={colors.surface}
      strokeWidth={2}
    />
  );
}

export default function RiskTrajectoryChart({ data }) {
  const colors = useThemeColors();

  return (
    <>
      <div className="chart-body">
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 4 }}>
            <defs>
              <linearGradient id="riskFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={colors.series} stopOpacity={0.18} />
                <stop offset="100%" stopColor={colors.series} stopOpacity={0.01} />
              </linearGradient>
            </defs>

            <CartesianGrid stroke={colors.grid} strokeDasharray="0" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={fmtDate}
              tick={{ fontSize: 11, fill: colors.axis }}
              tickLine={false}
              axisLine={{ stroke: colors.grid }}
              minTickGap={24}
            />
            <YAxis
              domain={[0, 100]}
              ticks={[0, 25, 50, 75, 100]}
              tick={{ fontSize: 11, fill: colors.axis }}
              tickLine={false}
              axisLine={false}
              width={32}
            />
            <Tooltip
              content={<ChartTooltip colors={colors} />}
              cursor={{ stroke: colors.axis, strokeOpacity: 0.35, strokeDasharray: "3 3" }}
            />

            <ReferenceLine y={40} stroke={colors.serious} strokeDasharray="4 4" strokeWidth={1.5} />
            <ReferenceLine y={70} stroke={colors.critical} strokeDasharray="4 4" strokeWidth={1.5} />

            <Area
              type="monotone"
              dataKey="risk_score"
              stroke="none"
              fill="url(#riskFill)"
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="risk_score"
              stroke={colors.series}
              strokeWidth={2}
              dot={<PointMarker colors={colors} />}
              activeDot={{ r: 5, fill: colors.series, stroke: colors.surface, strokeWidth: 2 }}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-legend">
        <span>
          <i className="legend-rule" style={{ color: colors.serious }} /> Elevated threshold (40)
        </span>
        <span>
          <i className="legend-rule" style={{ color: colors.critical }} /> Critical threshold (70)
        </span>
        <span>
          <i className="legend-dot" style={{ background: colors.critical }} /> Narrative changepoint
        </span>
      </div>
    </>
  );
}
