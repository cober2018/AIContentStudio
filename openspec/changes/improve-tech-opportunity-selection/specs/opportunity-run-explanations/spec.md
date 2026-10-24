## ADDED Requirements

### Requirement: Persist factual stage diagnostics
Research runs SHALL retain versioned diagnostics for collected items, successful and failed body reads, budget-unexamined items, proposed candidates, pre-score rejection, scored candidates, score rejection, deduplication/source-cap exclusion and persisted opportunities. Each stage SHALL declare its count unit and assign at most one primary exit reason per candidate at that stage. Missing historical statistics SHALL be null/unrecorded, not invented zeros. No raw provider secrets or response dumps SHALL be exposed.

#### Scenario: Rejected before scoring
- **WHEN** three generated candidates fail pre-score evidence checks
- **THEN** the UI says scoring was not reached and shows recorded evidence reasons rather than asserting low model scores

### Requirement: Explain empty and partial outcomes
The page SHALL distinguish not yet scheduled/executed, running/waiting collection, blocked/failed/unknown, completed with no qualifying candidates and empty due to filters. It SHALL show actual run business date, last result and next scheduled time for the selected Persona. Source failures SHALL coexist with valid results. Historical rows without detailed reasons SHALL show unrecorded details. Read failures MUST NOT render as successful empty results.

#### Scenario: New day before batch
- **WHEN** today's batch has not run but yesterday has a zero result
- **THEN** the page shows today's pending state and labels yesterday's result with its real date

#### Scenario: Filter hides stored opportunities
- **WHEN** a date or status filter hides existing records
- **THEN** the page explains the active filter and offers history/filter adjustment without asserting discovery failure

### Requirement: Read-only explanations
Viewing, refreshing or opening run details SHALL only read persisted records and MUST NOT dispatch collection, models, retries or mutate opportunities. Explanations SHALL link to recorded run/source details with bounded safe error information.

#### Scenario: User refreshes empty list
- **WHEN** the user refreshes a zero-result view
- **THEN** no new external request is dispatched by that page action
