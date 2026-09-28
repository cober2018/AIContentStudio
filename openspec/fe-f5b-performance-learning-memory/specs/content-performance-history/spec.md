# content-performance-history Specification

## Purpose

Define durable published-content recovery, append-only performance/feedback observations, visible historical data coverage and metric-key-specific long-term analysis without fabricating missing data or silently normalizing incompatible platform metrics.

## Requirements

### Requirement: Published content has durable provenance

The system SHALL represent both confirmed Studio publications and external historical imports as owner-scoped PublishedContentRecord rows. Studio records SHALL preserve verifiable Candidate/Delivery/Identity/Account provenance; external records SHALL be explicitly labeled external and MUST NOT be presented as Studio-produced.

#### Scenario: Confirmed Studio publication
- **WHEN** an authorized delivery has a human-confirmed publication Receipt
- **THEN** the system can idempotently create one PublishedContentRecord linked to the real Candidate/Target/Receipt and publication time

#### Scenario: Delivery is not confirmed
- **WHEN** a target is only authorized, package-ready, failed, or unresolved unknown
- **THEN** no record is claimed as published

#### Scenario: Historical external import
- **WHEN** an owner imports an older published item with no Studio Candidate
- **THEN** the record is labeled external_import, stores normalized historical snapshot/provenance, and leaves Studio links null

### Requirement: Historical coverage is explicit

Published history SHALL expose known/missing/unknown coverage for content, identity, account, publication time, metrics, comments and production provenance. Missing historical fields MUST NOT be fabricated.

#### Scenario: Incomplete old record
- **WHEN** an imported record has title and URL but no body, identity or metrics
- **THEN** coverage marks those fields missing/unknown and the UI does not substitute confirmed zeros

### Requirement: Performance observations are append-only

Metrics, qualitative feedback, editorial observations and corrections SHALL be immutable PerformanceObservation rows linked to one PublishedContentRecord.

#### Scenario: Add metric
- **WHEN** an editor/importer records a valid namespaced metric
- **THEN** the observation preserves metric key, value, unit, observation time and source provenance

#### Scenario: Correct observation
- **WHEN** a prior metric was wrong
- **THEN** a new correction/superseding observation is appended and the old row remains auditable

### Requirement: Platform metrics retain meaning

The system MUST NOT silently sum, average or compare different platform metric keys as if equivalent. Aggregation is valid only within the same declared metric namespace/key unless a future explicit normalization rule exists.

#### Scenario: Different metrics
- **WHEN** a cohort contains `youtube.views` and `xiaohongshu.saves`
- **THEN** analysis reports them separately and creates no synthetic combined engagement score

### Requirement: Delivery feedback remains provenance, not fabricated metrics

Existing DeliveryFeedback MAY be referenced as a qualitative observation source. Free-text feedback MUST NOT be parsed into a numeric metric unless an explicit structured observation is created.

#### Scenario: Free-text feedback
- **WHEN** DeliveryFeedback says “表现不错”
- **THEN** the system may preserve it qualitatively but does not invent view/like/share counts

### Requirement: Long-term analysis exposes coverage

Cohort analysis SHALL include record count, observation count, data coverage and limitations, and SHALL warn when compared cohorts have materially different coverage.

#### Scenario: Compare incomplete history
- **WHEN** an older cohort lacks metrics present in a recent cohort
- **THEN** analysis includes a coverage warning instead of treating missing observations as zero
