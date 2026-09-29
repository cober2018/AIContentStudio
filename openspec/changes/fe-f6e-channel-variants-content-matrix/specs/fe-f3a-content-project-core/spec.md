## ADDED Requirements

### Requirement: Project read models include real ChannelVariant history
Project Versions SHALL list authorized immutable ChannelVariant revisions with their exact Master/profile/adapter/source provenance. Overview SHALL derive current/stale/blocked state from the actual Variant, check, Candidate and delivery facts; it MUST NOT store a second mutable variant status or let older successful deliveries approve a newer Variant.

#### Scenario: Master changes after a Variant
- **WHEN** a newer source Master makes a Variant stale
- **THEN** Versions retains both revisions and Overview shows the stale next action without rewriting the old approved Candidate

#### Scenario: Unknown delivery on a Variant Candidate
- **WHEN** a v5 Candidate has unresolved unknown delivery
- **THEN** Overview keeps reconciliation above adaptation or check suggestions in priority
