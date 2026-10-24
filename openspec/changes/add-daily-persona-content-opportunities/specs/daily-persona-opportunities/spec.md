## ADDED Requirements

### Requirement: Automatic daily generation per Persona

The system SHALL generate a daily opportunity batch for each enabled eligible Persona using the latest valid profile snapshot and persisted research evidence. The initial defaults SHALL be 08:00 Asia/Taipei and at most five opportunities per Persona, with automatic first generation after bootstrap research. Opening a page or maintaining a chat session MUST NOT be required. The same generic path SHALL serve both starter Personas and future Personas.

#### Scenario: Daily work without user interaction
- **WHEN** an enabled Persona becomes due and the worker is running with usable providers
- **THEN** the batch is processed automatically and its accepted opportunities appear in the ordinary opportunity list and Home

#### Scenario: Different role interpretations
- **WHEN** an event is relevant to both the engineering and lifestyle Personas
- **THEN** each receives an independently justified angle reflecting its profile, audience and boundaries rather than a duplicated generic headline

### Requirement: Event grouping and observed heat

The system SHALL deduplicate items before grouping events and SHALL require positive evidence that reports concern the same event. Uncertain matches MUST remain separate. Heat SHALL use verified source publication time within 48 hours, count each independent source actor at most once and decay with a 24-hour half-life. Copies and linked accounts of the same actor MUST NOT inflate independent-source counts. Heat SHALL be labeled as observed within tracked sources and remain separate from Persona relevance.

#### Scenario: Repeated and syndicated reports
- **WHEN** the same report is fetched repeatedly or the same actor republishes it across accounts
- **THEN** only one independent contribution is counted and repeated collection cannot create a rising trend

#### Scenario: A single valuable source
- **WHEN** one credible source provides useful role-related evidence
- **THEN** it can support an opportunity but cannot be labeled multi-source confirmation or broad public heat

### Requirement: Grounded role evaluation

Candidate evaluation SHALL consider role fit, audience value, evidence quality, angle novelty and timeliness/evergreen value. The initial weights SHALL be 30/25/20/15/10, each on a 0–100 scale; final candidates SHALL receive two independent evaluations and an average of at least 70. The second evaluation MUST NOT see the first score. Rule and prompt versions SHALL be recorded. At most ten final candidates per role/day SHALL be evaluated. Outputs SHALL include why-now, angle, original evidence references, gaps, suggested formats and expiry. Claims MUST NOT invent personal experiences, benchmarks or current facts.

#### Scenario: Insufficient suitable content
- **WHEN** fewer than five candidates pass the declared checks
- **THEN** only passing candidates are saved and the batch records the shortfall reason without fabricating topics

#### Scenario: Evergreen evidence
- **WHEN** useful older evidence supports a role-relevant question
- **THEN** the opportunity may be saved as evergreen with its real evidence age and no fabricated current-event claim

### Requirement: Atomic persistence and cross-day deduplication

The system SHALL atomically create a new ContentOpportunity, its evidence signals, the initial system assessment and existing AuditLog entries. The automated provenance SHALL include owner, Persona and revision, run, event version, angle identity, provider and rule versions. A stable unique key for owner/Persona/event-version/angle SHALL prevent duplicate opportunities across retries or days. Human edits and dismissed/archived/converted states MUST NOT be overwritten. Profile changes MUST NOT reset prior-topic deduplication.

Angle identity SHALL be derived and checked by the server against existing angles for the same role/event; altered headlines or model-generated random IDs MUST NOT bypass deduplication. Current role eligibility, profile version and evidence-processing permissions SHALL be rechecked before final persistence.

#### Scenario: A duplicate daily or bootstrap run
- **WHEN** bootstrap and daily processing or duplicate messages propose the same role/event-version/angle
- **THEN** one opportunity exists and no partial duplicate assessment, signal or audit row is committed

#### Scenario: Genuine event progress
- **WHEN** new evidence establishes a materially new event development
- **THEN** a new opportunity may be created with its new event version and explicit prior-event relation

