# FE-F6E Channel Variants & Content Matrix Design

## 1. Content Matrix planner

The planner produces bounded proposals, not durable truth:

```json
{
  "items":[
    {
      "identity_snapshot_id": 1,
      "modality": "text",
      "channel": "wechat",
      "content_form": "article",
      "reason_codes":["identity_relevant","channel_value"],
      "estimated_cost":"medium"
    }
  ]
}
```

Inputs may include Opportunity/Brief, selected identities, channel registry, existing content units and historical performance summaries. It MUST NOT mutate identity/memory or create ContentUnits without explicit user confirmation.

## 2. ChannelVariantRevision

Recommended fields:
- id
- project_id
- content_unit_id
- source_master_revision_id
- variant_key
- revision_no
- parent_revision_id
- channel_id
- content_form
- adapter_key / adapter_version
- channel_profile_version_id
- payload_schema
- payload_json
- payload_hash
- context_hash
- source_master_payload_hash
- source_master_context_hash
- source_kind
- edit_summary_json
- idempotency_key / request_fingerprint
- created_by / created_at

Unique:
- `(content_unit_id, channel_id, content_form, revision_no)`
- `(content_unit_id, channel_id, content_form, idempotency_key)`

A variant belongs to the same pinned identity as its source Master; channel adaptation cannot repin identity.

## 3. Exact refs/checks

Variant refs are references, never byte copies:
- ChannelVariantAssetRef
- ChannelVariantEvidenceRef
- ChannelVariantCheckRun

The default adaptation can inherit exact Master refs, but the persisted variant freezes the exact final set so later Master changes do not rewrite history.

## 4. Channel Adapter

Contract:

```text
capabilities(db, channel, form)
validate(db, source_master, variant_payload)
adapt(db, source_master, target, options)
preview(db, variant)
render(db, variant)
required_checks(db, variant)
package_projection(db, variant)
```

Adapters are replaceable capabilities; they do not own business history.

## 5. Staleness

Variant currentness includes:
- exact source Master ID/payload/context hash
- exact Channel Profile revision/config hash
- adapter key/version
- exact refs
- exact rules/check profiles

If source Master changes, old Variant remains readable but becomes stale for new Candidate freeze.

Existing approved Candidate history does not mutate.

## 6. Candidate manifest v5

V5 freezes:
- Project/Unit/Identity
- exact source Master identity/hash/context
- exact ChannelVariant ID/revision/payload/context hash
- channel/content form/profile
- exact final refs
- exact variant checks
- exact render
- adapter/provenance
- citations/declarations

`ContentAsset.channel_variant_revision_id` is populated for v5.
v3/v4 remain readable and unchanged.

## 7. Legacy channel-bound Master compatibility

Existing v4 Master Candidates continue to work.

For new cross-channel flow:
- ContentMaster may be channel-neutral.
- ChannelVariant supplies target channel/content-form.
- Candidate v5 freezes the post-adaptation result.

No migration guesses old ChannelVariant rows.

## 8. Channel packages

Initial controlled adapters should cover registered current forms:
- WeChat article
- X thread/single where registered
- Xiaohongshu image_note: actual ordered image bytes required
- Douyin spoken_script: structured script/scenes/B-roll/voice text and explicitly estimated SRT when no real timed media exists

Do not claim Douyin video completion when only script exists.
Do not claim Xiaohongshu image-note ready when only prompts exist.

## 9. Frontend

Project Matrix:
- suggest matrix
- user confirms selected units/targets
- never auto-creates without confirmation

Production:
- source Master workspace
- Channel Variants panel
- per-channel status/stale/checks/preview/diff
- explicit adapt/regenerate/save

Review:
- v5 variant-aware preview/changes/checks/publish

## 10. Legacy active change

Before final F6E archive, audit every requirement/scenario in:
`complete-prd-v1-channel-deliverables`

Preserve it in F6E/F7 tests/specs, then mark superseded only under archive authorization.
