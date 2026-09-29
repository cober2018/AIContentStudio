## ADDED Requirements

### Requirement: Project Candidate v5 is Variant-backed and schema-dispatched
Freeze SHALL accept one current, project-owned, ready ChannelVariantRevision as a distinct v5 source, canonically bind its exact Master/Identity/profile/adapter/refs/checks/render and set the Candidate's Variant link. V3 Draft and v4 Master source paths SHALL remain unchanged. V5 failure MUST NOT fall back to an older source schema.

#### Scenario: Freeze Variant
- **WHEN** a current Variant passes CAS, context, check, rights, evidence and render gates
- **THEN** v5 creates an immutable Candidate hash without implicit approval or authorization

#### Scenario: Wrong Project Variant ID
- **WHEN** a caller supplies another Project's Variant ID to a freeze or raw Candidate endpoint
- **THEN** authorization denies the request before private payload or media is returned

### Requirement: V5 approval authorization and package preserve frozen adaptation
Review Preview/Changes/Checks SHALL read the frozen v5 Variant and final channel content. Approval SHALL bind exact Candidate ID/hash; new Delivery Authorization SHALL validate current Variant and account/channel/form/action capability. For v5, the authorized channel/form SHALL equal the frozen Variant target rather than the source Unit's channel; pinned identity/account constraints still apply. V3/v4 retain their existing Unit-channel rule. Local package SHALL use approved frozen bytes/content, current live rights and no Draft/v4 fallback; Publisher MUST NOT rewrite approved content. Existing unknown/reconciliation and historical authorization semantics SHALL remain.

#### Scenario: Profile changes before new authorization
- **WHEN** target profile advances after v5 freeze but before a new authorization
- **THEN** authorization is blocked for the stale Candidate while existing approved history remains readable

#### Scenario: V5 package lacks image bytes
- **WHEN** a Xiaohongshu v5 Candidate references an unavailable or revoked image file
- **THEN** package generation fails without remote publication, fake receipt or fallback to v4

#### Scenario: Cross-channel source Unit
- **WHEN** an approved v5 Variant targets a channel different from its source Unit
- **THEN** authorization uses the Variant target and still denies a foreign or incompatible account, without relaxing v3/v4 authorization
