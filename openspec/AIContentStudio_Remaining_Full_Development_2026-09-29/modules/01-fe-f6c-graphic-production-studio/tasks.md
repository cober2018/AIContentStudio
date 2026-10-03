## 0. Baseline and guardrails
- [ ] 0.1 Start only after F6B implementation gates pass.
- [ ] 0.2 Re-read current Graphic shell, Production Core and Material/Channel specs.
- [ ] 0.3 Record backend/frontend/bundle/OpenSpec baseline.
- [ ] 0.4 Target zero new tables/migrations; stop and amend if persistence expansion is required.
- [ ] 0.5 No push/deploy/production migration/F6D overlap.

## 1. graphic.master.v2 contract
- [ ] 1.1 Add schema-version adapter dispatch for graphic v2 while preserving v1.
- [ ] 1.2 Define canvas stable ID/order/dimensions/background bounds.
- [ ] 1.3 Define stable layer ID/order/geometry bounds.
- [ ] 1.4 Define text layer content/marks/style tokens.
- [ ] 1.5 Define image layer exact MaterialRevision ref/crop/fit/focal data.
- [ ] 1.6 Define chart layer exact MaterialRevision or bounded chart-spec workflow.
- [ ] 1.7 Define bounded shape/background primitives.
- [ ] 1.8 Reject unknown layers, remote/local infrastructure paths and non-finite geometry.
- [ ] 1.9 Add canonicalization/hash tests.
- [ ] 1.10 Make new Graphic edits default to v2.

## 2. Exact assets and platform presets
- [ ] 2.1 Require embedded image/chart refs in ContentMasterAssetRef.
- [ ] 2.2 Enforce image/chart material kind/hash/project visibility/rights.
- [ ] 2.3 Support repeated material use with distinct layer IDs/placements.
- [ ] 2.4 Resolve exact channel/content-form graphic dimension/media rules.
- [ ] 2.5 Surface profile presets without silently rewriting existing dimensions.
- [ ] 2.6 Add cover/multi-image requirements where exact profile declares them.
- [ ] 2.7 Add stale/current tests when profile/context changes.

## 3. Rendering and package
- [ ] 3.1 Extend GraphicV2 adapter preview and canonical render-input hash.
- [ ] 3.2 Support verified renderer output when a verified renderer capability exists.
- [ ] 3.3 Preserve explicit manual/Studio render attestation fallback.
- [ ] 3.4 Require exact output coverage for every canvas.
- [ ] 3.5 Invalidate render on any layer/canvas/ref/context input change.
- [ ] 3.6 Package exact final image bytes in canvas order.
- [ ] 3.7 Reject missing/duplicate/wrong-kind/mismatched render bytes.
- [ ] 3.8 Add render/package regressions.

## 4. Graphic checks and diff
- [ ] 4.1 Add `graphic_structure`.
- [ ] 4.2 Add text-layer identity coverage using pinned IdentitySnapshot.
- [ ] 4.3 Add exact platform/profile check.
- [ ] 4.4 Preserve common evidence/rights/render checks.
- [ ] 4.5 Add structured canvas/layer diff service.
- [ ] 4.6 Report add/remove/move/resize/text/asset/render changes.
- [ ] 4.7 Add v1↔v2 bounded comparison without persistence.
- [ ] 4.8 Add check/diff tests.

## 5. Provider hooks
- [ ] 5.1 Add provider-neutral material search request boundary.
- [ ] 5.2 Add provider-neutral image generation/variation request boundary.
- [ ] 5.3 Require configured capability; otherwise return typed unavailable.
- [ ] 5.4 Persist accepted provider output as MaterialRevision before canvas use.
- [ ] 5.5 Preserve source URL/ref, provider/version, prompt, rights/license and exact hash.
- [ ] 5.6 Never expose raw credential/provider internals in project UI.
- [ ] 5.7 Add mock/unavailable/provenance tests.
- [ ] 5.8 Leave real provider verification to F7.

## 6. Professional Graphic Studio frontend
- [ ] 6.1 Replace normal Graphic JSON shell with typed Studio.
- [ ] 6.2 Add canvas list/create/delete/duplicate/reorder.
- [ ] 6.3 Add canvas stage with zoom/selection.
- [ ] 6.4 Add text layer create/edit/style/position.
- [ ] 6.5 Add image layer insert/replace/crop/fit/position.
- [ ] 6.6 Add chart layer insert/replace.
- [ ] 6.7 Add layer reorder/visibility/lock controls.
- [ ] 6.8 Add channel dimension preset UI.
- [ ] 6.9 Add project asset picker.
- [ ] 6.10 Add search/generation panels with truthful capability states.
- [ ] 6.11 Add revision history/diff/check/readiness.
- [ ] 6.12 Preserve local dirty vs Workflow dirty independence.
- [ ] 6.13 Historical/archived revisions read-only.

## 7. Candidate/Review/browser/final gates
- [ ] 7.1 Save/reload multi-canvas v2.
- [ ] 7.2 Test text-as-content changes invalidate Candidate/render.
- [ ] 7.3 Test exact asset rights revocation.
- [ ] 7.4 Freeze with exact multi-canvas render.
- [ ] 7.5 Review structured diff and final render.
- [ ] 7.6 Approve and download ordered image package.
- [ ] 7.7 Verify v1/legacy Graphic and Text/Video regressions.
- [ ] 7.8 Run frontend build/bundle isolation.
- [ ] 7.9 Run backend full suite/OpenSpec/Ruff/diff-check.
- [ ] 7.10 Complete isolated browser acceptance and independent reviews.
- [ ] 7.11 Record limitations and local implementation commit.
- [ ] 7.12 Do not canonical-sync/archive without explicit authorization.
