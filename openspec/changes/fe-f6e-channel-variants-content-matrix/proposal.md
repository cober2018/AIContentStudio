## Why

North Star requires channel adaptation between a reusable ContentMaster and Candidate approval. Today the project matrix binds Units to a channel and v3/v4 Candidates freeze their source directly; there is no durable ChannelVariant or post-adaptation approval boundary. FE-F6E introduces that boundary without rewriting historical Masters or Candidates.

## What Changes

- Add bounded, read-only Identity × Modality × Channel matrix suggestions; creating a Unit remains an explicit authorized action. Matrix selection never creates an FE-F4 DeliveryTarget before Candidate Approval.
- Add append-only `ChannelVariantRevision` with exact source Master, IdentitySnapshot, profile/adapter, context and request provenance; persist exact variant asset/evidence refs and append-only checks.
- Add a versioned Channel Adapter capability contract with truthful unavailable state. Deterministic adaptation and model suggestions require explicit review/save, never implicit Master mutation.
- Allow newly created channel-neutral Units/Masters while preserving existing channel-bound Unit/Master and Candidate v4 behavior.
- Add Candidate manifest v5 sourced from one current, ready ChannelVariant; extend Review, Approval, authorization and local packaging through schema dispatch without v3/v4 fallback.
- Provide controlled registered-form packages for WeChat article, `x/thread`, Xiaohongshu image_note and Douyin spoken_script. The legacy `x_thread/thread` fallback retains existing v3/v4 behavior but is not an exact published-profile v5 target. Registered `x/single` remains unavailable until a matching adapter is implemented and verified. A script or estimated SRT is not a finished video; prompts are not Xiaohongshu image bytes.
- Preserve the active `complete-prd-v1-channel-deliverables` scenarios and PRD acceptance traceability; do not archive or mark that change superseded in FE-F6E without separate authorization.

## Capabilities

### New Capabilities

- `channel-variants-content-matrix`: matrix suggestions, append-only variants, exact refs/checks, adaptation, v5 provenance and controlled channel deliverables.

### Modified Capabilities

- `fe-f0-f1-project-experience`: add non-mutating matrix suggestions and explicit Unit/target confirmation.
- `production-content-master`: permit explicit channel-neutral source Masters for the v5 path while retaining channel-bound v4 history and gates.
- `fe-f3a-content-project-core`: project Versions and Overview project variant revisions and currentness without a second status source.
- `fe-f4-project-review-distribution`: Review/Approval/Delivery/local package gain v5 schema dispatch and retain exact-hash safety/unknown semantics.
- `fe-p1-frontend-bundle-performance`: lazy-load Matrix/Variant editing without expanding unrelated initial route closures.

## Impact

Additive API models/migration for variant revisions, refs/checks and nullable Candidate variant link; project-scoped variant services/routes; Channel Adapter registry; Candidate v5 builder and Review/Delivery dispatch; Matrix, Production and Review UI. Requires F6D acceptance before business-code apply. No production migration, remote publishing, push, canonical sync or archive is authorized by this proposal.
