## 0. Apply baseline and guardrails

- [ ] 0.1 Re-verify AIContentStudio workspace, approved apply baseline, clean/conflict state, F6A archive/canonical specs and preserved user artifacts.
- [ ] 0.2 Record fresh backend, frontend build/budget, OpenSpec strict, Ruff and diff-check baseline before F6B code changes.
- [ ] 0.3 Require explicit F6B apply authorization; do not infer it from specification approval.
- [ ] 0.4 Keep target at zero new DB tables/migrations; stop and amend this change if durable persistence expansion becomes necessary.
- [ ] 0.5 Do not push, deploy, run production migration, start F6C/F6D, or add connector/publisher capability.

## 1. Schema-aware Text adapters

- [ ] 1.1 Refactor Production adapter lookup to resolve exact `(modality, payload_schema)` and expose supported/default schemas.
- [ ] 1.2 Preserve historical `text.master.v1` validation/render/freeze/package behavior.
- [ ] 1.3 Add `TextMasterV2Adapter` and make `text.master.v2` the default for new Text user edits after F6B.
- [ ] 1.4 Keep Graphic/Video adapter defaults unchanged and reject unknown schema versions fail-closed.
- [ ] 1.5 Make readiness, checks, Candidate validation and package projection use the persisted schema adapter.
- [ ] 1.6 Add cross-schema adapter regression tests for v1/v2/graphic/video.

## 2. Studio Text Document contract

- [ ] 2.1 Add `services/text_documents.py` with `studio.text.document.v1` validation, canonicalization and bounded hashing.
- [ ] 2.2 Implement stable unique block/list-item IDs and strict bounds for document size, counts, strings and URLs.
- [ ] 2.3 Implement heading, paragraph, quote, bullet/ordered list, callout, code, image, chart and divider blocks.
- [ ] 2.4 Implement bounded inline runs and bold/italic/code/http(s)-link marks independent of TipTap JSON.
- [ ] 2.5 Reject unknown block/mark/editor nodes and infrastructure path/storage fields.
- [ ] 2.6 Add canonical per-block/whole-document plain-text projections and block-offset lookup for locators.
- [ ] 2.7 Reject client-supplied editable v2 Markdown to enforce one authoritative document truth.
- [ ] 2.8 Add exhaustive document validation/canonicalization tests.

## 3. Deterministic v2 rendering

- [ ] 3.1 Implement deterministic Studio Document → Markdown rendering for every supported block/mark.
- [ ] 3.2 Ensure image/chart Markdown uses content metadata/exact refs and never local infrastructure paths.
- [ ] 3.3 Make repeated render/hash deterministic across JSON key ordering and editor implementation.
- [ ] 3.4 Update v2 preview/render/package projection to use the server renderer.
- [ ] 3.5 Add renderer and content-hash regression tests.

## 4. Exact assets and embedded references

- [ ] 4.1 Require every image/chart block MaterialRevision ID to exist in declared exact asset refs.
- [ ] 4.2 Validate expected image/chart material kind, project visibility, exact hash and rights via Production Core.
- [ ] 4.3 Reject conflicting duplicate declarations, foreign/raw material IDs and unchecked embedded references.
- [ ] 4.4 Keep bytes outside document payload and preserve append-only ref history.
- [ ] 4.5 Report declared-but-unused Text assets truthfully without silently using them.
- [ ] 4.6 Add asset insert/remove/rights regression tests.

## 5. Citations and exact evidence

- [ ] 5.1 Define citation IDs and exact `(block_id,start,end,fact_pack_item_id)` contract.
- [ ] 5.2 Validate text-bearing target block, canonical offsets and declared exact evidence ref.
- [ ] 5.3 Require ContentMasterEvidenceRef locator/snapshot checksum to match the citation use.
- [ ] 5.4 Reject foreign/out-of-boundary/dangling evidence and preserve Production context-CAS behavior.
- [ ] 5.5 Reuse current Project Fact Boundary + FactPack read APIs unless a concrete bounded read gap is proven.
- [ ] 5.6 Add citation bind/unbind/range/boundary-drift tests.

