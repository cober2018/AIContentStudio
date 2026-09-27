## Why

On FE-F4 commit `2f3ced2`, the production frontend builds one 1,095.28 kB JavaScript bundle (351.06 kB gzip). `App.tsx` eagerly imports every current and legacy page, while the persistent project module eagerly imports the production designer. Opening a lightweight route therefore requires downloading code for unrelated editors and workflow screens. Establish load boundaries before later product work adds more code.

## What Changes

- Load current and legacy page modules on demand while preserving all existing routes, aliases, redirects, and page behavior.
- Separate the persistent project list, project detail, and unit production route load graphs so `/projects` does not pull in the designer or inactive project tabs.
- Keep TipTap and XYFlow outside the initial load graph for `/projects` and other routes that do not use them.
- Record and enforce a reproducible bundle budget for the entry and representative initial routes; compare it with the FE-F4 baseline rather than treating the Vite warning alone as success.
- Verify direct navigation, refresh, route transitions, loading/failure states, and legacy-route reachability using the existing frontend build and targeted route smoke checks.

No business logic, API, database, identity, review, or delivery contract changes are intended. Do not bundle query-cache policy, pagination, virtual lists, settings-section refactors, or speculative `manualChunks` configuration into this change.

## Capabilities

### New Capabilities

- `fe-p1-frontend-bundle-performance`: Route-oriented loading, project/production dependency isolation, and measurable initial JavaScript budget with preserved navigation behavior.

### Modified Capabilities

None. Existing FE-F0/F1 through FE-F4 product requirements and routes remain unchanged.

## Impact

- Frontend only: `apps/web/src/App.tsx`, persistent project/production page modules and their type imports, optional build-budget script and `apps/web/package.json`, plus frontend documentation.
- No new runtime dependency, backend endpoint, migration, production data write, or deployment in this change.
- Baseline evidence: FE-F4 `2f3ced2`; `npm run build` produced one 1,095.28 kB JS file, gzip 351.06 kB; the web package has no dedicated test script.
