## 0. Baseline and scope

- [x] 0.1 Verify F6B 162/162, local main baseline and zero F6C migration before business edits.
- [x] 0.2 Re-read current Graphic shell, Production Core, Material and exact Channel Registry contracts.
- [x] 0.3 Record backend/frontend/bundle/OpenSpec baseline and current migration head.
- [x] 0.4 Preserve v1/Text/Video history; stop to amend the change if a new durable table or destructive migration proves necessary.
- [x] 0.5 Keep F6D–F8, push/deploy/production migrations and canonical sync/archive outside this change.

## 1. Graphic v2 document and explicit upgrade

- [x] 1.1 Register `graphic.master.v2` adapter while retaining `graphic.master.v1` dispatch.
- [x] 1.2 Canonicalize bounded canvas stable IDs, order, dimensions and backgrounds.
- [x] 1.3 Canonicalize bounded stable layer IDs, order, geometry, visibility and lock semantics.
- [x] 1.4 Canonicalize visible text runs and closed typography/style tokens.
- [x] 1.5 Validate image layer crop/fit/focal/opacity and exact MaterialRevision ID.
- [x] 1.6 Validate chart layer exact revision or require chart-spec materialization before freeze.
- [x] 1.7 Validate bounded shape/background primitives.
- [x] 1.8 Reject unknown layers, raw bytes/URLs/paths, non-finite geometry and oversized documents.
- [x] 1.9 Verify deterministic canonical payload/render-input hashes and invalid-data rollback.
- [x] 1.10 Make new Graphic edits default to v2 without changing legacy v1 reads.
- [x] 1.11 Implement current v1→v2 upgrade preview with explicit conversion warnings.
- [x] 1.12 Implement CAS/idempotent append-only v1→v2 fork; generic schema crossing stays rejected.
- [x] 1.13 Preserve duplicate-canvas variant provenance using a same-document source canvas ID.

## 2. Exact references and channel rules

- [x] 2.1 Atomically match every image/chart layer with exact ContentMasterAssetRef slot/placement.
- [x] 2.2 Enforce project visibility, kind, hash, bytes and live rights for embedded media.
- [x] 2.3 Preserve repeated use of one MaterialRevision through distinct stable layer placements.
- [x] 2.4 Bind any text-layer claim to exact FactPackItem checksum and canvas/layer/range locator.
- [x] 2.5 Resolve published exact image-classified channel/content-form profile and dimension/card rules.
- [x] 2.6 Offer profile presets without silently rewriting valid saved dimensions.
- [x] 2.7 Enforce cover/multi-image requirements only when declared by the exact profile.
- [x] 2.8 Verify stale/current behavior when profile, Brief, Boundary or Identity context changes.
- [x] 2.9 Keep legacy text-classified Xiaohongshu form unavailable to direct Graphic freeze.

## 3. Rendering, Candidate and package

- [x] 3.1 Extend Graphic v2 preview and canonical render-input hash without including final output refs.
- [x] 3.2 Gate verified-renderer lineage on an actually verified capability; otherwise report unavailable.
- [x] 3.3 Preserve explicit manual/Studio attestation with truthful `origin=manual`.
- [x] 3.4 Require distinct exact image output coverage for each canvas in canonical order.
- [x] 3.5 Invalidate render after any canvas/layer/text/asset/evidence/context input change.
- [x] 3.6 Freeze v4 Candidate with ordered final outputs and package their exact image bytes.
- [x] 3.7 Reject missing/duplicate/wrong-kind/out-of-order/mismatched output bindings.
- [x] 3.8 Verify Candidate/hash/approval/authorization/package and v1 compatibility regressions.

## 4. Graphic checks, diff and Review

- [x] 4.1 Add append-only input-bound `graphic_structure` check.
- [x] 4.2 Add text-layer fact/identity coverage using exact evidence and pinned IdentitySnapshot.
- [x] 4.3 Report missing semantic provider as unavailable/partial, never verified pass.
- [x] 4.4 Add exact `graphic_platform` profile check; retain common evidence/rights/render gates.
- [x] 4.5 Add structured canvas/layer diff by stable IDs and canonical order.
- [x] 4.6 Report add/remove/move/resize/text/asset/evidence/render changes without whole-graphic text similarity.
- [x] 4.7 Add bounded v1↔v2 comparison without rewriting either revision.
- [x] 4.8 Show frozen Graphic v2 text/cards/final render/checks in project-first Review.
- [x] 4.9 Verify check freshness, diff and Review against current/older Candidate history.

## 5. Honest provider and project-material hooks

- [x] 5.1 Expose project-scoped Material search capability state and request boundary.
- [x] 5.2 Expose project-scoped image generation/variation capability state and request boundary.
- [x] 5.3 Return typed unavailable when no configured/executable provider exists; create no fake output.
- [ ] 5.4 Materialize an actually accepted provider result as MaterialRevision before canvas use.
- [ ] 5.5 Preserve source/provider/version/prompt/hash/license metadata and do not auto-grant public/commercial rights.
- [ ] 5.6 Bind accepted revision to the Project explicitly and mask provider secrets in responses.
- [ ] 5.7 Verify unavailable/mock/provider provenance and live-rights negative paths.
- [x] 5.8 Leave real-provider verification and remote publishing to F7.

## 6. Professional Graphic Studio frontend

- [x] 6.1 Replace the normal Graphic JSON shell with typed Graphic v2 state and explicit save.
- [x] 6.2 Add canvas list/create/delete/duplicate/reorder with stable IDs.
- [x] 6.3 Add canvas stage zoom/selection and bounded geometry editing.
- [x] 6.4 Add visible text layer create/edit/style/position controls.
- [x] 6.5 Add exact image insert/replace/crop/fit/position controls.
- [x] 6.6 Add chart insertion/replacement and bounded shape/background controls.
- [x] 6.7 Add layer reorder/visibility/lock controls.
- [x] 6.8 Add exact profile dimension preset and unsupported-form feedback.
- [x] 6.9 Add project-visible exact asset picker and rights/source details.
- [x] 6.10 Add search/generation panels with truthful unavailable/executable states.
- [x] 6.11 Add checks/readiness, immutable history, explicit v1 upgrade and structured diff UI.
- [x] 6.12 Keep Graphic Master local dirty/save independent from Workflow dirty/save.
- [x] 6.13 Make historical/archived units read-only and handle 409 save conflicts.

## 7. Acceptance and handoff

- [x] 7.1 Save/reload a multi-canvas Graphic v2 document in an isolated environment.
- [x] 7.2 Prove changing text-layer content invalidates old checks/render/Candidate eligibility.
- [x] 7.3 Prove embedded/final MaterialRevision rights revocation blocks live actions.
- [x] 7.4 Freeze exact ordered multi-canvas renders into Candidate v4.
- [x] 7.5 Review structured changes, text and final image order in the browser.
- [x] 7.6 Approve, authorize and inspect local ordered image-package bytes/hashes.
- [x] 7.7 Verify v1/legacy Graphic and Text/Video regressions.
- [x] 7.8 Verify Graphic lazy dependency isolation and all FE-P1 route budgets.
- [x] 7.9 Run full backend, frontend build, OpenSpec all-strict, relevant Ruff and diff-check.
- [ ] 7.10 Complete isolated browser acceptance and independent spec/backend/frontend reviews.
- [x] 7.11 Record exact limitations, changed files, gates and local implementation commit.
- [x] 7.12 Keep canonical sync/archive pending separate authorization.
