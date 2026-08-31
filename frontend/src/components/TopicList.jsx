export default function TopicList({ topics, onSelect, selectedTopicId }) {
  return (
    <table className="topic-table">
      <thead>
        <tr>
          <th>Topic</th>
          <th>Keywords</th>
          <th>Mentions</th>
        </tr>
      </thead>
      <tbody>
        {topics.map((t) => (
          <tr
            key={t.topic_id}
            className={t.topic_id === selectedTopicId ? "selected" : ""}
            onClick={() => onSelect(t.topic_id)}
          >
            <td>{t.topic_id === -1 ? "(outliers)" : `#${t.topic_id}`}</td>
            <td>{t.keywords}</td>
            <td>{t.size}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
