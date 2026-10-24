## ADDED Requirements

### Requirement: Automatic source catchup on service recovery
The system SHALL automatically create or resume durable source catchup work when background execution resumes after missed collection. It SHALL use each eligible source's persisted successful-read boundary and a fixed recovery cutoff, without requiring an open page or chat. A source without a known boundary MUST be labeled as first collection with unknown historical coverage. Scheduler heartbeats MUST NOT be presented as precise computer shutdown times.

#### Scenario: Overnight shutdown
- **WHEN** the computer stops at 20:00 and background services resume at 09:00 the next day
- **THEN** due eligible sources are automatically checked from their persisted source boundaries to the recovery cutoff and the pending daily generation waits for the required receipts

#### Scenario: Resume before daily time
- **WHEN** services resume at 07:00
- **THEN** catchup runs immediately and daily generation waits until 08:00 Asia/Taipei, checking any newly due source work before freezing evidence

### Requirement: Bounded historical retrieval with durable progress
The system SHALL follow public history or pagination links explicitly supplied by a supported source, or an already configured documented date/cursor mechanism. It SHALL preserve per-source progress and deduplicate repeated item versions. The initial per-source per-batch budget SHALL be ten requests including retries and 300 scanned entries, with a daily prerequisite wait budget of fifteen minutes of accumulated background operation excluding stopped or sleeping intervals. Existing fetch safety and size limits SHALL apply to every history request. Budget exhaustion SHALL produce an explicit incomplete receipt rather than silent truncation or an endless wait.

#### Scenario: More than thirty recoverable entries
- **WHEN** a source exposes 85 entries since its previous known boundary through supported pagination within the declared budget
- **THEN** all 85 are inspected and new versions are persisted without a hidden thirty-entry total cap

#### Scenario: High volume exceeds budget
- **WHEN** a source still has unvisited history after ten requests or 300 scanned entries
- **THEN** collected items are preserved and its receipt reports the budget limit and unconfirmed target interval before allowing partial-coverage generation

#### Scenario: Repeated outage during catchup
- **WHEN** the process stops after a page commit and resumes later
- **THEN** it resumes from durable progress without resetting the consumed budget or duplicating versions, excludes the stopped interval from waiting time, and checks the additional recovery interval before a not-yet-started daily batch

### Requirement: Evidence-based source coverage
Every source receipt SHALL distinguish processing completion from coverage completeness and retain target interval, observed evidence, inspected/new counts, failure reason, and any known or unconfirmed gap. Complete coverage SHALL require demonstrable continuity of the accessible source endpoint through the target interval. A successful response, zero new entries, one old article, search results, or HTTP 304 alone MUST NOT establish complete coverage. Unknown missing counts or timestamps MUST remain unknown.

#### Scenario: Truncated feed without history
- **WHEN** the current feed no longer reaches the previous known boundary and exposes no supported historical entry point
- **THEN** available entries are persisted and the receipt reports partial coverage, history unavailable, and the affected interval with unknown exact missing count

#### Scenario: Historical hotlist cannot be recovered
- **WHEN** only the current hotlist is accessible
- **THEN** the system preserves the current snapshot and explicitly states that rankings disappearing during downtime cannot be verified

#### Scenario: An unchanged cached endpoint has an earlier gap
- **WHEN** the endpoint returns HTTP 304 while previous historical coverage is unconfirmed
- **THEN** the successful check does not erase the historical gap or claim full catchup

#### Scenario: Access failure
- **WHEN** a source cannot be read because of network failure, authentication requirement or parsing failure within its budget
- **THEN** its receipt reports that actual reason and never presents the failure as no new content

### Requirement: Collection barrier before opportunity generation
The system SHALL gate every automated opportunity-producing path, including bootstrap generation, on concluded receipts for the Persona's required source windows. Scheduler dispatch and worker execution SHALL both enforce the barrier. Pending work SHALL yield execution and retain a waiting state instead of blocking a worker on another queue. Each Persona SHALL depend only on its eligible sources and SHALL share source receipts when applicable. After all required receipts conclude, generation SHALL freeze its coverage snapshot and use only committed eligible evidence. Partial or failed source receipts SHALL remain visible while other qualifying evidence can be used.

#### Scenario: Research queue is processed first
- **WHEN** the worker receives a daily research task before pending source collection tasks
- **THEN** no evidence freeze or generation model call occurs and the task waits until its source prerequisite is concluded