#### Scenario: Revocation during generation
- **WHEN** a source processing permission is revoked or the Persona profile changes while generation is running
- **THEN** the response remains in historical run accounting but is not persisted as a current eligible opportunity

### Requirement: Durable scheduling and recovery

The system SHALL persist queued/running/succeeded/partial/failed/blocked/unknown run state, business date, profile hash, input evidence snapshot, outputs, provider request references and counts. It SHALL use uniqueness constraints and exclusive task leases. Restart recovery SHALL reuse completed stages, recover due work for the current local date only and not manufacture missed historical daily outputs. Existing Celery UTC behavior and unrelated schedules SHALL remain intact.

#### Scenario: Computer resumes later today
- **WHEN** the worker resumes after the daily due time and today's batch has not completed
- **THEN** it schedules at most one current-day batch and records delayed execution

#### Scenario: Ambiguous provider outcome
- **WHEN** a model request may have been sent but the response cannot be established
- **THEN** its stage is recorded as unknown and is not automatically reissued; unrelated Personas continue

### Requirement: Bounded autonomous execution

Execution SHALL enforce configured limits for searches, source validations, active subscriptions, model requests and tokens before dispatch. Initial bounds SHALL match design.md: bootstrap 8 searches/40 validations/24 active sources per Persona; weekly expansion 4 searches; daily supplemental search 4 searches; daily model budget 12 requests and 120k input/24k output tokens, with a separate equal model bucket for bootstrap. Retries SHALL consume the same bucket. Concurrent reservations MUST prevent exceeding budgets. A parse repair SHALL occur at most once; provider errors SHALL follow bounded retry policy and retain failure evidence.

#### Scenario: Budget exhausted
- **WHEN** a worker would exceed the relevant budget
- **THEN** it performs no additional paid dispatch, preserves successful results and records a visible budget reason

### Requirement: Completion reflects real coverage

A batch with no suitable candidates SHALL report its completed evaluation and reason. Missing search or model capabilities SHALL be blocked/failed, not successful empty results. Partial source coverage SHALL be visible with successful outputs and source-level failures. Acceptance of daily automation SHALL require a natural scheduled execution with no page/user trigger; a manually invoked run alone MUST NOT satisfy it.

#### Scenario: Some sources unavailable
- **WHEN** valid opportunities are written while a required portion of source collection failed
- **THEN** the batch reports partial coverage, retains opportunities and identifies missing source coverage

### Requirement: Editorial evidence gates before ranking

Selection SHALL require fetched article body with supporting verbatim passages, not just titles or feed teasers. Missing or unparseable body SHALL be excluded, regardless of aggregate score. Original publication, republication/update and substantive event dates SHALL be recorded separately with verifiable evidence; unknown dates SHALL remain unknown. Collection, translation or syndication time SHALL NOT refresh an old event. Current reporting and a current event SHALL be distinguished; older evidence may be evergreen without a new-event claim. Both independent evidence-quality scores SHALL be at least 70 in addition to the aggregate threshold.

#### Scenario: Empty article or stale translation
- **WHEN** a candidate has no article body or only a recent translation of an older event
- **THEN** missing-body candidates are excluded and older events cannot become hot merely from the translation date

#### Scenario: A substantive update to an older article
- **WHEN** a dated quoted passage establishes a new development in an older article
- **THEN** the event date may support a current-event candidate while original and update dates remain distinct

### Requirement: Merge equivalent topics and diversify selection

Equivalent questions in the same batch SHALL be combined into one candidate retaining their evidence, including across different article/event IDs. Distinct questions SHALL remain distinct. At most two selected opportunities may have the same primary source actor per Persona per day. Ranking SHALL NOT replace rejected topics with weaker items to reach a quota. The daily limit SHALL be capped at five even if configuration requests more; zero is an acceptable completed result with an explicit reason. Existing human decisions and historical assessments SHALL be preserved.

#### Scenario: Concentrated or repetitive candidates
- **WHEN** candidates exceed the same-source limit or repeat the same editorial question
- **THEN** only distinct qualifying candidates within the source and daily caps are selected, with fewer than five allowed
