# content-learning-memory Specification

## Purpose
Define evidence-backed insights, explicitly validated learning candidates, and versioned content memory while preserving the separation from Identity, Workflow, and channel strategy.
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

### Requirement: Candidate decisions freeze evidence and serialize mutations

Candidate edits and evidence additions SHALL be allowed only while collecting. Submit, return-to-collecting, validation and archive SHALL enforce the declared lifecycle server-side with optimistic expected_revision and 409 conflict handling. Acceptance SHALL require at least one supporting, owner-authorized reference plus a nonempty validation summary and a verifiable method record; context-only or contradict-only evidence cannot establish acceptance. Accept/reject SHALL freeze proposition, scope, evidence payloads/checksums, contradictions, method, actor and time in the same transaction. Later observation corrections or mutable source changes SHALL NOT rewrite decision history.

#### Scenario: Evidence changes during acceptance
- **WHEN** an evidence update races a validation request against the same expected revision
- **THEN** at most one mutation succeeds; the other returns 409 and creates no partially frozen decision or audit entry

#### Scenario: Multi-sample method without independent samples
- **WHEN** multi_sample validation cites several observations of the same published item as independent samples
- **THEN** the server rejects that method claim or records single-sample limitations; method labels cannot imply nonexistent rule/experiment execution

#### Scenario: Historical accepted candidate
- **WHEN** source observations are superseded after candidate acceptance
- **THEN** historical evidence snapshots remain readable and promotion uses the frozen decision, not refreshed current evidence

### Requirement: All Memory writes pass the validated learning gate

Initial ContentMemory creation SHALL require an accepted source LearningCandidate and use the same promotion gate, including direct POST /content-memory. Memory revision N+1 SHALL require expected_revision, append-only history and an accepted source candidate proving any changed learning claim; concurrent stale saves return 409 without partial revision/audit rows. Destination hierarchy ownership SHALL be validated before freezing scope. Archived entries reject revisions, and archived candidates reject new promotion. Read APIs SHALL label exact and ancestor origin explicitly without treating parent Memory as identity inheritance or exposing sibling/foreign scopes.

#### Scenario: Direct unvalidated Memory creation
- **WHEN** a caller uses POST /content-memory without an accepted source candidate
- **THEN** creation is rejected and no Memory entry, revision or stable-domain change is committed

#### Scenario: Retry promotion concurrently
- **WHEN** two requests promote the same accepted candidate concurrently
- **THEN** database-enforced source-candidate uniqueness and idempotency return one committed Memory result; a conflicting destination or payload returns 409 without orphan entries

#### Scenario: Memory revision conflict
- **WHEN** two revisions target the same current Memory revision
- **THEN** only one revision commits, the other returns 409, and old revision provenance stays unchanged
