## 0. Baseline and authorization

- [ ] 0.1 Confirm F6C and F6D final gates and independent reviews before any F6E business-code apply.
- [ ] 0.2 Review the six F6E delta specs against current canonical requirements and obtain explicit apply confirmation under the project OpenSpec rule.
- [ ] 0.3 Re-read the current Unit/Master/Candidate/Review/Delivery/Registry code and record actual Alembic head, tests, bundle budgets and Git status.
- [ ] 0.4 Audit every active `complete-prd-v1-channel-deliverables` requirement/scenario and PRD §15/§16 acceptance boundary before implementation.
- [ ] 0.5 Stop and revise the specification if implementation requires destructive migration, an unplanned durable business object or weaker safety gates; do not backfill historical variants.

## 1. Additive persistence and migration

- [ ] 1.1 Add append-only ChannelVariantRevision model with exact project/unit/source Master/Identity/profile/adapter/payload/context fields.
- [ ] 1.2 Add stable variant_key and per-series revision, parent, expected-head, idempotency key and request fingerprint constraints.
- [ ] 1.3 Add exact ChannelVariantAssetRef role/order/placement/hash/rights snapshot model.
- [ ] 1.4 Add exact ChannelVariantEvidenceRef FactPackItem/checksum/locator model.
- [ ] 1.5 Add append-only ChannelVariantCheckRun model with input/profile/adapter/rule hash.
- [ ] 1.6 Add nullable `ContentAsset.channel_variant_revision_id` for v5 only.
- [ ] 1.7 Add FK, unique, index and bounded field constraints with atomic relationship deletion policy.
- [ ] 1.8 Add migration after the verified current head without rewriting v3/v4 rows.
- [ ] 1.9 Make isolated downgrade refuse v5-linked history before destructive DDL; prove compatible up/down/up on SQLite.
- [ ] 1.10 Validate PostgreSQL-compatible migration/constraint behavior on an isolated database.

## 2. Channel Adapter and Registry boundary

- [ ] 2.1 Define versioned ChannelAdapter protocol with capabilities, validate, adapt, preview, render, required_checks and package_projection.
- [ ] 2.2 Resolve only exact registered channel/content_form and published profile version/config hash.
- [ ] 2.3 Persist adapter key/version and relevant rule/config hashes in variant provenance.
- [ ] 2.4 Expose configured/executable/verified capability state without treating mere plugin presence as execution proof.
- [ ] 2.5 Reject unsupported channel/form or unavailable model/render capability with typed no-write results.
- [ ] 2.6 Keep Channel Registry/Profile as existing truth; do not create a duplicate mutable settings registry.
- [ ] 2.7 Regress the existing published `x/thread` target, legacy `x_thread/thread` fallback exclusion from v5, and registered-but-adapter-unavailable `x/single`; do not confuse registration with executable adaptation.

## 3. Project-scoped Variant service and exact refs

- [ ] 3.1 Add authorized list/current/detail/history APIs; raw-ID reads must use the same Project/Unit boundary.
- [ ] 3.2 Add non-durable adapt-preview against exact current source Master and target profile.
- [ ] 3.3 Add append-only save with variant_key/head CAS, unit-scoped idempotency and atomic event/ref writes.
- [ ] 3.4 Reject a variant_key changing its channel/form or pointing to another Unit's Master.
- [ ] 3.5 Freeze exact source Master ID/payload/context and pinned IdentitySnapshot; preserve original source channel/form.
- [ ] 3.6 Freeze exact published target profile, adapter and rule version/config hashes.
- [ ] 3.7 Persist inherited and edited final MaterialRevision refs with distinct placements and no byte copy.
- [ ] 3.8 Persist eligible FactPackItem/checksum/locator refs without expanding the frozen Fact Boundary.
- [ ] 3.9 Validate Project visibility, media kind, live bytes/hash/rights and evidence scope before commit.
- [ ] 3.10 Derive stale state from source Master/head/context, profile/adapter/rule/check and ref drift without mutating historical rows.
- [ ] 3.11 Regress simultaneous saves, stale profile/source context, idempotent replay and foreign raw-ID denial.

