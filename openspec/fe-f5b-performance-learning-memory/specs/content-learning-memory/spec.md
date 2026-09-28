# content-learning-memory Specification

## Purpose

Define evidence-backed Insights, Learning Candidates, explicit validation and append-only Content Memory. Performance observations and accepted learnings never silently mutate stable Content Identity, Workflow defaults or channel strategy.

## Requirements

### Requirement: Insights preserve evidence and limitations

ContentInsight SHALL be immutable and SHALL record its statement, cohort/scope, supporting and contradicting references, coverage, limitations, confidence and analysis provenance.

#### Scenario: Save Insight
- **WHEN** a human/rule/model analysis produces a validated bounded insight
- **THEN** the Insight stores exact source refs and limitations and remains readable if a later Insight supersedes it

#### Scenario: Analyzer unavailable
- **WHEN** no verified analysis capability is configured
- **THEN** no fabricated Insight is created

### Requirement: Learning Candidate is not an automatic strategy change

A LearningCandidate SHALL represent a proposition awaiting evidence/validation. Categories SHALL include identity, audience, channel, format, topic and workflow.

#### Scenario: High-performing content
- **WHEN** one published item has strong performance
- **THEN** the system may create or suggest a LearningCandidate but MUST NOT update Identity, Workflow default or channel strategy

### Requirement: Learning evidence can support or contradict

LearningCandidate evidence SHALL preserve source type/entity, role (`support|contradict|context`) and snapshot/checksum metadata when available.

#### Scenario: Contradicting sample
- **WHEN** another published item weakens a candidate proposition
- **THEN** contradictory evidence remains visible and is not discarded

### Requirement: Candidate validation is explicit

Only a ready_for_review LearningCandidate MAY be accepted or rejected. Acceptance SHALL record validation method, validation summary, actor and time, and requires at least one valid evidence reference.

#### Scenario: Accept candidate
- **WHEN** an authorized human accepts a candidate with evidence and validation rationale
- **THEN** status becomes accepted and no Identity/Workflow/Memory change happens implicitly

#### Scenario: Reject candidate
- **WHEN** a candidate is rejected
- **THEN** evidence/history remains readable and no long-term configuration changes

### Requirement: Content Memory is versioned and separate from Identity

ContentMemoryEntry SHALL be scoped to owner/Brand/Persona/Account/Series and SHALL use append-only ContentMemoryRevision rows. Memory is dynamic learned context, not a stable Identity profile field.

#### Scenario: Promote accepted learning
- **WHEN** an accepted LearningCandidate is explicitly promoted to a validated memory scope
- **THEN** a ContentMemory entry/revision is created with source candidate/evidence provenance and stable Identity rows remain unchanged

#### Scenario: New memory revision
- **WHEN** an existing memory statement is refined
- **THEN** revision N+1 is appended and N remains readable

### Requirement: Promotion is a separate explicit action

LearningCandidate acceptance alone SHALL NOT create Content Memory. Promotion requires a separate authorized action and idempotency protection.

#### Scenario: Accept but do not promote
- **WHEN** a candidate is accepted
- **THEN** no ContentMemory row exists until explicit promotion

#### Scenario: Promote twice
- **WHEN** the same promotion request is retried with the same idempotency key
- **THEN** the same memory result is returned without duplicate revisions

### Requirement: Stable domains require their own save/version action

Promoted memory MUST NOT automatically update ContentBrandRevision, ContentPersonaRevision, Account/Series revisions, Persona/Account/Series Workflow defaults or channel configuration.

#### Scenario: Identity learning promoted
- **WHEN** an Identity Learning candidate is promoted to Content Memory
- **THEN** Identity UI may show the learning and offer follow-up, but no Identity revision is created automatically

### Requirement: Identity Memory workspace reads validated memory

The FE-F3B Content Memory tab SHALL display applicable validated ContentMemory entries/revisions with scope origin, source LearningCandidate, applicability and limitations while keeping stable Identity fields separate.

#### Scenario: Persona memory
- **WHEN** a Persona has active validated memory
- **THEN** its Memory tab shows that memory without rendering it as an authored Persona profile field
