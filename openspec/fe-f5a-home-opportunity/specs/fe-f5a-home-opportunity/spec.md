# fe-f5a-home-opportunity Specification

## Purpose

Define Content Opportunity as the decision layer before ContentProject and Home as a bounded projection of current opportunities, projects and pending human decisions.

## Requirements

### Requirement: Opportunity is distinct from Topic and Project

The system SHALL persist ContentOpportunity before ContentProject. Opportunity MUST NOT replace TopicBrief and MUST NOT itself become a production root.

#### Scenario: Create opportunity
- **WHEN** an editor records a possible content opportunity
- **THEN** Opportunity persists without creating Topic, Project, FactPack or WorkflowRun

#### Scenario: Convert opportunity
- **WHEN** the user explicitly confirms an eligible Opportunity
- **THEN** one primary ContentProject is created through the conversion contract

### Requirement: Signals reference source truth

Opportunity signals SHALL reference existing source/business records with bounded annotations rather than duplicate raw SourceDocument, DataSnapshot or DeliveryFeedback payloads.

#### Scenario: Source signal
- **WHEN** an authorized SourceDocument is attached
- **THEN** the signal stores source reference/checksum metadata while the source body stays in SourceDocument

#### Scenario: Unauthorized signal
- **WHEN** a user references an inaccessible DataSnapshot or feedback row
- **THEN** the operation is rejected without disclosing the resource

### Requirement: Opportunity assessments are append-only

Opportunity judgment SHALL be stored as immutable assessment revisions with optimistic concurrency.

#### Scenario: Save revision
- **WHEN** expected_revision equals current revision
- **THEN** N+1 is created and N remains readable

#### Scenario: Stale save
- **WHEN** a newer revision already exists
- **THEN** the request returns 409 with no partial assessment

### Requirement: Recommendations remain suggestions

Identity/modality/channel recommendations SHALL NOT mutate Identity, create IdentitySnapshot, bind ContentUnit or authorize delivery.

#### Scenario: Identity recommendation
- **WHEN** an Assessment references Persona/Account/Series
- **THEN** hierarchy is validated and no identity state is changed

#### Scenario: Similarity unknown
- **WHEN** no reliable history comparison has run
- **THEN** similarity remains `unknown` rather than `none`

### Requirement: Opportunity conversion is explicit and idempotent

Opportunity→Project conversion SHALL be an explicit transactional action using the current Assessment revision and an idempotency key.

#### Scenario: Successful conversion
- **WHEN** conversion succeeds
- **THEN** Project, Conversion, CreativeBrief v1, selected Source bindings, ProjectEvent and Opportunity converted state commit together

#### Scenario: Repeat conversion
- **WHEN** the same Opportunity is converted again
- **THEN** the existing primary Project is returned and no duplicate Project is created

#### Scenario: Conversion failure
- **WHEN** any required mutation fails
- **THEN** no partial Project/Brief/Source/Event/status change remains

### Requirement: Opportunity evidence never auto-becomes Fact Boundary

Opportunity signals MAY seed Project Source bindings but MUST NOT automatically create/freeze/bind FactPack or Project Fact Boundary.

#### Scenario: Convert with sources
- **WHEN** selected SourceDocument signals are included in conversion
- **THEN** Project receives normal Source bindings and Fact Boundary remains absent

### Requirement: Project origin is traceable

Projects created from Opportunity SHALL retain durable origin Opportunity and Assessment revision provenance.

#### Scenario: Opportunity archived later
- **WHEN** origin Opportunity becomes archived
- **THEN** Project origin remains historically readable

### Requirement: Home is a projection

Home SHALL derive Opportunities, active Projects, pending decisions and identity alerts from existing business state. Home MUST NOT persist a second task/state system.

#### Scenario: Reload Home
- **WHEN** the user reloads `/home`
- **THEN** cards are reconstructed from current Opportunity/Project/Review/Identity facts with no HomeTask rows

### Requirement: Today's opportunities use deterministic ordering

Home SHALL use explicit lifecycle/priority/time-sensitivity/expiry/recency rules rather than an opaque hidden AI rank score.

#### Scenario: Converted opportunity
- **WHEN** Opportunity becomes converted
- **THEN** it no longer appears in actionable Today Opportunities

#### Scenario: Expired opportunity
- **WHEN** relevant_until is in the past
- **THEN** it is not promoted into Today's list merely because it was recently edited

### Requirement: Pending decisions reuse responsible domains

Home SHALL reuse Project Overview and FE-F4 review/distribution decision facts instead of recalculating a second review state.

#### Scenario: Unknown delivery
- **WHEN** FE-F4 reports reconciliation required
- **THEN** Home surfaces reconciliation and does not show generic Ready/Delivered

#### Scenario: Duplicate alert
- **WHEN** the same entity issue appears through multiple projections
- **THEN** Home deduplicates using stable code/entity refs

### Requirement: Future cadence is truthful

Home SHALL NOT fabricate scheduled publication dates.

#### Scenario: No scheduling model
- **WHEN** no real planning-date business object exists
- **THEN** Home returns `schedule=false` and an empty upcoming section

### Requirement: AI Opportunity Analysis is optional

Automated analysis MAY use a replaceable model capability, but persisted Assessment revisions remain the truth and manual assessment MUST work without it.

#### Scenario: Analyzer unavailable
- **WHEN** no verified analyzer capability is configured
- **THEN** the system reports unavailable and creates no fake Assessment
