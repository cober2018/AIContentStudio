## 1. Preserve route behavior while establishing load boundaries

- [ ] 1.1 Record the FE-F4 build baseline, existing route map, and current direct-link behavior before implementation.
- [ ] 1.2 Move persistent project shared TypeScript shapes into a type-only module; separate `/projects` list, project detail, and unit production wrapper into distinct runtime modules without changing API calls or UI actions.
- [ ] 1.3 Change `App.tsx` page imports to route-level lazy imports, preserving numeric project/production dispatch, demo fallback, legacy aliases, redirects, and persistent navigation shell.
- [ ] 1.4 Add an accessible route loading view and recoverable chunk-load error/retry behavior that resets when the user navigates elsewhere.

## 2. Measure and constrain the resulting JavaScript graph

- [ ] 2.1 Emit a Vite manifest during the normal frontend build and implement an initial-route budget check for the entry plus `/projects` static dependency closure, using actual emitted raw and gzip bytes.
- [ ] 2.2 Make the budget check fail on missing route mapping or at least 500,000 raw initial bytes; report total generated JS separately and verify that TipTap/XYFlow are absent from `/projects` initial graph.
- [ ] 2.3 Inspect the resulting chunks and recorded baseline comparison before considering any manual vendor strategy; leave `manualChunks` unchanged unless measured evidence and a revised spec justify it.

## 3. Verify and document

- [ ] 3.1 Run frontend TypeScript/Vite build, bundle budget, OpenSpec strict validation, and `git diff --check`; record actual sizes and failures.
- [ ] 3.2 Smoke direct navigation, refresh, and transitions for `/`, `/projects`, numeric project detail, numeric production, `/review`, `/identities`, `/workspace`, `/workflows`, and nonnumeric demo fallback; exercise loading and chunk-failure recovery.
- [ ] 3.3 Update README, progress, and findings with the verified result, remaining performance debt, and no-business-change boundary; request independent review before archive.
