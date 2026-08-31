import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { getBrands, getDailyStats, getMentions, getTopics } from "./api";
import MentionsTable from "./components/MentionsTable";
import RiskTrajectoryChart from "./components/RiskTrajectoryChart";
import StatusCard from "./components/StatusCard";
import TopicList from "./components/TopicList";

export default function App() {
  const [brands, setBrands] = useState([]);
  const [brand, setBrand] = useState(null);
  const [dailyStats, setDailyStats] = useState([]);
  const [topics, setTopics] = useState([]);
  const [mentions, setMentions] = useState([]);
  const [selectedTopicId, setSelectedTopicId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getBrands()
      .then((b) => {
        setBrands(b);
        setBrand(b[0] ?? null);
      })
      .catch(() => setError("Could not reach the API. Is uvicorn running on :8000?"));
  }, []);

  useEffect(() => {
    if (!brand) return;
    setError(null);
    Promise.all([getDailyStats(brand), getTopics(brand), getMentions(brand)])
      .then(([stats, topicsRes, mentionsRes]) => {
        setDailyStats(stats);
        setTopics(topicsRes);
        setMentions(mentionsRes);
        setSelectedTopicId(null);
      })
      .catch(() => setError(`No data yet for ${brand}. Run the pipeline first.`));
  }, [brand]);

  const latest = dailyStats[dailyStats.length - 1];
  const filteredMentions = useMemo(
    () =>
      selectedTopicId === null
        ? mentions
        : mentions.filter((m) => m.topic_id === selectedTopicId),
    [mentions, selectedTopicId]
  );

  return (
    <div className="app">
      <header>
        <h1>Brand Risk Radar</h1>
        {brands.length > 1 && (
          <select value={brand ?? ""} onChange={(e) => setBrand(e.target.value)}>
            {brands.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        )}
      </header>

      {error && <p className="error-banner">{error}</p>}

      {latest && (
        <div className="top-row">
          <StatusCard brand={brand} latest={latest} />
          <div className="chart-panel">
            <h2>Risk trajectory</h2>
            <RiskTrajectoryChart data={dailyStats} />
          </div>
        </div>
      )}

      <section>
        <h2>Topics</h2>
        <p className="hint">Click a topic to filter mentions below.</p>
        <TopicList topics={topics} onSelect={setSelectedTopicId} selectedTopicId={selectedTopicId} />
      </section>

      <section>
        <h2>
          Mentions{" "}
          {selectedTopicId !== null && (
            <button onClick={() => setSelectedTopicId(null)}>clear filter</button>
          )}
        </h2>
        <MentionsTable mentions={filteredMentions} />
      </section>
    </div>
  );
}
