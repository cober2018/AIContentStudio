## Context

FE-F6A–F6D use append-only ContentMasterRevision and Candidate v4. `ContentUnit.channel_id` and Master channel/form columns are nullable, but save/readiness currently treat a Unit's channel as Master context and v4 freezes that context directly. Project Matrix has explicit Unit CRUD; Review/Delivery bind immutable Candidate hashes. The source F6E package calls for a separate post-Master ChannelVariant and Candidate v5, while the active V1 deliverables change still owns ten unclosed tasks. FE-F6E business-code apply requires F6D gates and a fresh base audit; this change is specification-only until then.

## Goals / Non-Goals

**Goals:** Non-mutating matrix planning; append-only, project-owned ChannelVariant revisions with exact source/profile/adapter/ref lineage; channel-neutral source path; v5 Candidate/Review/Approval/local-package dispatch; truthful controlled registered-form packages and legacy scenario retention.

**Non-Goals:** Auto-creating the matrix Cartesian product; publisher-side rewriting; silently converting old v3/v4 Candidates; unverified remote publication; new Identity or Fact Boundary; auto-closing the active V1 change; production migration.

## Decisions

1. **Matrix is a projection, not a second plan database.** Suggest from current Opportunity/Brief/Identity/Registry/existing Units and coverage-qualified Performance summaries. Bound result size and show reason/unknown/cost data. A user-selected subset creates Units through existing project APIs with their normal authorization and fork/archive rules. A selected channel is a production target, not an FE-F4 DeliveryTarget; Delivery Authorization is permitted only for an approved exact Candidate. No suggestion silently changes Identity, Memory, Project, Unit or delivery authorization. Alternative: durable Cartesian matrix rows; rejected because they duplicate Unit truth and create speculative content.

2. **One variant series per explicit key.** A stable `variant_key` identifies an alternative under a Unit × channel × content_form. Revision numbers and optimistic CAS are scoped to that key; unique `(unit_id, variant_key, revision_no)` and `(unit_id, variant_key, idempotency_key)` prevent race duplicates. Each revision pins source Master ID/payload/context, Unit IdentitySnapshot, exact published profile ID/version/config hash, adapter key/version, payload/context hash, actor, parent and request fingerprint. A key cannot silently switch channel/form or source Unit. Alternative: mutable latest row; rejected because frozen Candidates need immutable provenance.

3. **Refs and checks are first-class exact records.** New asset/evidence refs point to existing MaterialRevision and FactPackItem, never copied bytes or text. Final refs are explicit even when inherited from Master, with role/order/placement, checksum/rights snapshot and source locator. Checks are append-only, keyed to exact variant input/profile/adapter/rule hashes. Live rights/evidence and current checks are revalidated at freeze, approval, new authorization and package gates as appropriate. Alternative: implicit Master refs; rejected because adaptation can change order or omit assets.

4. **Adapter is replaceable but cannot invent authority.** Versioned `capabilities/validate/adapt/preview/render/required_checks/package_projection` resolve the exact Registry form and published profile. Deterministic adaptation can propose a concrete payload. Model-assisted adaptation returns a suggestion and verifiable runtime receipt, followed by explicit accept and durable save; unavailable providers fail closed. No adapter can repin Identity, add unsupported claims, bypass the frozen Fact Boundary or grant public-use rights. Alternative: publisher-side transformation; rejected because approval must cover final bytes/content.

5. **Channel-neutral is opt-in, not a backfill.** A newly created Unit may intentionally have `channel_id=null`; its Master then has null channel/form and is source-only, not v4 Candidate-ready. Channel-bound Units/Masters remain unchanged and can still use v4. A channel-bound Master may also explicitly source a variant, with its original channel preserved as provenance. Source Master currentness uses the exact Unit context; variant currentness additionally uses its target profile/adapter/rules. No historical row is relabeled neutral.

6. **V5 is a separate Candidate source path.** A pure canonical manifest builder freezes exact Project/Unit/Identity, source Master, ChannelVariant, target channel/form/profile, ordered refs/checks/render, citations/declarations and adapter/model provenance. `ContentAsset.channel_variant_revision_id` is populated only for v5. Freeze uses CAS/idempotency and checks current Master/variant/context plus live rights and byte hashes. Review/Approval/Delivery/Package dispatch on schema before touching Draft/v4 fields, enforce the same raw-ID ownership/archive boundary, and never fall back to v4/v3 after a v5 failure. Approved/authorized history stays immutable; unknown delivery remains unknown and requires reconciliation.

7. **Controlled forms reflect actual Registry capability.** Start with `wechat/article`, `x_thread/thread`, `xiaohongshu/image_note`, `douyin/spoken_script` only where the exact form/profile is registered and executable. X single is unavailable until registered. Xiaohongshu requires ordered real image bytes/hash/rights; Douyin script/estimated SRT is labeled script-only, not a finished video or timed audio. Missing/withdrawn bytes block package while preserving the approved Candidate. Package construction performs no remote call.

8. **Active V1 acceptance is audited, not auto-closed.** Preserve its three-channel readiness, Douyin script package, Xiaohongshu ordered images, account-separated authorization/reconciliation and PRD §15/§16 acceptance evidence as named FE-F6E/F7 scenarios. A passing local package does not imply 15 criteria or 30 real Topics are accepted. `complete-prd-v1-channel-deliverables` stays active until a separately authorized scenario-retention and archive decision.

   The seven active legacy scenarios map to: old-draft unreadiness → new capability history requirement; approved Douyin script → controlled deliverable; missing image and changed order/bytes → controlled deliverable/ref/manifest gates; separate accounts and revoked rights → v5 delivery/live gates; overall V1 status → explicit PRD acceptance requirement. This mapping is a preservation plan, not a claim that those scenarios already pass.

## Risks / Trade-offs

- [Existing channel-bound Master semantics bleed into neutral flow] → Explicit source-only null-channel path and regression of v4 behavior before enabling v5.
- [Multiple target profiles or adapter updates silently retarget a variant] → Pin version/config hashes and require a new variant revision; preserve old approved history.
- [Suggested or model-produced claims exceed evidence] → Mark unsupported facts as incomplete, require exact Fact Boundary refs, and save only after explicit acceptance.
- [A package or publisher edits approved content] → Build from frozen v5 manifest and exact bytes; block unsafe live rights, never rewrite at delivery.
- [Migration downgrade would lose v5 history] → Additive nullable link and new tables; refuse downgrade while v5-linked rows exist, rehearse only on isolated SQLite/PostgreSQL.
- [Matrix/Variant UI inflates common routes] → Lazy module boundary and FE-P1 import-graph budget gate.

## Migration Plan

After F6D acceptance, inspect the actual Alembic head and models. Add tables for variant revisions/refs/checks plus nullable `content_asset.channel_variant_revision_id`, with foreign keys, bounded values, indexes, unique CAS/idempotency keys and a data-safe downgrade preflight. No historical backfill. Implement adapter/currentness before v5 builder, then schema dispatch, UI and isolated browser acceptance. Run isolated SQLite up/down/up and PostgreSQL-compatible DDL/rollback checks; never run a production migration under this change's specification approval.

## Open Questions

No product choice is required for specification review. Exact current channel/profile availability and schema/migration details must be rechecked on the F6D-complete base before apply. If that audit reveals a destructive migration, an unplanned durable business object or a safety-boundary reduction, stop and revise the proposal rather than proceeding.
