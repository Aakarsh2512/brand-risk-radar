export default function TopicList({ topics, onSelect, selectedTopicId }) {
  if (!topics.length) return <p className="empty-note">No topics extracted yet.</p>;

  return (
    <table className="topic-table">
      <thead>
        <tr>
          <th style={{ width: "5.5rem" }}>Topic</th>
          <th>Keywords</th>
          <th className="num-cell">Articles</th>
        </tr>
      </thead>
      <tbody>
        {topics.map((t) => (
          <tr
            key={t.topic_id}
            className={t.topic_id === selectedTopicId ? "selected" : ""}
            onClick={() => onSelect(t.topic_id === selectedTopicId ? null : t.topic_id)}
          >
            <td className="topic-id">{t.topic_id === -1 ? "unsorted" : `#${t.topic_id}`}</td>
            <td className="topic-keywords">{t.keywords}</td>
            <td className="num-cell">{t.size}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
