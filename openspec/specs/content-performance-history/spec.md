# content-performance-history Specification

## Purpose
Define owner-scoped published content history and append-only performance observations with verifiable provenance, explicit coverage, and platform-specific measurement semantics.
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

### Requirement: Publication timestamps and receipt provenance are distinct

Studio materialization SHALL require a human_confirmed Receipt with delivered_at, validate its Candidate hash, Target and owner, and enforce a unique delivery_receipt_id. Publication confirmation time and actual published_at SHALL be distinct. Existing receipt timestamps produced by utcnow() on submission SHALL NOT be relabeled as actual publication time; published_at SHALL remain unknown unless the operator explicitly supplies a verified publication timestamp with provenance. External imports SHALL NOT set Studio links. Normal create/update APIs SHALL NOT bypass Studio qualification or rewrite frozen provenance.

#### Scenario: Late manual receipt
- **WHEN** an operator confirms old published content today without its actual publication date
- **THEN** the record stores today's confirmation provenance but leaves published_at unknown and excludes it from dated cohorts with an explicit missing-date count

#### Scenario: Reconciliation has no receipt
- **WHEN** a target becomes human_confirmed through reconciliation but no qualifying Receipt exists
- **THEN** synchronization creates no published record; the UI links to the explicit confirm-reconciled publication action, rather than synthesizing a Receipt from target status

#### Scenario: Explicit confirmation after reconciliation
- **WHEN** the owner submits POST /published-content/confirm-reconciled with target_id, a nonempty actual-publication attestation, an idempotency key and optional verified published_at for a receipt-less human_confirmed target whose unknown attempts are all explicitly resolved
- **THEN** the server validates Target ownership, immutable Candidate/hash and existing mutation boundaries, locks the target, and atomically creates one human_confirmed Receipt, its PublishedContentRecord and audit/project events; Target/Attempt reconciliation state and remote systems remain unchanged, and absent actual publication time remains unknown

#### Scenario: Conflicting or invalid recovery confirmation
- **WHEN** a recovery action is retried concurrently, conflicts in its attestation payload, or targets foreign, archived, mismatched-hash or still-unknown delivery facts
- **THEN** an identical retry returns the existing Receipt/history result, a payload or state conflict returns 409, unauthorized references disclose no data, and no partial Receipt/history/event or remote side effect is created

#### Scenario: Multiple receipt entry points
- **WHEN** a qualifying Receipt is saved through generic delivery or the legacy article-handoff endpoint
- **THEN** owner-validated materialization and retry semantics are identical; failure never commits a partial publication/event or triggers a remote operation

### Requirement: Observation aggregation has a declared measurement grain

Observations SHALL validate finite numeric values, metric namespace/key, unit, UTC timestamps, ordered period bounds and source provenance. Analysis SHALL group only compatible namespace/key/unit/window/measurement-mode observations. Snapshot counters SHALL select one latest effective observation per record and measurement scope as of the cutoff, not sum successive cumulative snapshots. Superseded observations SHALL be excluded from current aggregates but remain readable. Supersedes links MUST target the same owned published record and compatible metric scope, with no cycles or competing correction tips. Interval totals SHALL aggregate only declared non-overlapping intervals; unsupported or overlapping combinations SHALL report an explicit limitation.

#### Scenario: Two cumulative reads
- **WHEN** a record has 100 views yesterday and 150 views today
- **THEN** latest-snapshot analysis reports 150, not 250, and preserves both original observations

#### Scenario: Correct and retry import
- **WHEN** a correction supersedes an observation or an external import is retried concurrently
- **THEN** effective statistics count the correction only, imports use a database-enforced owner/channel/external-key identity, and mismatched repeated payloads return 409 without rewriting historical data

#### Scenario: Incompatible units or windows
- **WHEN** matching metric keys have incompatible units or measurement windows
- **THEN** analysis separates or rejects the incompatible inputs instead of silently averaging them

### Requirement: History and analytical references enforce ownership

Every history, observation, Insight, feedback and cohort reference SHALL resolve through the authoritative resource ownership boundary, including legacy target authorization. Archived sources MAY remain readable but SHALL NOT be mutable. Missing coverage SHALL be derived or verified from actual fields and authorized observations rather than trusted client assertions. Insight analysis_source/provider metadata SHALL be server-assigned; unverified rule/model capability SHALL report unavailable instead of accepting spoofed analysis provenance.

#### Scenario: Foreign referenced feedback
- **WHEN** an owner supplies another owner's DeliveryFeedback, observation or cohort record ID
- **THEN** the request discloses no referenced content and commits no partial observation or Insight

#### Scenario: Assert missing metrics as known
- **WHEN** import coverage claims metrics are known without valid observations
- **THEN** authoritative coverage remains missing or unknown, not known or zero

### Requirement: Third-party models import account data over MCP

MCP SHALL offer `list_accounts` and `import_account_metrics`. An import SHALL name one owned account, its source kind (screenshot, copied text or export file) with file name and checksum, and one row per work with title, publish time, optional form, metrics from that platform's fixed metric set, and the metrics marked uncertain. Unknown metrics SHALL be rejected. Rows SHALL match existing works by account, platform, title and publish time or create external works, and each metric SHALL be stored as an observation recording the source and checksum. The result SHALL report created, updated and skipped counts and link to the batch in 效果复盘.

#### Scenario: 抖音 works export
- **WHEN** the model reads 作品列表导出.xlsx and imports it for the 抖音 account
- **THEN** each work appears in 效果复盘 under that account with its plays, likes, shares, comments and favorites

#### Scenario: Unknown metric
- **WHEN** a row carries a metric outside the platform's set
- **THEN** the import is rejected and nothing is written

### Requirement: Imports are batches the user can undo

Each import SHALL be recorded as a batch with source, time and counts, and 效果复盘 SHALL let the user undo a whole batch, removing its observations and any works it created that hold no other data.

#### Scenario: Undo
- **WHEN** the user undoes a batch
- **THEN** its observations and the works it alone created are gone

### Requirement: Imported material does not pile up

Source screenshots and files SHALL NOT be uploaded or stored; only extracted values, the file name and checksum are kept. A source with a checksum already imported for that account SHALL be skipped. For the same work, metric and day only the latest value SHALL be kept.

#### Scenario: Same day re-import
- **WHEN** the same work's plays are imported twice on one day with different values
- **THEN** only the later value remains for that day

### Requirement: Platform storage is cleaned on a schedule

The daily maintenance SHALL also: clear the full text of discovery source documents older than the configured days (default 30) that are not used as a topic or work source, keeping title and link; delete generated result files older than the configured days (default 7) that were never accepted as material; delete candidate materials older than the configured days (default 30) that were never accepted and are attached to no project. The database SHALL be compacted weekly. Accepted materials, project files on external drives and finished videos SHALL NOT be touched. Settings SHALL show storage sizes, the last cleanup result, editable day limits and a run-now button.

#### Scenario: Unused generated result
- **WHEN** a generated image file has sat unaccepted for more than 7 days
- **THEN** the next cleanup deletes the file and reports it

#### Scenario: Accepted material
- **WHEN** a material was accepted, however old
- **THEN** cleanup leaves it and its file alone

