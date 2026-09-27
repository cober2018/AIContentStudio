## Context

The current frontend is React 18, React Router 6, Tailwind, TanStack Query, and a small reusable UI component set. Existing routes and API pages have uncommitted user work. The FE-F0-F1 handoff and approved Frontend Product Contract specify a local-only prototype with ContentProject as its root.

## Goals / Non-Goals

**Goals:** Build the nine-workspace shell; project list and seven-tab detail; editable Content Units; asset drawer and production route; distinct status presentation; healthy and abnormal mock fixtures.

**Non-Goals:** Backend changes, real persistence, full workflow debugger, real publishing, guessed ORM mapping.

## Decisions

1. Use `App.tsx` for primary routes and navigation, preserving existing legacy URLs in a secondary section. This keeps current work accessible while making the new product model the primary experience.
2. Keep mock view models and repository in a dedicated frontend module backed by `localStorage`. Seed fixtures once, so Content Unit edits survive a refresh without implying server persistence. No backend contract is assumed.
3. Use query parameter `tab` for project tabs and URL path for the selected unit. Local draft form state is separate from saved mock state.
4. Reuse `Modal`/`Drawer`/`EmptyState` from `components/ui.tsx`, extend shared status badges, and add a concise production shell. Workflow editing remains FE-F2.
5. Keep the V5 prototype as a visual and interaction reference, while the Frontend Contract governs status and object semantics.

## Risks / Trade-offs

- [Local mock edits look permanent] → Label them as local demo data and expose reset behavior only as an explicit user action.
- [Legacy routes disappear] → Preserve URLs and a secondary legacy navigation section.
- [Status meanings collapse] → Assign distinct labels, colors, and explanatory copy for blocked, stale, unknown, ready, and waiting human.

## Migration Plan

Frontend-only code; no database migration. Existing routes remain reachable. Rollback can remove the new routes and mock repository without touching backend data.