## 4. Adaptation and neutral source path

- [ ] 4.1 Verify existing explicit channel-neutral Unit creation and enable source-only neutral Master behavior without changing channel-bound Unit history.
- [ ] 4.2 Save neutral Master with null channel/form as source-only; direct v4 freeze must remain unavailable.
- [ ] 4.3 Keep existing channel-bound Master/v4 paths and hashes unchanged, including optional explicit adaptation from a bound Master.
- [ ] 4.4 Implement deterministic concrete adaptation preview through registered rules/code.
- [ ] 4.5 Implement model-assisted adaptation as suggestion with verified runtime receipt, never implicit Master/Variant save.
- [ ] 4.6 Require explicit accept and validated variant save; never repin Identity or mutate source Master.
- [ ] 4.7 Mark newly introduced unsupported factual claims incomplete until exact eligible evidence is bound.
- [ ] 4.8 Add stable-ID/content/ref/profile structured variant diff and source-change stale regression.

## 5. Content Matrix planner

- [ ] 5.1 Add bounded, authorized, read-only matrix suggestion API.
- [ ] 5.2 Use current Opportunity/Brief, selected Identity, Registry and existing Units as inputs without copying their truth.
- [ ] 5.3 Use historical Performance only with explicit coverage/unknown semantics, not zero-filled ranking.
- [ ] 5.4 Return reason/estimated-cost/value/confidence/unknown signals without persisting a duplicate strategy state.
- [ ] 5.5 Guarantee suggestions do not mutate Project, Unit, Identity, Memory or DeliveryTarget.
- [ ] 5.6 Confirm only selected suggestions through existing Unit APIs with normal history fork/archive rules; do not create DeliveryTarget before approved Candidate.
- [ ] 5.7 Bound result count and reject Cartesian expansion; regress repeated/no-selection requests.

## 6. Controlled registered-form adapters

- [ ] 6.1 Implement WeChat article adaptation against the exact published registered form/profile.
- [ ] 6.2 Implement adaptation for the published `x/thread` profile; leave already-registered `x/single` unavailable until its adapter is implemented and verified, and keep legacy `x_thread/thread` history unchanged.
- [ ] 6.3 Require Xiaohongshu image_note ordered actual image revisions, bytes/hash and public-use rights; reject prompt-only readiness.
- [ ] 6.4 Produce Douyin spoken_script with script/scenes/B-roll/voice text and no false final-video claim.
- [ ] 6.5 Generate SRT only as explicitly estimated timing absent real timed media.
- [ ] 6.6 Build byte-exact local package projections for each supported form with citations/declarations and no remote call.
- [ ] 6.7 Regress account-separated local targets, rights revocation and unknown/reconciliation preservation.

## 7. Variant checks and render readiness

- [ ] 7.1 Add append-only schema/content check bound to exact Variant payload/context.
- [ ] 7.2 Add exact channel/profile/rule check and preserve provider-coverage honesty.
- [ ] 7.3 Add final refs/evidence/rights and package/render readiness checks.
- [ ] 7.4 Derive latest applicable check per kind; later blocker for the same input must outrank old pass.
- [ ] 7.5 Make source/profile/adapter/rule/ref drift stale relevant checks and render binding.
- [ ] 7.6 Preserve exact warning disposition and live safety semantics from v4.

## 8. Candidate manifest v5

- [ ] 8.1 Implement pure canonical v5 manifest builder from one exact current Variant and source Master.
- [ ] 8.2 Freeze Project/Unit/Identity, source Master ID/hash/context and source channel/form provenance.
- [ ] 8.3 Freeze Variant ID/key/revision/payload/context, target profile/adapter/rules and model receipt.
- [ ] 8.4 Freeze ordered final refs, rights snapshots, evidence locators, latest checks, render, citations/declarations.
- [ ] 8.5 Regress canonical hash determinism and tamper detection.
- [ ] 8.6 Add v5 Freeze CAS/idempotency/currentness/live rights/evidence/bytes/render gates.
- [ ] 8.7 Populate Candidate variant FK only for v5; keep v3/v4 source dispatch and history unchanged.
- [ ] 8.8 Prove an invalid v5 freeze never falls back to v4/v3 or creates Approval/DeliveryTarget.