## 6. Generic Master save integration

- [ ] 6.1 Make new Text Studio drafts emit the v2 document envelope and save through the existing append-only Master API.
- [ ] 6.2 Preserve expected_revision, expected_context_hash, idempotency, archive and transaction rules.
- [ ] 6.3 Atomically validate v2 payload plus exact asset/evidence refs and verified AI edit provenance.
- [ ] 6.4 Allow incomplete drafting revisions but block Candidate readiness for empty/invalid required content.
- [ ] 6.5 Ensure failed saves persist no partial Master/ref/event rows.
- [ ] 6.6 Add v2 idempotency/concurrency/context-drift tests.

## 7. Explicit v1 → v2 fork

- [ ] 7.1 Add deterministic v1-to-v2 converter using provable legacy document data first and bounded Markdown conversion second.
- [ ] 7.2 Map only exact authorized legacy asset/evidence refs and return explicit warnings for unsupported/unmapped constructs.
- [ ] 7.3 Add read-only upgrade-preview API and append-only upgrade API with expected revision/hash/idempotency.
- [ ] 7.4 Require current mutable v1 Master for commit; never rewrite v1 or historical Candidates in place.
- [ ] 7.5 Record source schema/conversion warnings in bounded edit provenance.
- [ ] 7.6 Add preview/commit/idempotency/conflict/history tests.

## 8. Draft ProjectWorkflowOutput → v2 seed

- [ ] 8.1 Keep the existing verified `from-output` route but make new Text seeds produce `text.master.v2`.
- [ ] 8.2 Preserve exact Draft/Workflow/Run/Step/latest-successful-Attempt lineage validation.
- [ ] 8.3 Deterministically convert Draft body/document and map only provable asset/evidence refs.
- [ ] 8.4 Preserve unmapped media/claims as explicit conversion warnings/incomplete coverage.
- [ ] 8.5 Make idempotent replay return committed v2 without rereading later Draft changes.
- [ ] 8.6 Keep all historical v1 seed revisions readable/unchanged and add regressions.

## 9. Schema-aware Master checks

- [ ] 9.1 Evolve required-check resolution to be exact-schema/profile aware rather than a modality-wide fixed tuple.
- [ ] 9.2 Preserve v1 common-check behavior and register v2 common + `text_structure`, `text_fact`, `text_identity`, `text_platform`.
- [ ] 9.3 Require `text_discoverability` only when an exact published channel/content-form profile resolves.
- [ ] 9.4 Include exact payload/context/assets/evidence/adapter/profile versions in check input/currentness.
- [ ] 9.5 Preserve latest-result authority, immutable history, stale behavior and exact warning dispositions.
- [ ] 9.6 Add cross-schema/currentness/profile-change regression tests.

## 10. Text-specific check services

- [ ] 10.1 Add/refactor `services/text_master_checks.py` for v2 checks without Draft persistence.
- [ ] 10.2 Implement deterministic `text_structure` coverage for schema, IDs, hierarchy, refs and required content.
- [ ] 10.3 Implement `text_fact` from deterministic v2 text + exact Fact Boundary snapshots; reuse factchecker logic without DraftClaim/DraftCheckRun writes.
- [ ] 10.4 Map fact issues to block/range locators where deterministic mapping permits and respect evidence model-use rights.
- [ ] 10.5 Implement `text_identity` against the exact pinned IdentitySnapshot; report deterministic/semantic coverage and never mutate identity.
- [ ] 10.6 Treat unavailable semantic identity review truthfully (warning/incomplete coverage, never fake verified pass).
- [ ] 10.7 Implement `text_platform` from exact Channel Registry/rule descriptors and fail incomplete when required execution is unavailable.
- [ ] 10.8 Refactor exact discoverability profile resolution for `text_discoverability` without creating Draft-bound DiscoverabilityReport.
- [ ] 10.9 Add fact/identity/platform/discoverability prompt-injection, provider-failure and pinned-context regressions.