#### Scenario: One source fails and others succeed
- **WHEN** all required sources conclude and one has a failure receipt
- **THEN** the system automatically evaluates available evidence, labels the daily batch with incomplete coverage and names the missing source and interval

#### Scenario: No usable body remains
- **WHEN** catchup concludes but no eligible fetched article body is available
- **THEN** the batch records zero topics and the actual evidence/collection reason without inventing topics

### Requirement: Idempotent recovery across business days and model stages
The system SHALL preserve the existing daily uniqueness, five-topic maximum, item-version uniqueness, source leases, and paid-call ledger. Duplicate scans and late workers MUST NOT create duplicate active window work, overwrite a newer lease result, or reset budgets. Catchup SHALL NOT automatically regenerate or top up a completed day's topics. Only the current Asia/Taipei business day SHALL receive delayed daily generation. An already-started model stage SHALL retain its frozen evidence and unknown requests MUST NOT be reissued automatically; new catchup not included in that frozen run SHALL be disclosed.

#### Scenario: Today's batch is already complete
- **WHEN** the computer restarts after today's topics were generated
- **THEN** source catchup continues without regenerating, replacing or supplementing those topics

#### Scenario: Several days offline
- **WHEN** services resume after several calendar days
- **THEN** source history is checked within budget, missed old daily runs are recorded as skipped, and only the current day is eligible for automatic delayed generation

#### Scenario: Restart during a model call
- **WHEN** a daily run has frozen evidence and a model request has an unknown outcome
- **THEN** catchup may continue independently but that model request is not automatically replayed and the UI identifies the run's original coverage snapshot

#### Scenario: Cross-midnight recovery
- **WHEN** yesterday's waiting or running daily work is resumed after midnight
- **THEN** business-day validation prevents new yesterday-topic writes while preserving already committed evidence and outcomes and evaluating today's work through its own barrier

### Requirement: Eligibility and permissions survive catchup
The system SHALL reuse source ownership, manual association, active Persona/profile, validation, collection and processing permission rules. Sources excluded by these rules SHALL show the reason rather than being fetched or counted as fully covered. Required source membership SHALL be rechecked before evidence freeze and permission checks SHALL also run before source access and model use. A shared source SHALL reuse its bounded collection result across eligible Personas without leaking data across owners.

#### Scenario: Source permission is revoked during recovery
- **WHEN** the user pauses a source or revokes its processing permission while a batch is in progress
- **THEN** later source requests and model use stop as applicable, the receipt records exclusion and the user's setting is not restored automatically

#### Scenario: Source is newly associated
- **WHEN** an eligible source is linked to a Persona before its daily evidence snapshot is frozen
- **THEN** the source's required check is incorporated into that Persona's barrier; a link made after freeze applies to subsequent normal work without rewriting the frozen run

### Requirement: User-visible and immutable daily coverage reporting
The existing discovery status, source registry and research history SHALL display recovery progress, target interval, per-source outcome, counts, gap reason and affected Persona. Daily runs SHALL retain the coverage snapshot used at generation time. A later successful collection MUST NOT rewrite a past daily batch's coverage as complete. Read-only API/UI access MUST NOT trigger work and SHALL enforce owner isolation.

#### Scenario: Recovery progress is inspected
- **WHEN** the user opens Content Opportunities during catchup
- **THEN** the UI shows that today's topics are waiting for collection, with per-source progress and actionable reasons rather than a generic empty page

#### Scenario: Source recovers after partial generation
- **WHEN** a failed source becomes readable after today's partial-coverage topics were generated
- **THEN** the source view shows its new check result while the daily history preserves the gap that existed during generation

### Requirement: Existing editorial quality and natural recovery acceptance
Catchup SHALL retain original, republication and event-time distinctions, fetched-body requirements, evidence checks, duplicate merging, source diversity and zero-to-five daily topic limits. Collection time MUST NOT make old content hot. Acceptance SHALL include actual Beat/Worker stop-and-resume execution and UI/API readback, not just manual method invocation or an enabled flag.

#### Scenario: Old article discovered after downtime
- **WHEN** recovery retrieves an older article
- **THEN** it can only be considered with its real dates and appropriate evergreen/reporting classification, without acquiring a new event timestamp from collection

#### Scenario: Natural recovery acceptance
- **WHEN** background services are stopped and resumed in an isolated environment with controlled source histories
- **THEN** persisted execution evidence proves catchup receipts precede the not-yet-started day's evidence freeze, repeated restarts produce no duplicate topics, and incomplete source history is visible in the normal page
