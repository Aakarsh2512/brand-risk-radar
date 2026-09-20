import { useState } from "react";

export default function BrandSearch({ onSearch, busy }) {
  const [value, setValue] = useState("");

  const submit = (e) => {
    e.preventDefault();
    const name = value.trim();
    if (name) onSearch(name);
  };

  return (
    <form className="brand-search" onSubmit={submit} role="search">
      <label htmlFor="brand-search">Look up any brand</label>
      <div className="brand-search-row">
        <input
          id="brand-search"
          type="search"
          placeholder="e.g. Airbnb"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          autoComplete="off"
          maxLength={40}
        />
        <button type="submit" disabled={busy || !value.trim()}>
          {busy ? "Checking…" : "Search"}
        </button>
      </div>
    </form>
  );
}
