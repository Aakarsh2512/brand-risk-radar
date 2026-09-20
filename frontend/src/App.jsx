import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { getBrands, getDailyStats, getMentions, getPreview, getTopics } from "./api";
import BrandSearch from "./components/BrandSearch";
import MentionsTable from "./components/MentionsTable";
import PreviewPanel from "./components/PreviewPanel";
import RiskTrajectoryChart from "./components/RiskTrajectoryChart";
import StatTiles from "./components/StatTiles";
import TopicList from "./components/TopicList";

// Shein is the clearest worked example in the current data -- its coverage
// pivots hard onto a product-safety recall, which is exactly what the drift
// signal exists to catch. Landing there beats opening on a quiet brand.
const PREFERRED_BRAND = "Shein";

export default function App() {
  const [brands, setBrands] = useState([]);
  const [brand, setBrand] = useState(null);
  const [dailyStats, setDailyStats] = useState([]);
  const [topics, setTopics] = useState([]);
  const [mentions, setMentions] = useState([]);
  const [selectedTopicId, setSelectedTopicId] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState(null);
  const [searching, setSearching] = useState(false);

  // Searching a brand we already track should open the real analysis rather
  // than a thinner live preview of it.
  const handleSearch = (name) => {
    const match = brands.find((b) => b.toLowerCase() === name.toLowerCase());
    if (match) {
      setPreview(null);
      setBrand(match);
      return;
    }
    setSearching(true);
    setError(null);
    getPreview(name)
      .then(setPreview)
      .catch((e) =>
        setError(e?.response?.data?.detail ?? `Could not look up "${name}".`)
      )
      .finally(() => setSearching(false));
  };

  useEffect(() => {
    getBrands()
      .then((list) => {
        setBrands(list);
        setBrand(list.includes(PREFERRED_BRAND) ? PREFERRED_BRAND : list[0] ?? null);
      })
      .catch(() => {
        setError("Could not reach the API. It sleeps on the free tier — give it up to a minute.");
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!brand) return;
    setError(null);
    setLoading(true);
    Promise.all([getDailyStats(brand), getTopics(brand), getMentions(brand)])
      .then(([stats, topicsRes, mentionsRes]) => {
        setDailyStats(stats);
        setTopics(topicsRes);
        setMentions(mentionsRes);
        setSelectedTopicId(null);
      })
      .catch(() => setError(`No data yet for ${brand}.`))
      .finally(() => setLoading(false));
  }, [brand]);

  const latest = dailyStats[dailyStats.length - 1];
  const peak = useMemo(() => {
    const scored = dailyStats.filter((d) => typeof d.drift_z === "number");
    if (!scored.length) return null;
    return scored.reduce((a, b) => (b.drift_z > a.drift_z ? b : a));
  }, [dailyStats]);

  const filteredMentions = useMemo(
    () =>
      selectedTopicId === null
        ? mentions
        : mentions.filter((m) => m.topic_id === selectedTopicId),
    [mentions, selectedTopicId]
  );

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Brand Risk Radar</h1>
          <p className="tagline">
            Flags PR risk from shifts in <em>what</em> coverage is about, rather than whether
            its tone is positive or negative.
          </p>
        </div>

        {brands.length > 0 && (
          <div className="header-controls">
            <div className="brand-picker">
              <label htmlFor="brand">Tracked brand</label>
              <select
                id="brand"
                value={preview ? "" : brand ?? ""}
                onChange={(e) => {
                  setPreview(null);
                  setBrand(e.target.value);
                }}
              >
                {preview && <option value="">—</option>}
                {brands.map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </select>
            </div>
            <BrandSearch onSearch={handleSearch} busy={searching} />
          </div>
        )}
      </header>

      {error && <p className="error-banner">{error}</p>}

      {preview && (
        <PreviewPanel
          preview={preview}
          onTrackedClick={() => {
            setPreview(null);
            setBrand(preview.brand);
          }}
        />
      )}

      {!preview && loading && !dailyStats.length && !error && (
        <div className="card skeleton">Loading…</div>
      )}

      {!preview && latest && (
        <>
          <StatTiles latest={latest} peak={peak} />

          <section className="card chart-card">
            <div className="card-head">
              <h2>Risk trajectory</h2>
              <span className="hint">{dailyStats.length} days</span>
            </div>
            <RiskTrajectoryChart data={dailyStats} />
          </section>
        </>
      )}

      {!preview && topics.length > 0 && (
        <section className="card section">
          <div className="card-head">
            <h2>Topics</h2>
            <span className="hint">select one to filter the articles below</span>
          </div>
          <TopicList
            topics={topics}
            onSelect={setSelectedTopicId}
            selectedTopicId={selectedTopicId}
          />
        </section>
      )}

      {!preview && mentions.length > 0 && (
        <section className="card section">
          <div className="card-head">
            <h2>
              Articles{" "}
              {selectedTopicId !== null && (
                <button className="clear-filter" onClick={() => setSelectedTopicId(null)}>
                  clear filter
                </button>
              )}
            </h2>
            <span className="hint">
              {filteredMentions.length} of {mentions.length}
            </span>
          </div>
          <MentionsTable mentions={filteredMentions} />
        </section>
      )}
    </div>
  );
}
