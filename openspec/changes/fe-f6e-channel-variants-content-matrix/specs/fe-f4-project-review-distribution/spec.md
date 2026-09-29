## ADDED Requirements

### Requirement: Project Candidate v5 is Variant-backed and schema-dispatched
Freeze SHALL accept one current, project-owned, ready ChannelVariantRevision as a distinct v5 source, canonically bind its exact Master/Identity/profile/adapter, versioned canonical Variant payload/hash, refs/checks/render and set the Candidate's Variant link as its only source pointer. V5 `draft_id`, `topic_brief_id` and `content_master_revision_id` SHALL be null; the source Master is reached through the Variant and frozen manifest. The Candidate's `channel`, `content_form` and `artifact_kind` projections SHALL match the Variant's frozen target and exact published profile. V3 Draft and v4 Master source paths SHALL remain unchanged. V5 failure MUST NOT fall back to an older source schema.

#### Scenario: Freeze Variant
- **WHEN** a current Variant passes CAS, context, check, rights, evidence and render gates
- **THEN** v5 creates an immutable Candidate hash without implicit approval or authorization

#### Scenario: Wrong Project Variant ID
- **WHEN** a caller supplies another Project's Variant ID to a freeze or raw Candidate endpoint
- **THEN** authorization denies the request before private payload or media is returned

#### Scenario: V5 carries a conflicting Master pointer or target projection
- **WHEN** a v5 Candidate carries a Draft/Master source FK or a cached channel/form/artifact_kind inconsistent with its frozen Variant/profile
- **THEN** schema-dispatched readers and gates reject it before any Review content, authorization or package is returned

### Requirement: V5 approval authorization and package preserve frozen adaptation
Review Preview/Changes/Checks SHALL dispatch on manifest `schema_version` before any Draft/Master source-pointer heuristic and read the frozen v5 Variant's canonical payload and final channel content. Approval SHALL bind exact Candidate ID/hash; new Delivery Authorization SHALL validate the current Variant, the account's active ownership through the pinned identity, any Unit-bound account constraint, and the target channel/form/action. A local `copy_package` or `manual_handoff` MAY be authorized as an explicitly manual action without inferring verified remote capability from free-form account profile data; any remote effect SHALL additionally require verified exact account/channel/form/action capability. For v5, the authorized channel/form SHALL equal the frozen Variant target rather than the source Unit's channel. V3/v4 retain their existing Unit-channel rule. Local package SHALL use approved frozen bytes/content, current live rights and no Draft/v4 fallback; Publisher MUST NOT rewrite approved content. Existing unknown/reconciliation and historical authorization semantics SHALL remain.

V5 Approval and new Authorization SHALL compare Candidate currentness to the latest Candidate and current Variant revision in the same `(unit_id, variant_key)` series, not the greatest Candidate ID for the entire Unit. Another series or v3/v4 Candidate MUST NOT invalidate a current v5 Candidate by ID ordering alone; true source/context/profile/rights/check drift still blocks. V3/v4 currentness and existing DeliveryTargets retain their prior semantics.

#### Scenario: Independent channel approvals and targets
- **WHEN** current WeChat, X thread and X single v5 Candidates were all frozen before Review decisions
- **THEN** each can be approved and authorized in any order without another series' later Candidate ID blocking it

#### Scenario: Same-series replacement with legacy coexistence
- **WHEN** only X thread advances to a new Variant/Candidate while a v3/v4 Candidate and other v5 series also exist
- **THEN** old X thread cannot receive new approval or authorization, the other series remain current absent real drift, and v3/v4 history and target access keep their existing rules

#### Scenario: Profile changes before new authorization
- **WHEN** target profile advances after v5 freeze but before a new authorization
- **THEN** authorization is blocked for the stale Candidate while existing approved history remains readable

#### Scenario: V5 package lacks image bytes
- **WHEN** a Xiaohongshu v5 Candidate references an unavailable or revoked image file
- **THEN** package generation fails without remote publication, fake receipt or fallback to v4

#### Scenario: Cross-channel source Unit
- **WHEN** an approved v5 Variant targets a channel different from its source Unit
- **THEN** authorization uses the Variant target and still denies a foreign or incompatible account, without relaxing v3/v4 authorization
