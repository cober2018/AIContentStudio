## Context

React 18 + Vite + Tailwind 3. About 100 components use raw Tailwind palette classes (slate ×1528, indigo ×198, amber ×262 …) and a dark sidebar. No component library.

## Decisions

- **Retheme through Tailwind palettes.** `slate`/`gray`/`zinc`/`neutral` map to a warm ink scale; `indigo`/`violet` map to the accent scale; status hues are softened. Every page changes consistently in one step, then structure is redesigned page by page.
- **Tokens as CSS variables** (`--paper`, `--ink`, `--accent` …) consumed by Tailwind `rgb(var(--x) / <alpha-value>)`, so opacity utilities keep working and a dark theme stays possible.
- **Type.** Chinese display: `"Songti SC", "Noto Serif SC", "STSong", serif`; body: `"PingFang SC", "Hiragino Sans GB", system-ui`; Latin display and numerals: Kudryashev Display (already bundled). No network font dependency.
- **Light sidebar.** The shell moves from a dark slab to a paper-coloured rail with a serif wordmark and grouped workflow navigation; the active item uses an ink marker, not a filled block.
- **Readable structure over dumps.** A shared `ProfileView` renders known fields with purpose-built layouts (positioning as a lead paragraph, audiences and domains as chips, boundaries as lists, creative stages as a pipeline); unknown keys fall back to a compact key list; raw JSON sits behind a disclosure.
- **Self-review loop.** Each redesigned page is screenshotted at 1440 and 390 widths, checked against a fixed checklist (hierarchy, alignment, spacing rhythm, contrast, density, empty/loading/error states, mobile), fixed, and re-shot until no issue remains.

## Risks

- Palette remap can lower contrast in spots; the checklist includes contrast checks.
- Large surface; legacy pages get the theme but not structural redesign.