## 11. AI Text suggestions

- [ ] 11.1 Add `services/text_master_ai.py` and a project-scoped Text suggestion route.
- [ ] 11.2 Support rewrite, expand, shorten, tone and bounded restructure operations.
- [ ] 11.3 Authorize current base Master, validate base payload hash and bounded unsaved working v2 document, then derive selection/context server-side.
- [ ] 11.4 Load pinned Identity/Brief and only model-use-allowed Evidence; treat all source/evidence text as untrusted data rather than instructions.
- [ ] 11.5 Invoke the existing configured rewrite model route and persist LLMRun with purpose/input/output/usage/status.
- [ ] 11.6 Return only validated `replace_text` or `replace_blocks` patches; suggestion call must create no Master/check/Candidate.
- [ ] 11.7 Reject archived/historical/foreign bases, invalid selections and oversized working documents.
- [ ] 11.8 Add authorization, bounds, stale-base, injection and operation-specific tests.

## 12. AI provenance verification

- [ ] 12.1 Define bounded `edit_summary.ai_edits[]` metadata and store project/unit/base/working-document/operation/selection/patch provenance in LLMRun parsed output.
- [ ] 12.2 On Master save, verify referenced LLMRun exists, succeeded, has supported purpose and matches exact project/unit/base hashes.
- [ ] 12.3 Verify returned patch hash/output matches accepted edit metadata.
- [ ] 12.4 Reject or exclude fake/unrelated/failed run IDs; never freeze unverified AI provenance.
- [ ] 12.5 Preserve AI use as optional: content with no AI edits remains fully valid.
- [ ] 12.6 Add provenance tamper and replay regression tests.

## 13. Structured Text Master diff

- [ ] 13.1 Add `services/text_master_diff.py` and bounded project-scoped diff API.
- [ ] 13.2 For v2, report stable-ID block add/remove/move/modify and title changes.
- [ ] 13.3 Report asset, citation/evidence and verified AI-edit provenance changes; report context changes separately.
- [ ] 13.4 Support bounded v1↔v2 comparable projection without persisting an upgrade.
- [ ] 13.5 Keep diff read-only with no diff table.
- [ ] 13.6 Add authorization/history/move-vs-delete-add regression tests.

## 14. Candidate v4 / Review / local package compatibility

- [ ] 14.1 Freeze v2 structured payload unchanged in manifest v4 and freeze deterministic Markdown/hash in render.
- [ ] 14.2 Update Text Candidate Preview to use frozen render rather than requiring `content.markdown`.
- [ ] 14.3 Add structured Candidate change metadata when both sides are v2; keep rendered Markdown similarity secondary.
- [ ] 14.4 Keep v1↔v2 Candidate history comparison truthful and bounded.
- [ ] 14.5 Ensure Approval remains exact-hash/immutable and live evidence/rights gates remain unchanged.
- [ ] 14.6 Ensure local v2 package writes deterministic `content.md` from frozen render with no Draft fallback.
- [ ] 14.7 Preserve v1/v2/v3/v4 and Graphic/Video Review/Delivery regressions.

## 15. Professional Text Studio editor

- [ ] 15.1 Replace the normal TextStudio JSON textarea with a professional structured editor while keeping Graphic/Video shells unchanged.
- [ ] 15.2 Add Studio Document ↔ TipTap adapter; ProseMirror/TipTap JSON never becomes durable payload.
- [ ] 15.3 Preserve stable block IDs through editing/reorder and surface unsupported editor content before save.
- [ ] 15.4 Provide accessible toolbar/editing for heading, paragraph, quote, lists, callout, code, divider and inline formatting.
- [ ] 15.5 Keep historical v1/v2 revisions read-only and current v2 edits local/dirty until explicit save.
- [ ] 15.6 Preserve context rebase, archive read-only, reload/switch dirty confirmation and Candidate freeze entry.
- [ ] 15.7 Keep Workflow dirty/save fully independent from Text Master dirty/save.