## 9. Review Approval Delivery and Project read models

- [ ] 9.1 Add v5 Preview/Changes/Checks from frozen adapted content without Publisher-side rewriting.
- [ ] 9.2 Bind Content Approval to exact v5 Candidate ID/hash and recheck live rights/evidence/integrity.
- [ ] 9.3 Dispatch new Delivery Authorization by Candidate schema: v5 must match its frozen Variant target channel/form/profile rather than the source Unit channel, preserve pinned identity/account authorization, label local packages manual, and require exact account/channel/form/action verification for remote effects; do not infer a binding from free-form account profile text. V3/v4 retain their Unit-channel rule.
- [ ] 9.4 Make v5 local package use frozen approved content and byte-verified final media, with no Draft/v4 fallback.
- [ ] 9.5 Preserve existing authorized history, DeliveryAttempt/Receipt semantics and unknown reconciliation priority.
- [ ] 9.6 Include Variant revisions/provenance in Project Versions and derive Overview without a second status table.
- [ ] 9.7 Regress foreign/archived project raw-ID reads and mutations across Variant, Candidate and package APIs.

## 10. Frontend and route isolation

- [ ] 10.1 Add bounded Matrix suggestion UI and explicit selected-only confirmation.
- [ ] 10.2 Add Production Channel Variants panel with target/profile/adapter capability state.
- [ ] 10.3 Show per-Variant current/stale/check/render/ref provenance and history/diff.
- [ ] 10.4 Add adapt preview, explicit accept/save and 409 conflict handling without modifying Master editor state.
- [ ] 10.5 Add v5 Review preview/changes/checks, separate approval/authorization and truthful local-package status.
- [ ] 10.6 Preserve Text/Graphic/Video editing and Workflow dirty/save independence.
- [ ] 10.7 Keep Matrix/Variant modules lazy and enforce `/projects` and unrelated route initial-JS/import-graph budgets.

## 11. Regression browser acceptance and closeout

- [ ] 11.1 Regress neutral and bound Master paths, v3/v4 Candidate history and no invented Variant backfill.
- [ ] 11.2 Regress exact refs/evidence, profile/source/adapter stale, concurrent save and hash-tampered v5 gates.
- [ ] 11.3 Browser: confirm selected Matrix Units and prove suggestion-only state makes no writes.
- [ ] 11.4 Browser: one Text Master to multiple channel Variants, current checks and v5 Candidate/Approval/local package.
- [ ] 11.5 Browser: Graphic Master to ordered-byte Xiaohongshu image_note and prompt-only blocked state.
- [ ] 11.6 Browser: Video/script to Douyin controlled script-only package with estimated SRT and no publication claim.
- [ ] 11.7 Browser: profile/source drift, archived read-only, rights revocation and unknown/reconciliation safety.
- [ ] 11.8 Audit every `complete-prd-v1-channel-deliverables` scenario and PRD §15/§16 acceptance evidence; do not auto-close V1.
- [ ] 11.9 Run full backend, frontend TypeScript/Vite, FE-P1 budgets, OpenSpec all-strict, relevant lint and diff-check.
- [ ] 11.10 Verify isolated SQLite/PostgreSQL migration and non-destructive downgrade preflight.
- [ ] 11.11 Obtain independent SPEC, backend/security, frontend/Review/package review; resolve findings without weakening gates.
- [ ] 11.12 Update README, task_plan/progress/findings and acceptance record with exact outcomes/limitations; commit owned files locally only.
- [ ] 11.13 Keep F6E canonical sync/archive, push, deploy and production migration pending separate authorization.
