## ADDED Requirements

### Requirement: Direct-search personas run their daily research
A persona without an aggregate source SHALL run its daily, bootstrap and weekly research using the configured search provider, and SHALL NOT fail because of how search availability is checked.

#### Scenario: Daily run for a direct-search persona
- **WHEN** the daily run starts for a direct-search persona with search configured
- **THEN** it searches and produces opportunities instead of failing with research_processing_failed

### Requirement: A data guard checks targets hourly and remedies misses
The system SHALL check every hour, against configurable targets (source freshness default 6 hours; daily research done by 12:00 Asia/Taipei, remedies until 22:00), whether each enabled source was collected and each persona's daily research finished. Misses SHALL be re-dispatched automatically within bounded attempts; a model call that failed before it could be sent SHALL be recorded as not dispatched and retried; a call possibly sent SHALL NOT be resent automatically.

#### Scenario: Model channel down at the daily hour
- **WHEN** the model address cannot be connected at 08:00 and comes back at 11:00
- **THEN** the run waits, is re-dispatched, and the day's opportunities are produced before 12:00

#### Scenario: Source overdue
- **WHEN** an enabled source has no successful collection for longer than its target
- **THEN** collection is re-dispatched, and after 3 consecutive failures the source is shown as needing attention with its reason

### Requirement: Guard problems are visible on the opportunities page
The opportunities page SHALL show a banner when any persona or source needs attention, naming it and the step it is stuck on in plain words, and SHALL offer a data guard panel listing each persona's and source's status today.

#### Scenario: Code error during research
- **WHEN** research fails with an unexpected error twice
- **THEN** the full error is in the worker log and the page shows 代码报错 for that persona

### Requirement: A dropped source does not block later research
When research reuses evidence from earlier opportunities, the system SHALL carry only discovery paths through sources the persona currently uses, so that removing a source from a persona never blocks that persona's later runs. Every blocked reason the guard shows SHALL have plain-language text.

#### Scenario: Old opportunity found through a removed source
- **WHEN** an earlier opportunity's article was found through two sources and one of them was later removed from the persona
- **THEN** today's run keeps the article via the remaining source and is not blocked with source_processing_revoked
