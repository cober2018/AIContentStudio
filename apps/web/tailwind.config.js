/** @type {import('tailwindcss').Config} */
const scale = (name, steps = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]) =>
  Object.fromEntries(steps.map((step) => [step, `rgb(var(--${name}-${step}) / <alpha-value>)`]));

// Existing pages use stock palette names; mapping them onto the studio tokens restyles every page at once.
const ink = scale("ink");
const accent = scale("accent");

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "rgb(var(--paper) / <alpha-value>)",
        white: "rgb(var(--surface) / <alpha-value>)",
        black: "rgb(var(--ink-950) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        ink, accent,
        slate: ink, gray: ink, zinc: ink, neutral: ink, stone: ink,
        indigo: accent, violet: accent, purple: accent,
        emerald: scale("moss"), green: scale("moss"),
        amber: scale("ochre"), yellow: scale("ochre"), orange: scale("ochre"),
        rose: scale("clay"), red: scale("clay"),
        sky: scale("tide"), blue: scale("tide"), teal: scale("tide"), cyan: scale("tide"),
      },
      fontFamily: {
        display: ['"Kudryashev Display"', '"Songti SC"', '"Noto Serif SC"', '"STSong"', "serif"],
        serif: ['"Songti SC"', '"Noto Serif SC"', '"STSong"', "serif"],
        sans: ["-apple-system", '"SF Pro Text"', '"PingFang SC"', '"Hiragino Sans GB"', '"Microsoft YaHei"', "sans-serif"],
        mono: ['"SF Mono"', "ui-monospace", "Menlo", "monospace"],
        kudryashev: ['"Kudryashev Display"', "serif"],
        grotesk: ["-apple-system", '"PingFang SC"', '"Microsoft YaHei"', "sans-serif"],
        helvetica: ['"Helvetica Neue"', "Helvetica", "Arial", "sans-serif"],
      },
      borderRadius: { card: "18px", pill: "999px" },
      boxShadow: {
        card: "0 1px 0 rgb(var(--ink-900) / 0.04), 0 12px 32px -18px rgb(var(--ink-900) / 0.18)",
        lift: "0 2px 0 rgb(var(--ink-900) / 0.04), 0 22px 48px -24px rgb(var(--ink-900) / 0.28)",
      },
      letterSpacing: { label: "0.08em" },
      transitionTimingFunction: { studio: "cubic-bezier(0.2, 0.7, 0.1, 1)" },
      keyframes: {
        rise: { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "none" } },
      },
      animation: { rise: "rise 420ms cubic-bezier(0.2, 0.7, 0.1, 1) both" },
    },
  },
  plugins: [],
};
