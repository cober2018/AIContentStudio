## 0. Reconciliation/baseline
- [ ] 0.1 Start after F6D gates pass.
- [ ] 0.2 Re-read North Star ChannelVariant/Channel Adapter invariants and current F4/F6A specs.
- [ ] 0.3 Audit active `complete-prd-v1-channel-deliverables` requirements for retention.
- [ ] 0.4 Record fresh backend/frontend/OpenSpec/migration baseline.
- [ ] 0.5 No historical backfill or destructive migration.

## 1. Additive persistence
- [ ] 1.1 Add ChannelVariantRevision model.
- [ ] 1.2 Add exact variant asset refs.
- [ ] 1.3 Add exact variant evidence refs.
- [ ] 1.4 Add append-only variant check runs.
- [ ] 1.5 Add nullable ContentAsset.channel_variant_revision_id.
- [ ] 1.6 Add uniqueness/index/FK/check constraints.
- [ ] 1.7 Add reversible migration after actual head.
- [ ] 1.8 Add downgrade preflight protecting v5 history.
- [ ] 1.9 Validate SQLite/PostgreSQL migration paths.

## 2. Channel Adapter registry
- [ ] 2.1 Add versioned ChannelAdapter protocol.
- [ ] 2.2 Implement capabilities().
- [ ] 2.3 Implement validate().
- [ ] 2.4 Implement adapt().
- [ ] 2.5 Implement preview().
- [ ] 2.6 Implement render().
- [ ] 2.7 Implement required_checks()/package_projection().
- [ ] 2.8 Resolve exact ChannelTemplate/Profile version.
- [ ] 2.9 Preserve adapter key/version in provenance.
- [ ] 2.10 Unsupported capability fails closed.

## 3. Variant service/currentness
- [ ] 3.1 Add list/current/detail APIs.
- [ ] 3.2 Add append-only save with expected revision/idempotency.
- [ ] 3.3 Authorize exact project/unit/source Master.
- [ ] 3.4 Pin exact source Master payload/context hashes.
- [ ] 3.5 Pin exact channel/profile/adapter config.
- [ ] 3.6 Persist exact final refs without byte copy.
- [ ] 3.7 Derive stale state from source Master/profile/adapter/ref drift.
- [ ] 3.8 Preserve historical variant rows.
- [ ] 3.9 Add concurrency/context-CAS tests.

## 4. Adaptation operations
- [ ] 4.1 Add explicit adapt-preview without persistence.
- [ ] 4.2 Add explicit save adapted variant.
- [ ] 4.3 Preserve identity/evidence and only change channel expression/format.
- [ ] 4.4 Support deterministic transforms through code/rules.
- [ ] 4.5 Support model-assisted adaptation as suggestion + explicit save.
- [ ] 4.6 Record provider/run provenance where model used.
- [ ] 4.7 Never mutate source Master.
- [ ] 4.8 Add variant diff.
- [ ] 4.9 Add source-change stale tests.

## 5. Content Matrix planner
- [ ] 5.1 Add bounded matrix suggestion API.
- [ ] 5.2 Inputs include Opportunity/Brief/selected identities/channel registry/existing units.
- [ ] 5.3 Historical performance may inform suggestions without becoming truth.
- [ ] 5.4 Return reason/cost/value signals without ranking as immutable strategy.
- [ ] 5.5 Suggestions never mutate ContentProject.
- [ ] 5.6 User confirmation creates/updates explicit units/targets through existing APIs.
- [ ] 5.7 Add no-Cartesian-explosion bounds.
- [ ] 5.8 Add planner tests.

## 6. Initial channel adapters
- [ ] 6.1 WeChat article adapter using registered rules/profile.
- [ ] 6.2 X thread/single adapter where registered.
- [ ] 6.3 Xiaohongshu image_note requires actual ordered image bytes.
- [ ] 6.4 Douyin spoken_script produces structured script/scenes/B-roll/voice text.
- [ ] 6.5 Douyin estimated SRT is explicitly labeled estimated.
- [ ] 6.6 Do not claim completed video when only script exists.
- [ ] 6.7 No prompt-only Xiaohongshu image readiness.
- [ ] 6.8 Add local package projections/tests.

## 7. Variant checks/render
- [ ] 7.1 Add schema/content check.
- [ ] 7.2 Add exact channel/profile/rule check.
- [ ] 7.3 Add final media rights/ref check.
- [ ] 7.4 Add render/package readiness check.
- [ ] 7.5 Per-check currentness includes profile/adapter version.
- [ ] 7.6 Later blocker for same frozen input blocks delivery where applicable.
- [ ] 7.7 Add warning disposition semantics.

## 8. Candidate manifest v5
- [ ] 8.1 Add pure manifest-v5 builder.
- [ ] 8.2 Freeze source Master identity/hash/context.
- [ ] 8.3 Freeze Variant ID/revision/payload/context.
- [ ] 8.4 Freeze channel/profile/adapter.
- [ ] 8.5 Freeze refs/checks/render/provenance/citations/declarations.
- [ ] 8.6 Add deterministic canonical hash.
- [ ] 8.7 Add v5 freeze idempotency/currentness/live gates.
- [ ] 8.8 Populate channel_variant_revision_id only for v5.
- [ ] 8.9 Preserve v3/v4 freeze paths unchanged.

## 9. Approval/Delivery/Review
- [ ] 9.1 Approval accepts current valid v5 exact hash.
- [ ] 9.2 Live rights/evidence/variant integrity rechecked.
- [ ] 9.3 Delivery Authorization binds v5 candidate hash/account/channel/form/action.
- [ ] 9.4 Publisher cannot change v5 payload.
- [ ] 9.5 Review Preview/Changes/Checks supports v5.
- [ ] 9.6 Project Versions/Overview includes variants and stale state.
- [ ] 9.7 Unknown/reconciliation priority preserved.
- [ ] 9.8 Local packages support v5 without v4/v3 fallback.

## 10. Frontend
- [ ] 10.1 Add matrix suggestion UI with explicit confirmation.
- [ ] 10.2 Add Channel Variants panel in Production.
- [ ] 10.3 Show per-channel variant current/stale/check/render state.
- [ ] 10.4 Add adapt preview/save/regenerate.
- [ ] 10.5 Add variant history/diff.
- [ ] 10.6 Add v5 Review UI.
- [ ] 10.7 Preserve Text/Graphic/Video editor state independence.
- [ ] 10.8 Preserve route/bundle budgets.

## 11. Acceptance/final gates
- [ ] 11.1 Text Master → multiple ChannelVariants browser acceptance.
- [ ] 11.2 Graphic Master → Xiaohongshu variant acceptance.
- [ ] 11.3 Video/script → Douyin controlled deliverable acceptance.
- [ ] 11.4 Source Master change → variant stale.
- [ ] 11.5 Profile change → variant/check stale without history mutation.
- [ ] 11.6 v5 Candidate → Approval → local package.
- [ ] 11.7 v3/v4 historical regression.
- [ ] 11.8 Full backend/frontend/migration/OpenSpec/Ruff/diff gates.
- [ ] 11.9 Independent spec/backend/frontend review.
- [ ] 11.10 Scenario-retention audit for `complete-prd-v1-channel-deliverables`.
- [ ] 11.11 Record local implementation commit and ARCHIVE_READY.
- [ ] 11.12 Do not archive/canonical-sync without explicit authorization.
