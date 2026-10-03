# FE-F7 Capability Integrations & Delivery Design

## 1. Capability kinds

Registry shall support at least:
- model_provider
- tool_provider
- data_connector
- search_provider
- image_provider
- video_provider
- tts_provider
- asr_provider
- renderer
- channel_adapter
- browser_automation
- publisher
- existing node/rule/skill compatibility kinds

Business code resolves exact `key + version`.

## 2. Durable capability metadata

Recommended `CapabilityRegistration`:
- key
- kind
- version
- provider
- source
- license
- status
- capabilities_json
- dependencies_json
- permissions_json
- side_effects_json
- config_fingerprint
- created_at / updated_at

Recommended `CapabilityVerification`:
- capability_registration_id
- scope_json
- verified_at
- verified_by
- verification_kind
- result
- evidence_json (safe metadata only)
- expires_at / invalidated_at

No secret/cookie/token/local credential path may be serialized.

Statuses:
`discovered / installed / enabled / vetted / active / deprecated / disabled`.

`active` does not mean a Publisher action is verified for every account.

## 3. Publisher verification scope

Publisher verification is exact:
- platform/channel
- account identity
- content form
- action
- publisher key/version
- verification time

Only Real Platform acceptance may mark remote side-effect capability verified.

## 4. Data Connector bridge

Current Connector/ConnectorEndpoint remains the durable connector configuration.

Add explicit mapping from a Data Source plugin/capability to a Connector endpoint. Generic Connector existence alone does not imply `notion/sql/media/...` availability.

Execution:
`Workflow Data Node → data_connector capability → ConnectorEndpoint → DataSnapshot/SourceDocument/Fact mapping`.

Existing authorization and secret env references remain.

## 5. Material search

Material search providers return candidate metadata only.
Selecting/importing a result creates Material + MaterialRevision after:
- source/provenance capture
- download/byte hash verification
- MIME sniff
- rights/license declaration
- public/model/commercial use state

A preview URL is not an approved asset.

## 6. Image/video generation

Provider output:
- is untrusted until bytes are fetched/verified
- becomes MaterialRevision
- stores provider/version/prompt/generation metadata/hash
- gets rights/use flags according to provider/license/config
- never directly mutates a Master

Graphic/Video Studio explicitly accepts provider results into a new revision.

## 7. TTS/ASR

TTS produces exact audio MaterialRevision.
ASR returns transcript/cues; accepted transcript content only enters a Video Master on explicit save.
Provider run history and exact audio/source hashes remain auditable.

## 8. Renderer capability

Renderer verification records exact supported:
- modality
- payload schema
- channel/content form if applicable
- input/output MIME
- version
- deterministic/verified/manual properties

Render output becomes exact MaterialRevision if it is media.

## 9. Settings

Settings capability inventory:
- configured vs executable vs verified
- safe provider/version/status
- scope/last verification
- reason unavailable
- explicit probe/verify action

Read-only inventory never triggers network calls.

## 10. Delivery

Delivery keeps:
`Approved Candidate + Delivery Authorization → Publisher`.

Publisher receives frozen package/manifest and may not rewrite content.

If action capability is not verified:
- `copy_package` / manual flow may remain available if packageable
- automatic remote action is unavailable

Unknown side-effect remains reconciliation-needed.

## 11. Real verification

Verification tests are explicit side-effect actions and require:
- selected account
- selected form/action
- confirmation
- safe output metadata
- read-back or human verification where possible

No background probe marks a Publisher verified.

## 12. Legacy channel deliverables

Douyin/Xiaohongshu controlled local packages from F6E satisfy local/manual delivery.
Remote publishing remains unavailable until a real Publisher adapter is configured and verified.
