import { useEffect, useState } from "react";

// Recharts takes colors as SVG attributes, which don't resolve CSS custom
// properties reliably -- so the palette lives here too and is selected in JS.
// Values mirror the tokens in index.css; change both together.
const LIGHT = {
  surface: "#fcfcfb",
  grid: "#e6e5e1",
  axis: "#52514e",
  series: "#2a78d6",
  good: "#0ca30c",
  serious: "#ec835a",
  critical: "#d03b3b",
};

const DARK = {
  surface: "#1a1a19",
  grid: "#32312e",
  axis: "#c3c2b7",
  series: "#3987e5",
  good: "#0ca30c",
  serious: "#ec835a",
  critical: "#d03b3b",
};

export function useThemeColors() {
  const query = "(prefers-color-scheme: dark)";
  const [isDark, setIsDark] = useState(
    () => typeof window !== "undefined" && window.matchMedia(query).matches
  );

  useEffect(() => {
    const mql = window.matchMedia(query);
    const onChange = (e) => setIsDark(e.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return isDark ? DARK : LIGHT;
}

export const BAND_ROLE = {
  Watch: "good",
  Elevated: "serious",
  Critical: "critical",
};
