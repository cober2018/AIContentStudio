## ADDED Requirements

### Requirement: Persona-scoped technology value policy
The system SHALL bind a versioned technology policy explicitly to the technology Persona without changing the lifestyle Persona policy. Technology hot candidates SHALL require a verified substantive event within 48 hours. Technology recent_report candidates SHALL require verified original reporting or substantive technical progress within 30 days. Evergreen candidates SHALL have no universal evidence-age cutoff and SHALL demonstrate durable audience value supported by fetched original content. Unknown dates SHALL remain unknown. Collection, republication and discovery times MUST NOT establish freshness.

#### Scenario: Useful older technical report
- **WHEN** a 10-day-old report supports an engineering-relevant question
- **THEN** it can enter recent_report evaluation without being rejected for exceeding 48 hours or labeled breaking news

#### Scenario: Old architecture material
- **WHEN** older original material supports a durable architecture question
- **THEN** it can enter evergreen evaluation with its actual evidence age and without invented current version or availability claims

#### Scenario: Missing current proof
- **WHEN** an old or undated source cannot support a candidate's necessary current API or price claim
- **THEN** that claim must be removed or the candidate deferred and relabeling as evergreen cannot bypass evidence requirements

### Requirement: Preserve scoring and bounded evaluation
The system SHALL preserve independent dual scoring, weights 30/25/20/15/10, average threshold 70, each evidence score at least 70, maximum ten evaluated candidates and five saved opportunities per Persona/day, and maximum two per primary source actor. The timeliness dimension SHALL evaluate freshness for hot and current relevance or lasting value for non-hot types. Existing observed heat calculation SHALL remain separate. Policy and prompt versions SHALL be frozen in the run. Sources, quotes, human decisions and old assessments MUST NOT be rewritten.

#### Scenario: No qualifying topics
- **WHEN** all candidates fail factual or scoring gates after the broader technology classification
- **THEN** zero remains valid with actual reasons and no quota-filling retry or lowered threshold

### Requirement: Distinct recommendation lifetime
New technology opportunities SHALL receive deterministic recommendation lifetimes from creation of 48 hours for hot, 7 days for recent_report and 30 days for evergreen. Source age SHALL remain separate. Old recommendation deadlines MUST NOT be extended automatically. Expiry MUST NOT reset cross-day deduplication.

#### Scenario: Recommendation is not new evidence
- **WHEN** a six-month-old evergreen source produces a qualifying new recommendation
- **THEN** the recommendation can remain actionable for 30 days while its six-month-old source date remains visible
