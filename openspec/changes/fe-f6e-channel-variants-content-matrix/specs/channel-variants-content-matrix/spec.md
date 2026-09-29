## ADDED Requirements

### Requirement: Matrix suggestions are bounded and non-mutating
The system SHALL suggest a bounded Identity × Modality × Channel selection using current authorized project, identity, Registry and coverage-qualified history context. Each proposal SHALL show reason, estimated cost/value, confidence and unknowns as suggestions rather than approved strategy; it MUST NOT create Units, targets, Identity revisions, Content Memory or a durable matrix state without an explicit user action.

#### Scenario: Inspect suggestions
- **WHEN** an editor requests matrix suggestions for a Project
- **THEN** the service returns a bounded proposal with reason/cost signals and no new business rows

#### Scenario: Confirm a subset
- **WHEN** the editor explicitly selects two suggested Unit targets
- **THEN** only those selections pass through existing authorized Unit APIs, with normal execution-history fork/archive semantics

### Requirement: ChannelVariantRevision is append-only and project-scoped
Each variant series SHALL have one stable Unit × channel × content_form × variant_key identity. Revisions SHALL be append-only, CAS/idempotent and bound to one exact project-owned source ContentMasterRevision, pinned IdentitySnapshot, source payload/context hashes and target Registry/profile/adapter versions. A key MUST NOT silently change its channel or content form; old rows MUST remain readable.

#### Scenario: Save after preview
- **WHEN** an authorized editor saves a validated adaptation against the current expected series head and source Master
- **THEN** the server appends revision N+1 and preserves revision N and its source/profile hashes

#### Scenario: Concurrent variant save
- **WHEN** another request advances the same series or its source context before commit
- **THEN** the stale request returns 409 with no partial revision, ref, check or event rows

#### Scenario: Raw ID from another project
- **WHEN** a caller requests or mutates a foreign Project's Variant through a raw-ID or project-scoped route
- **THEN** authorization fails before payload, refs, checks or media metadata are returned

#### Scenario: Archived Unit history
- **WHEN** an authorized user opens a Variant of an archived Unit
- **THEN** historical revisions remain readable but save, adapt, checks, freeze and rerun mutations are denied

### Requirement: Variant refs and checks freeze exact final adaptation
Each variant SHALL persist its exact ordered MaterialRevision refs, FactPackItem evidence refs and input-bound append-only check results. Inherited Master refs MUST be explicitly frozen in the final variant set without copying bytes/text. Save and downstream gates SHALL validate Project visibility, live bytes/hash/rights, frozen Fact Boundary scope and latest applicable check currentness.

#### Scenario: Adapt an ordered image set
- **WHEN** a Xiaohongshu variant reorders two eligible Project images from its Master
- **THEN** the saved refs pin those MaterialRevision IDs, hashes and final order independently of later Master edits

#### Scenario: Revoked media before package
- **WHEN** a referenced MaterialRevision loses public-use rights after Candidate freeze
- **THEN** package/unfinished delivery is blocked while the approved historical Candidate remains readable

### Requirement: Channel Adapter is replaceable and versioned
An adapter SHALL expose capabilities, validation, adaptation, preview, render, required checks and package projection against an exact registered channel/content_form and published profile. Its key/version and relevant config hashes SHALL enter Variant and Candidate provenance. Unsupported or unverified capability MUST return typed unavailable with no invented result.

#### Scenario: Registered adapter unavailable
- **WHEN** a client requests an adaptation that needs an unverified model or renderer
- **THEN** the request reports unavailable and writes no Variant, media or successful execution provenance

#### Scenario: Deterministic preview
- **WHEN** an executable adapter projects a concrete payload from a current source Master
- **THEN** preview remains non-durable until the editor explicitly saves a validated variant

### Requirement: Adaptation preserves speaker and evidence boundaries
A ChannelVariant SHALL keep its source Master's exact IdentitySnapshot and SHALL NOT mutate the source Master. Model-assisted edits SHALL be suggestions with verifiable runtime provenance, explicit preview/accept and save. New claims MUST resolve to the current frozen Fact Boundary or remain incomplete; adaptation MUST NOT fabricate rights or fact approval.

#### Scenario: Model suggestion rejected
- **WHEN** an editor rejects a model-suggested channel rewrite
- **THEN** neither Master nor Variant history is modified

#### Scenario: Unsupported new claim
- **WHEN** adaptation adds a factual claim with no eligible FactPackItem
- **THEN** readiness identifies the unsupported claim and Candidate freeze remains blocked

### Requirement: Variant currentness is explicit
Currentness SHALL compare the exact source Master/head/context, target profile/config, adapter version, rules/check inputs and final refs. A drifted Variant MUST be stale for new freezes without rewriting historical variants or approved Candidates. A new version requires explicit save/rebase and fresh checks/render where affected.

#### Scenario: Source Master advances
- **WHEN** the Unit saves a newer ContentMasterRevision after a Variant was created
- **THEN** the prior Variant stays readable but cannot be newly frozen as a current v5 Candidate

