## Why

The user finds the web app ugly and hard to use: pages are unordered lists, settings render as raw `key: value` text (persona overview dumps whole creative profiles), and nothing has hierarchy or rhythm. The target is award-level craft (Awwwards / Webby / FWA), checked by repeated self-review of screenshots.

The user also confirmed a full workflow map (2026-10-21): persona & accounts → topics & calendar → planning → material → production → cover & title → platform versions → review & publishing → growth analysis → brand deals. Cover, material library, growth analysis and brand deals are new modules and get their own changes; this change sets the shared structure and visual system they will use.

## What Changes

- **Visual direction: editorial creative studio** (chosen by the user from three options): warm paper background, ink text, one vermilion accent, serif display headings (Songti SC / Noto Serif SC, Kudryashev Display for Latin numerals), generous spacing, quiet motion.
- **Design tokens** as CSS variables mapped into Tailwind (paper, surface, ink, muted, line, accent, status colours, radius, shadow, type scale), so every existing page inherits the new system; arbitrary hex colours are replaced with tokens.
- **App shell and navigation** reorganised around the workflow: 今日 · 内容 (机会 / 项目 / 生产) · 审阅与发布 · 资产 (素材与知识) · 复盘 · 身份 (角色与账号) · 设置. New modules appear in navigation only when they exist (no placeholder features).
- **Shared components** rebuilt: page header, section, card, tabs, definition list, tag/badge, empty state, buttons, fields, modal, drawer.
- **Readable structured data**: profiles, creative configuration and method stacks render as labelled sections, chips and lists; raw JSON only in an explicit "raw data" disclosure.
- **Page-by-page redesign**, starting with 角色与账号 (directories, persona overview, account detail, every tab), then home, opportunities, projects, production, review, assets, learning, settings. Legacy routes outside navigation inherit tokens only.
- No API, data or behaviour changes; all guards (unsaved-change prompts, conflicts, read-only states) stay.

## Capabilities

### New Capabilities

- `studio-visual-system`: tokens, shell, navigation and readable-structure rules for every page.

## Impact

- `apps/web/src/index.css`, `tailwind.config.js`, `src/App.tsx`, `src/components/ui.tsx`, and page components under `src/product` and `src/pages`.
- Follow-up changes (separate proposals): cover & title step, material library, growth analysis, brand deals, content calendar.
