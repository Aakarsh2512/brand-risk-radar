const SENTIMENT_COLOR = { positive: "#2f9e44", neutral: "#868e96", negative: "#c92a2a" };

export default function MentionsTable({ mentions }) {
  if (!mentions.length) return <p className="empty-note">No mentions match this filter.</p>;

  return (
    <table className="mentions-table">
      <thead>
        <tr>
          <th>Title</th>
          <th>Source</th>
          <th>Sentiment</th>
          <th>Published</th>
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
            <td>{m.source_name}</td>
            <td style={{ color: SENTIMENT_COLOR[m.sentiment_label] ?? "#868e96" }}>
              {m.sentiment_label}
            </td>
            <td>{new Date(m.published_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
