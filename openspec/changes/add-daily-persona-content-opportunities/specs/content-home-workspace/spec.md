## ADDED Requirements

### Requirement: Daily discovery status remains a read projection

Home SHALL read generated opportunities from ContentOpportunity and per-Persona discovery status from persisted research runs. It SHALL show role labels and provide role filtering/grouping while retaining the existing deterministic opportunity ordering inside each group. Home reads MUST NOT enqueue collection, call models or create duplicate task state. Bounded status SHALL include last result, next due time, generated count and reason for zero/partial/unavailable outcomes. Failed reads MUST be rendered as unknown/error, not an empty successful queue.

#### Scenario: Two Persona batches complete
- **WHEN** the owner opens Home after the scheduled worker has saved role-specific opportunities
- **THEN** eligible unexpired opportunities appear with role labels and links to their original assessments and signals without new generation calls

#### Scenario: Discovery blocked
- **WHEN** a Persona has a blocked search/model run
- **THEN** Home shows the recorded reason and links to the normal run/settings view rather than only showing no content opportunities

### Requirement: Discovery schedule is distinct from publication schedule

Home SHALL expose a separate daily_discovery capability and discovery_status metadata. The existing schedule capability and upcoming list SHALL continue to describe publication scheduling and MUST NOT be enabled solely because daily opportunity discovery exists. The old optional single-opportunity analysis capability SHALL remain separately reported; an unavailable manual analyzer MUST NOT cause the page to describe a working daily-discovery pipeline as wholly unavailable.

#### Scenario: Daily discovery is ready while publication scheduling is absent
- **WHEN** daily discovery runs successfully but content publication scheduling is not implemented
- **THEN** Home exposes daily_discovery=true with discovery status while schedule=false and upcoming=[] remain unchanged
