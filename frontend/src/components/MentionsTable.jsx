const SENTIMENT_ROLE = { positive: "good", neutral: "neutral", negative: "critical" };

const fmtDate = (iso) =>
  new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });

export default function MentionsTable({ mentions }) {
  if (!mentions.length) return <p className="empty-note">No articles match this filter.</p>;

  return (
    <table className="mentions-table">
      <thead>
        <tr>
          <th>Headline</th>
          <th>Source</th>
          <th style={{ width: "7rem" }}>Sentiment</th>
          <th className="num-cell">Published</th>
        </tr>
      </thead>
      <tbody>
        {mentions.map((m) => (
          <tr key={m.url}>
            <td>
              <a href={m.url} target="_blank" rel="noreferrer">
                {m.title}
              </a>
            </td>
            <td className="source-cell">{m.source_name}</td>
            <td>
              {/* the word carries the meaning; the dot only reinforces it */}
              <span className="sentiment">
                <i className={`band-dot ${SENTIMENT_ROLE[m.sentiment_label] ?? "neutral"}`} />
                {m.sentiment_label ?? "—"}
              </span>
            </td>
            <td className="num-cell date-cell">{fmtDate(m.published_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
