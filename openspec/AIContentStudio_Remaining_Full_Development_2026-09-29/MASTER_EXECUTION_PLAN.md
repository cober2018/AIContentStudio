# AIContentStudio Remaining Full Development — Master OpenSpec Execution Plan

Date: 2026-09-29
Verified planning baseline: local `main@ca52aa5` with an uncommitted FE-F6B working tree.
Current FE-F6B OpenSpec status: **131/162**, **31 remaining**.
This package is a planning/development package. It does not itself modify the repository.

## 1. What is already substantially complete

The current repository already has the stable product/platform foundation:
- F0/F1 product shell, ContentProject workspace and Content Matrix CRUD
- F2 persisted Production Workflow + debugger
- F3A ContentProject core / CreativeBrief / Fact Boundary / project source/material references
- F3B Content Identity / IdentitySnapshot / defaults
- F4 Candidate / Approval / Delivery Authorization / Unknown reconciliation
- F5A Opportunity / Home
- F5B Performance / Learning / Content Memory
- F5C System Assets / Knowledge / Settings
- F6A Production Core / ContentMasterRevision / v4 Candidate / modality adapters
- F6B backend A+B and professional Text Studio frontend 15–20

The Text path is already architecturally functional:
`text.master.v2 → checks → Candidate v4 → Approval → local package`.

## 2. What is still incomplete relative to the North Star

### A. FE-F6B final close — 31 tasks
The professional Text Studio is implemented but not fully accepted. Remaining work is exact cross-layer reference validation, legacy/cross-modality regression, full browser acceptance and final gates.

### B. FE-F6C Graphic Production Studio
Current state is only an F6A JSON shell. Missing professional multi-canvas/card editing, text-as-content layers, image/chart layers, project asset integration, variants, AI/search capability hooks, structured diff, professional checks and full browser acceptance.

### C. FE-F6D Video Production Studio
Current state is only an F6A JSON shell. Missing professional script/shot/timeline workspace, source asset placement, voice/TTS, subtitles, overlays, music, cover, long→short/ratio transformations, render lineage, structured diff, checks and full browser acceptance.

### D. FE-F6E Content Matrix planning + ChannelVariant + Channel Adaptation
North Star defines `ChannelVariant`, but the current codebase has no ChannelVariant model/service. Missing:
- content-matrix suggestion/planning across Identity × Modality × Channel
- append-only ChannelVariant revisions
- Channel Adapter `capabilities/validate/adapt/preview/render`
- channel-specific stale propagation
- Candidate freezing of the post-adaptation artifact
- schema-aware Review/Delivery for ChannelVariant
- legacy channel-bound Master compatibility
- reconciliation of the still-active `complete-prd-v1-channel-deliverables` change

### E. FE-F7 Replaceable Capabilities + real integrations
North Star expects replaceable Model/Tool/Data/Search/Image/Video/TTS/ASR/Renderer/Channel Adapter/Publisher capabilities. Current registry is still a narrower in-memory plugin registry and Settings truthfully reports many unavailable capabilities. Missing:
- durable capability verification state
- Connector→Data Source execution mapping
- material search provider
- image/video generation provider contracts and real configured adapters
- TTS/ASR capability boundary
- capability verification by exact account/channel/form/action/time
- real-provider/project-asset ingestion with rights/provenance
- verified Publisher capability where a real supported integration exists
- controlled Douyin/Xiaohongshu deliverables without false remote-publish claims

### F. FE-F8 Production Readiness / Operations / Golden & real-platform acceptance
North Star requires observability, untrusted-capability safety, five-level tests and real-platform verification. Current Settings explicitly says auth is development-header mode and must not fake organization/SSO/tenant support. Remaining engineering completion:
- production-safe authentication boundary using existing User/Role semantics
- secure secrets/config behavior
- capability/runtime audit and correlation
- health/readiness, worker/runtime observability
- storage/runtime deployment hardening
- migration/backup/restore rehearsal
- Identity Golden / Content Golden / Integration acceptance
- real platform read-back/human verification before marking Publisher capability verified

Organization/invite/SSO/multi-tenant administration is **not** made a mandatory feature by this package because the canonical product-settings spec explicitly says it is not implemented and North Star does not define its product contract.

## 3. Execution order

