## ADDED Requirements

### Requirement: Authorized daily local producer
When explicitly enabled, the existing discovery catchup worker SHALL run the verified local Radar free-mode producer before importing the day's report and freezing technology daily evidence. Production SHALL use the existing configured daily hour and Asia/Taipei business date, without a second scheduler, paid signals or historical daily replay. A durable per-day receipt and exclusive local lock SHALL prevent repeated execution. Only the installed, pinned producer and fixed free-mode arguments MAY execute; arbitrary commands from API or report content MUST NOT execute.

#### Scenario: Daily generation precedes assessment
- **WHEN** the authorized technology daily collection runs at or after its configured daily hour
- **THEN** at most one bounded producer invocation occurs for that business day, validated output is atomically published and imported before the daily evidence snapshot, and repeat scans reuse its receipt

#### Scenario: Failure or interruption
- **WHEN** generation fails, times out, or a prior invocation has an unknown result
- **THEN** the receipt preserves that status, the system does not automatically redispatch that day's generation or call the previous report fresh, and AIHOT may continue with an explicit Radar gap

### Requirement: Verified optional Radar ingestion
The system SHALL support an explicitly configured read-only new-term-radar report/export or documented interface as a supplementary technology discovery source. A verified producer version, actual output schema and location SHALL precede activation. The GitHub repository URL alone MUST NOT be treated as a live feed. No available output SHALL result in unconfigured/unavailable status, not fabricated successful ingestion. Installation, new credentials and paid services SHALL require separate authorization.

#### Scenario: Only repository is known
- **WHEN** no consumable Radar output is configured
- **THEN** Radar remains unconfigured and existing AIHOT discovery continues without fabricated Radar candidates

### Requirement: Explicit dual-source technology isolation
Technology discovery SHALL permit its existing AIHOT source and its explicitly activated Radar source through the same Persona-scoped allowed-source set. Lifestyle SHALL retain its existing source selection. Collection, event reuse, evaluation and final persistence SHALL all enforce this boundary. Existing subscriptions MUST NOT all become enabled as a side effect.

#### Scenario: Technology supplement
- **WHEN** both technology sources have eligible evidence
- **THEN** both may supply technology candidates and neither supplies lifestyle candidates through this integration

### Requirement: Stable lineage and original evidence
Radar items SHALL preserve producer/version, stable item identity, original URL, observed/discovered timestamps, verified publication/event timestamps or null, signal kind and input hash through existing source/item versions. Reimport SHALL be idempotent. Repeated report reads MUST NOT reset discovery time. Signals SHALL remain leads until original body and supporting quotes are verified. Imported metadata MUST NOT override evidence quality, processing permissions or URL safety.

#### Scenario: Duplicate aggregator discovery
- **WHEN** Radar and AIHOT discover the same original project or event and equivalent angle
- **THEN** one candidate retains both discovery paths and counts the original publisher only once as an independent source

#### Scenario: No original body
- **WHEN** a Radar item provides only a headline, score or repository link without fetched supporting original content
- **THEN** it remains a lead and cannot become an evidence-qualified opportunity

### Requirement: Shared budgets and truthful coverage
Radar SHALL reuse the existing scanner and daily workflow, with no second scheduler or automatic budget increase. Eligible source queues SHALL be interleaved deterministically before existing evidence limits. Source failures and budget-unexamined items SHALL be recorded separately from unsuitable candidates. Unknown external outcomes MUST NOT trigger blind retries.

#### Scenario: Radar outage
- **WHEN** Radar fails while AIHOT provides usable evidence
- **THEN** valid AIHOT opportunities remain usable and the run shows partial Radar coverage without claiming complete evaluation
