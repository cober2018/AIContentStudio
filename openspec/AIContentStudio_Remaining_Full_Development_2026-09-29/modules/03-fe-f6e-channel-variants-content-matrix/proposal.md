## Why

North Star defines platform adaptation as a distinct layer after Identity + ContentMaster. The current repository has no `ChannelVariant` persistence and current ContentMaster revisions still carry channel/content-form context. This is sufficient for legacy delivery but does not implement the intended `Identity × Modality × Channel` architecture.

F6E introduces explicit Content Matrix planning and append-only ChannelVariant revisions while preserving all existing v3/v4 Candidates and channel-bound Masters.

## What Changes

- Add a non-destructive Content Matrix suggestion API across Identity × Modality × Channel; suggestions never auto-create units.
- Add append-only ChannelVariantRevision with exact source ContentMasterRevision provenance.
- Add exact ChannelVariant asset/evidence/check lineage.
- Add Channel Adapter contract: capabilities/validate/adapt/preview/render.
- Allow new channel-neutral ContentMaster workflows to derive one or more channel variants.
- Preserve existing channel-bound Master v4 path as legacy/current-compatible.
- Add Candidate manifest v5 sourced from exact ChannelVariantRevision.
- Extend Review/Approval/Delivery schema dispatch to v5.
- Add channel-variant stale propagation when source Master/profile/rules/assets change.
- Add controlled channel packages for WeChat/X/Douyin/Xiaohongshu according to exact registered content forms.
- Absorb and preserve `complete-prd-v1-channel-deliverables` requirements instead of running a conflicting parallel change.

## Migration

Additive migration expected:
- `channel_variant_revision`
- `channel_variant_asset_ref`
- `channel_variant_evidence_ref`
- `channel_variant_check_run`
- nullable `content_asset.channel_variant_revision_id`

No backfill of old Masters/Candidates. Legacy remains legacy.

## Non-goals

- Auto-publishing to unverified platforms.
- Publisher-side content rewriting.
- Auto-creating every Cartesian product of Identity × Modality × Channel.
- Rewriting historical channel-bound Master rows.