## 16. Text Studio asset/evidence UX

- [ ] 16.1 Add bounded Project Shared Assets picker and rights/status display.
- [ ] 16.2 Image/chart insertion atomically updates local document block + exact asset-ref draft state; removal never deletes Material.
- [ ] 16.3 Add Evidence panel from current exact Project Fact Boundary/FactPack items.
- [ ] 16.4 Bind selected text to citation + exact evidence-ref draft state atomically and support local unbind.
- [ ] 16.5 Show evidence kind/snapshot/rights coverage and explicit boundary-stale behavior.
- [ ] 16.6 Keep server authoritative for all refs and context at save/freeze.

## 17. Text Studio AI / Identity / Checks UX

- [ ] 17.1 Add selection/block AI actions for five supported operations.
- [ ] 17.2 Show before/after suggestion diff with explicit Accept/Reject.
- [ ] 17.3 Accept changes local state only; reject does nothing; stale target prevents patch apply.
- [ ] 17.4 Add read-only pinned Identity panel with no mutation shortcut.
- [ ] 17.5 Add Text checks panel showing common/text-specific status, exact currentness, coverage/profile/provider and warnings.
- [ ] 17.6 Run checks without changing content and preserve old-check history.
- [ ] 17.7 Integrate existing exact warning-disposition flow where required.

## 18. Revision / upgrade / diff UX

- [ ] 18.1 Show immutable Master history with current/historical, schema, source, actor/time, AI-edit count and readiness summary.
- [ ] 18.2 Offer explicit upgrade preview/commit only for eligible current v1 Master and display conversion warnings.
- [ ] 18.3 Add structured revision diff UI for block/content/ref/provenance/context changes.
- [ ] 18.4 Keep historical rows read-only and require explicit new revision for continued editing.
- [ ] 18.5 Preserve dirty-confirmation behavior on reload/revision switch/navigation where practical.
- [ ] 18.6 Keep Draft seed action but show that new seed result is v2 with exact provenance.

## 19. ContentMasterPanel / ModalityWorkspace integration

- [ ] 19.1 Refactor Text-facing ContentMasterPanel state so payload/assets/evidence can be edited structurally without raw JSON normal UX.
- [ ] 19.2 Keep generic Production Core save/check/freeze orchestration where it remains modality-neutral.
- [ ] 19.3 Keep v2 Text local dirty state, current context accept/rebase and exact save inputs coherent.
- [ ] 19.4 Preserve Graphic/Video render-attestation and F6A shell behavior unchanged.
- [ ] 19.5 Preserve Review deep link and current Candidate flow.
- [ ] 19.6 Hide any development raw JSON tooling behind safe read-only/debug affordances only if retained.

## 20. FE-P1 performance isolation

- [ ] 20.1 Keep existing `/projects` hard initial-JS budget green.
- [ ] 20.2 Prove common Production, Graphic and Video static import closures do not include TipTap/editor-only dependencies.
- [ ] 20.3 Load TipTap only through Text Studio or legacy Workspace dynamic boundaries.
- [ ] 20.4 Record measured common Production and Text Studio raw/gzip baselines; do not invent a permanent Text cap before review.
- [ ] 20.5 Preserve `/assets`, `/settings`, `/learning` measured budgets and chunk failure recovery.
- [ ] 20.6 Add manifest/import-graph regression verification.

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
- [ ] 23.9 Record final changed files, test counts, bundle measurements, known limitations and commit.
- [ ] 23.10 Do not canonical-sync/archive without separate authorization; do not start F6C until F6B is closed and a Graphic Studio proposal is approved.