#### Scenario: Channel profile advances
- **WHEN** the published target profile or relevant rule version changes
- **THEN** currentness reports stale profile/check inputs while old approved Candidate hashes remain unchanged

### Requirement: Candidate v5 freezes post-adaptation content
Candidate manifest v5 SHALL canonically freeze one current ChannelVariantRevision and its exact source Master, Project/Unit/Identity, target channel/form/profile, adapter/model provenance, final refs/rights, checks, render, citations and declarations. Freeze MUST enforce ownership, currentness, CAS/idempotency, live rights/evidence/bytes and render availability. V5 failure MUST NOT fall back to v4/v3 or allow Publisher formatting after Approval.

#### Scenario: Freeze a ready variant
- **WHEN** a current Variant passes exact checks/render/rights gates
- **THEN** one immutable v5 Candidate/hash is created without approval or delivery authorization

#### Scenario: Unsupported final image
- **WHEN** a Xiaohongshu Variant contains only image prompts or missing image bytes
- **THEN** freeze fails without a package-ready Candidate or fabricated media

### Requirement: V5 Review and delivery use the exact approved result
Review, Content Approval, Delivery Authorization and local package SHALL dispatch v5 separately from v3/v4, bind the immutable Candidate ID/hash and recheck applicable live safety gates. New v5 authorization SHALL match the frozen Variant target channel/form/profile, not the source Unit's channel; pinned IdentitySnapshot and any Unit-bound account MUST remain authorized. Free-form account profile data MUST NOT be treated as verified channel ownership: local packaging is labeled manual, and remote effects require exact account/channel/form/action verification. V3/v4 retain their Unit-channel rule. Publisher MUST NOT rewrite approved payload/media. Existing authorized history remains frozen, and unknown remote outcomes SHALL require reconciliation rather than automatic resend.

#### Scenario: Local package after approval
- **WHEN** a current v5 Candidate is separately approved and authorized for a local action
- **THEN** its package contains only frozen approved content and byte/hash-verified media without a remote call

#### Scenario: V5 package cannot be built
- **WHEN** frozen render shape or referenced bytes cannot be verified
- **THEN** packaging fails closed without v4/v3 fallback or a false receipt

#### Scenario: Cross-channel Variant authorization
- **WHEN** a channel-bound source Master has a v5 Variant for a different registered target channel
- **THEN** authorization checks the approved Variant target and pinned account/identity compatibility, without rewriting the source Unit channel or admitting an unrelated target account

### Requirement: Registered controlled channel deliverables are truthful
Initial adapters SHALL operate only on exact published forms with matching executable adapters. WeChat article and `x/thread` SHALL be formatted before approval. The `x_thread/thread` legacy fallback SHALL retain its existing v3/v4 behavior but SHALL NOT serve as a v5 target without its own published profile. Already-registered `x/single` SHALL remain unavailable until a matching adapter is implemented and verified. Xiaohongshu image_note SHALL include ordered real image bytes; Douyin spoken_script SHALL include script/scenes/B-roll/voice text and label SRT as estimated when no real timed media exists. Neither script nor prompt-only output SHALL be described as a finished video or complete image note.

#### Scenario: Registered form without an adapter
- **WHEN** an editor selects the published `x/single` form before a matching adapter is executable
- **THEN** adaptation reports unavailable without creating a Variant or implying that the legacy `x_thread` fallback provides that adapter

#### Scenario: Douyin script package
- **WHEN** an approved spoken_script Candidate is packaged without produced video/audio timing
- **THEN** the files and UI say script-only and estimated SRT, and the target is not marked published

#### Scenario: Two target accounts
- **WHEN** one approved Candidate is separately authorized for two ContentAccounts and one handoff fails
- **THEN** each target retains independent package access, attempt/receipt history and unknown-reconciliation state

#### Scenario: Approved image order or bytes drift
- **WHEN** an approved image_note Candidate's ordered image list or exact file bytes no longer match its frozen manifest
- **THEN** package delivery is blocked and any changed content requires a new Variant, Candidate and approval

### Requirement: Legacy histories and V1 acceptance remain honest
Existing channel-bound Masters and v1/v2/v3/v4 Candidates SHALL remain readable and hash-stable without invented Variant links or backfill. The active V1 deliverables change SHALL retain its three-channel readiness, exact account/rights/handoff scenarios and PRD §15 fifteen criteria/§16 thirty real-Topic gate as separate evidence; FE-F6E local success MUST NOT automatically mark overall V1 accepted or archive that change.

#### Scenario: Open historical Candidate
- **WHEN** a v3/v4 Candidate without ChannelVariant is opened after v5 is introduced
- **THEN** it follows its original schema path and its manifest/hash remain unchanged

#### Scenario: Old draft without complete approval evidence
- **WHEN** a historical Douyin or Xiaohongshu draft lacks the exact frozen Candidate and approval required for controlled handoff
- **THEN** it remains readable but is not represented as a ready v5 deliverable

#### Scenario: Record FE-F6E acceptance
- **WHEN** local WeChat/X/Douyin/Xiaohongshu paths pass FE-F6E checks
- **THEN** the acceptance record names those paths only and leaves unverified PRD criteria/real-Topic counts unclaimed
