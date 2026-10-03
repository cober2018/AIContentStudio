# FE-F6B Remaining 31 Tasks

## 5. Citation/evidence bridge
- [ ] 5.6 Add citation bind/unbind, emoji/list-item/repeated-use, edit/AI invalidation, range and boundary-drift tests.

## 6. Generic Master save bridge
- [ ] 6.1 Make new Text Studio drafts emit the v2 document envelope and save through the existing append-only Master API.
- [ ] 6.3 Atomically validate v2 payload plus exact asset/evidence refs and verified AI edit provenance.

## 21. Legacy and cross-modality regression
- [ ] 21.1 Preserve legacy `/workspace` TipTap Markdown save, selection rewrite, Draft fact-check and Draft document composition semantics.
- [ ] 21.2 Preserve historical `text.master.v1` read/freeze/Candidate hash behavior.
- [ ] 21.3 Preserve F6A Graphic/Video save/render/freeze/review/package behavior.
- [ ] 21.4 Preserve F2–F6A backend and browser-critical behavior.
- [ ] 21.5 Shared helper extraction must include explicit legacy regressions before acceptance.

## 22. Browser acceptance
- [ ] 22.1 Create/edit/reorder supported structured blocks and verify exact saved/reloaded v2 document.
- [ ] 22.2 Insert/remove exact project image and chart refs without copying/deleting shared assets.
- [ ] 22.3 Bind/unbind exact FactPack evidence to selected text and verify boundary-stale handling.
- [ ] 22.4 Run Text checks and verify current/stale/coverage UI.
- [ ] 22.5 Exercise AI rewrite Reject and Accept; prove Accept is local until explicit save and provenance is verified after save.
- [ ] 22.6 Exercise expand/shorten/tone/restructure and stale-patch rejection.
- [ ] 22.7 Verify pinned Identity panel cannot mutate identity.
- [ ] 22.8 Preview and explicitly commit v1→v2 fork; verify v1 history unchanged.
- [ ] 22.9 Seed a real verified Draft output into v2 and inspect provenance/warnings.
- [ ] 22.10 Verify structured Master diff add/remove/move/modify/ref/provenance output.
- [ ] 22.11 Freeze v2 Candidate, Review Preview/Changes/Checks, approve and download deterministic local package.
- [ ] 22.12 Verify Workflow dirty/save independence, archived read-only state and Graphic/Video shells.
- [ ] 22.13 Verify legacy `/workspace`, direct refresh, lazy chunk recovery and empty browser console.

## 23. Final gates and handoff
- [ ] 23.1 Run full backend suite plus all targeted F6B tests on isolated data.
- [ ] 23.2 Confirm zero new migration or stop/amend spec if this condition changed.
- [ ] 23.3 Run frontend TypeScript/Vite build and FE-P1 deterministic budget/import-graph checks.
- [ ] 23.4 Run OpenSpec all strict, relevant Ruff and git diff --check.
- [ ] 23.5 Complete isolated browser acceptance and retain bounded evidence record.
- [ ] 23.6 Independent SPEC review APPROVE.
- [ ] 23.7 Independent backend/Text-schema/check/AI-provenance review APPROVE.
- [ ] 23.8 Independent frontend/editor/accessibility/performance review APPROVE.
- [ ] 23.9 Record final changed files, test counts, bundle measurements, known limitations and local commit.
- [ ] 23.10 Do not canonical-sync/archive without separate authorization; do not start F6C until F6B implementation is closed.
