## ADDED Requirements

### Requirement: Project read models include real ChannelVariant history
Project Versions SHALL list authorized immutable ChannelVariant revisions with their exact Master/profile/adapter/source provenance. Overview SHALL derive current/stale/blocked state from the actual Variant, check, Candidate and delivery facts; it MUST NOT store a second mutable variant status or let older successful deliveries approve a newer Variant.

For v5, Versions and Overview SHALL project currentness per stable `(unit_id, variant_key)` series; a Unit may have multiple simultaneously current channel Candidates. A newer Candidate in one series MUST NOT mark another series stale solely by ID order. Source Master/context/profile/rights/check drift SHALL still be projected for every affected series. Existing v3/v4 currentness and historical target projections SHALL remain schema-specific rather than being silently replaced by a v5 Unit-wide head.

#### Scenario: Multiple channel series coexist
- **WHEN** one Unit has current WeChat article, X thread and X single v5 Candidates frozen in that order
- **THEN** Versions shows all three exact series and Overview does not label the first two stale merely because the third has a larger Candidate ID

#### Scenario: Master changes after a Variant
- **WHEN** a newer source Master makes a Variant stale
- **THEN** Versions retains both revisions and Overview shows the stale next action without rewriting the old approved Candidate

#### Scenario: Unknown delivery on a Variant Candidate
- **WHEN** a v5 Candidate has unresolved unknown delivery
- **THEN** Overview keeps reconciliation above adaptation or check suggestions in priority
