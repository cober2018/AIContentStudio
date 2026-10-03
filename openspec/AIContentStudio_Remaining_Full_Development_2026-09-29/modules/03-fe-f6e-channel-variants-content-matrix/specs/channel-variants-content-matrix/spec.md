## ADDED Requirements

### Requirement: Content Matrix planning is explicit and non-mutating
The system SHALL be able to propose selected Identity × Modality × Channel units based on available project/identity/channel/performance context. Suggestions MUST NOT auto-create units or mutate Identity/Memory.

### Requirement: ChannelVariantRevision is append-only
The system SHALL persist channel-specific adapted revisions derived from one exact ContentMasterRevision. Historical variants MUST NOT be retargeted when Master or channel profiles advance.

### Requirement: Channel adaptation is separate from identity adaptation
A ChannelVariant SHALL retain the source Master's exact IdentitySnapshot. Channel Adapter changes expression/format for a platform and MUST NOT silently change who is speaking.

### Requirement: Channel Adapter is replaceable
Each adapter SHALL expose capabilities, validation, adaptation, preview, render/check/package behavior through a versioned contract.

### Requirement: Variant refs are exact and immutable
Every final asset/evidence reference used by a ChannelVariant SHALL be frozen as exact revision/checksum/placement metadata without byte copying.

### Requirement: ChannelVariant stale propagation is explicit
Source Master/profile/adapter/rule/ref changes SHALL make old variants stale for new freezes while preserving history.

### Requirement: Candidate v5 freezes post-adaptation content
A v5 Candidate SHALL freeze exact source Master + exact ChannelVariant + exact checks/render/refs. V5 MUST NOT fall back to mutable Master or Publisher formatting.

### Requirement: Existing v3/v4 history remains compatible
Historical Draft-backed and Master-backed Candidates SHALL remain readable/hash-stable and no ChannelVariant backfill is fabricated.

### Requirement: Douyin/Xiaohongshu controlled deliverables remain truthful
Douyin script-only packages SHALL say they are script/estimated-timing deliverables; Xiaohongshu image-note readiness SHALL require actual ordered image bytes with rights/hash verification.

### Requirement: Publisher remains after Approval
Channel Adapter/rendering SHALL complete final platform formatting before Candidate/Approval. Publisher receives only Approved Candidate + Delivery Authorization and cannot alter approved content.
