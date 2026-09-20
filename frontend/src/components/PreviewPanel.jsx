import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useThemeColors } from "../theme";

const fmtDay = (iso) =>
  new Date(iso + "T00:00:00Z").toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });

function VolumeTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tooltip">
      <div className="tooltip-date">{fmtDay(label)}</div>
      <div className="tooltip-row">
        <span>Articles</span>
        <strong>{payload[0].value}</strong>
      </div>
    </div>
  );
}

export default function PreviewPanel({ preview, onTrackedClick }) {
  const colors = useThemeColors();
  const { brand, article_count, daily_volume, articles, tracked } = preview;

  return (
    <>
      <div className="notice">
        <strong>Live preview — no risk score yet.</strong>
        <p>
          Narrative drift is measured against a brand's <em>own</em> normal rate of change, so
          it needs about two weeks of history before it means anything. This is what{" "}
          <strong>{brand}</strong> coverage looks like right now.
          {tracked && (
            <>
              {" "}
              {brand} is already tracked —{" "}
              <button className="link-button" onClick={onTrackedClick}>
                open the full analysis
              </button>
              .
            </>
          )}
        </p>
      </div>

      <div className="stat-grid preview-stats">
        <div className="stat">
          <div className="stat-label">Articles found</div>
          <div className="stat-value num">{article_count}</div>
          <div className="stat-sub">headline mentions, most recent first</div>
        </div>
        <div className="stat">
          <div className="stat-label">Days covered</div>
          <div className="stat-value num">{daily_volume.length}</div>
          <div className="stat-sub">
            {daily_volume.length
              ? `${fmtDay(daily_volume[0].date)} – ${fmtDay(daily_volume.at(-1).date)}`
              : "—"}
          </div>
        </div>
      </div>

      {daily_volume.length > 1 && (
        <section className="card chart-card">
          <div className="card-head">
            <h2>Coverage volume</h2>
            <span className="hint">articles per day</span>
          </div>
          <div className="chart-body">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={daily_volume} margin={{ top: 8, right: 16, left: 8, bottom: 4 }}>
                <CartesianGrid stroke={colors.grid} vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={fmtDay}
                  tick={{ fontSize: 11, fill: colors.axis }}
                  tickLine={false}
                  axisLine={{ stroke: colors.grid }}
                  minTickGap={20}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 11, fill: colors.axis }}
                  tickLine={false}
                  axisLine={false}
                  width={28}
                />
                <Tooltip content={<VolumeTooltip />} cursor={{ fill: colors.grid, fillOpacity: 0.4 }} />
                <Bar dataKey="count" fill={colors.series} radius={[4, 4, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      <section className="card section">
        <div className="card-head">
          <h2>Latest coverage</h2>
          <span className="hint">{articles.length} headlines</span>
        </div>
        {articles.length ? (
          <table className="mentions-table">
            <thead>
              <tr>
                <th>Headline</th>
                <th>Source</th>
                <th className="num-cell">Published</th>
              </tr>
            </thead>
            <tbody>
              {articles.map((a) => (
                <tr key={a.url}>
                  <td>
                    <a href={a.url} target="_blank" rel="noreferrer">
                      {a.title}
                    </a>
                  </td>
                  <td className="source-cell">{a.source_name}</td>
                  <td className="num-cell date-cell">
                    {new Date(a.published_at).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty-note">
            No recent headlines name {brand}. Try a more common spelling, or a brand with more
            English-language news coverage.
          </p>
        )}
      </section>
    </>
  );
}
