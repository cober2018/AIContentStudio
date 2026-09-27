## Context

FE-F4 commit `2f3ced2` is the baseline. A fresh `npm run build` emits one 1,095.28 kB JS asset (351.06 kB gzip) and a 48.52 kB CSS asset. `App.tsx` statically imports all primary and legacy pages. The legacy `Workspace` imports the TipTap editor, and `Workflows` imports XYFlow. `PersistentProjectPages.tsx` exports `/projects`, project detail, and production from one module, and statically imports `ProductionDesigner` plus all project tabs. There is no `React.lazy`/`Suspense`, Vite manual chunk policy, or frontend test script.

The baseline demonstrates a packaging problem, not a measured React render problem. A smaller file count or disappearance of Vite's 500 kB warning is not sufficient evidence of less initial network transfer.

## Goals / Non-Goals

**Goals:**
- Keep every current route and legacy alias reachable with unchanged data and business behavior.
- Make pages load only when visited; make `/projects`, `/projects/:projectId`, and the unit production route separate runtime import roots.
- Exclude TipTap and XYFlow from the initial dependency closure of `/projects` and unrelated routes.
- Enforce a reproducible initial JavaScript budget and report both raw and gzip bytes for comparable builds.
- Provide accessible loading and recoverable chunk-load failure states; verify direct-link and navigation behavior.

**Non-Goals:**
- API/database changes, content or review state-machine changes, layout redesign, or production deployment.
- Refactoring Settings sections or all project tabs into additional boundaries in the first cut.
- Manual vendor chunks before inspecting the resulting Vite graph; global query-cache tuning, pagination, or virtualization.
- Claiming a user-perceived speedup without browser/network measurement.

## Decisions

1. **Route boundaries first.** Replace page-level static imports in `App.tsx` with `React.lazy(() => import(...))` and render route content under `Suspense`. Keep the navigation shell mounted during transitions. Wrap lazy content in a small route error boundary that provides retry/reload when a chunk fails; changing routes resets the error state. Alternative: `manualChunks` alone. Rejected because it may split files without removing code from the initial import closure.
2. **Separate project runtime roots.** Move persistent list, detail, and production wrapper into focused modules; move shared TypeScript shapes into a type-only module. `ProductionDesigner` and `ProjectMatrixTab` import types only. `/projects` dynamically loads the list, project detail loads its current tabs, and the numeric production route dynamically loads the wrapper/designer. Preserve the existing nonnumeric demo fallback and route priority. Alternative: lazy-load `PersistentProjectPages.tsx` as one chunk. Rejected because its static imports would still load the designer on the list route.
3. **Measure the initial graph, not total output.** Generate Vite's manifest in the normal build, traverse `imports` (not `dynamicImports`) from the entry and `/projects` route chunk, deduplicate shared files, and read actual emitted JS byte sizes. A budget script reports raw and gzip sizes. The entry plus `/projects` static closure MUST be below 500,000 raw bytes and MUST exclude the TipTap/XYFlow route chunks; record the actual post-change values and compare them to the 1,095,280-byte baseline. Report total generated JS separately without making it an initial-load gate. A route-to-manifest mapping missing after a toolchain change fails the check instead of reporting a false pass. Do not relax the threshold merely to pass the gate; if it proves unattainable, revisit the design/spec with the user.
4. **Reuse existing verification.** Run TypeScript/Vite build and the budget check, then manually smoke direct load/refresh and navigation for `/`, `/projects`, numeric project detail, numeric production, `/review`, `/identities`, `/workspace`, and `/workflows`, including fallback and chunk failure. The package has no frontend test harness; this change does not add one merely to test splitting. If user later requests automated route regression tests, scope that separately.

## Risks / Trade-offs

- [Lazy chunk request fails or deploy serves stale HTML] → Show a recoverable route error and preserve shell navigation; verify direct refresh under the current SPA serving setup.
- [Chunking duplicates shared code or delays subsequent route transitions] → Compare manifest/static closures and actual browser requests, not only emitted file count; keep shared runtime in Vite-managed chunks unless evidence supports a manual strategy.
- [Splitting project types creates runtime cycles or route regressions] → Use `import type`, preserve parameter validation and demo fallbacks, and smoke each route.
- [The 500 kB threshold captures only initial transfer] → Report gzip and total JS separately; add user timing only after a stable measurement environment is available.

## Migration Plan

No data migration. Apply in the FE-P1 branch after explicit approval, keep all route paths stable, build and inspect the manifest, run the budget and route checks, then archive the OpenSpec after acceptance. Rollback is a frontend code revert; there is no server or schema rollback. No push/merge/deploy is part of this proposal.

## Open Questions

None required before starting the proposed first cut. If the resulting `/projects` closure cannot meet 500,000 raw bytes without broader refactoring, stop and recalibrate the budget with measured evidence rather than silently expanding scope.