1. `00-fe-f6b-final-close`
2. `01-fe-f6c-graphic-production-studio`
3. `02-fe-f6d-video-production-studio`
4. `03-fe-f6e-channel-variants-content-matrix`
5. `04-fe-f7-capability-integrations-delivery`
6. `05-fe-f8-production-readiness-operations`

Once a master apply is authorized, Codex may continue from one passing module to the next without requesting a new product-design decision unless a stop condition below is reached.

## 4. Global stop conditions

Stop implementation and amend the relevant OpenSpec only when:
- current code contradicts a core North Star invariant;
- a destructive migration/backfill would be required;
- a new long-lived business object not specified here becomes necessary;
- external provider credentials are required to claim real-platform verification;
- a provider/platform cannot satisfy the claimed capability contract;
- a security boundary would need to be weakened to continue.

Missing external credentials do not block implementation of the capability framework; the capability remains `unverified/unavailable` and MUST NOT be presented as supported.

## 5. Global invariants

1. Source / Evidence / Fact separation.
2. Append-only historical revisions.
3. Historical IdentitySnapshot binding.
4. ContentProject as the business container.
5. Text / Graphic / Video as peer modalities.
6. Shared evidence boundary across identity expressions.
7. Identity adaptation separate from channel adaptation.
8. ContentMasterRevision bound to identity + modality.
9. Final text/media/metadata all belong to the approved Candidate.
10. Approval binds exact Candidate hash.
11. Content Approval separate from Delivery Authorization.
12. Publisher never changes approved content.
13. Unknown external side effect is never auto-retried.
14. Human is first-class.
15. providers/runtimes are replaceable.
16. external Skill is not core business truth.
17. unverified platform capability is never shown as supported.
18. new platform support extends Adapter/Renderer/Publisher/Rule, not Workflow Engine.
19. feedback never directly mutates long-term identity.
20. Content Brain is a projection, not a black-box state table.

## 6. Migration strategy

- F6B: no new migration expected.
- F6C: target no new table; use ContentMasterRevision/AssetRef/EvidenceRef/CheckRun.
- F6D: target no new table; use ContentMasterRevision/MaterialRevision and existing refs.
- F6E: additive migration is expected for ChannelVariant revision/ref/check lineage and Candidate linkage.
- F7: additive migration is expected if durable Capability verification records are introduced.
- F8: avoid business-data migrations unless required for production security/operational metadata; never rewrite historical content.

Every additive migration must validate SQLite compatibility where supported by the project and PostgreSQL production semantics. No migration may fabricate historical evidence, identity, approval or provider verification.

## 7. Legacy active change reconciliation

`openspec/changes/complete-prd-v1-channel-deliverables` remains active and incomplete.

Its requirements SHALL be preserved and absorbed:
- Douyin spoken-script structured package / estimated SRT → F6E ChannelVariant/local package
- Xiaohongshu image-note actual ordered image group → F6C + F6E
- target authorization / manual handoff / rights / hash checks → existing F4 + F6E/F7
- no false claim of finished video or remote Douyin/Xiaohongshu publishing → preserved
- real-account/manual verification → F7/F8

Do not execute a conflicting parallel implementation of that old change. Before final archive, perform scenario-retention audit and mark it superseded/absorbed only with explicit archive authorization.

## 8. Final definition of "designed version complete"

`Opportunity
→ ContentProject
→ identities + CreativeBrief + Fact Boundary
→ Content Matrix plan
→ Text / Graphic / Video professional production
→ ContentMasterRevision
→ ChannelVariant
→ Candidate
→ Content Approval
→ Delivery Authorization
→ safe local/assisted/verified delivery
→ Receipt
→ Performance / Learning`

and the system can answer the observability lineage questions for project, identity, brief, evidence, master, variant, workflow, provider, media, checks, candidate, approval, target, receipt and learning.

## 9. Master acceptance

Before declaring the entire roadmap complete:
- all module OpenSpecs are 100% complete;
- backend full suite passes;
- frontend type/build/bundle checks pass;
- browser acceptance passes for all three Production Studios;
- migration up/down/preflight behavior is tested;
- OpenSpec all-strict passes;
- lint/diff-check pass;
- Identity Golden passes;
- Content Golden passes;
- Integration path passes through ChannelVariant;
- real platform capability is marked verified only where actual read-back/human verification occurred;
- all unavailable/unverified providers remain truthful;
- no canonical sync/archive occurs without explicit authorization.
