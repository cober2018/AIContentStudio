## ADDED Requirements

### Requirement: Content opportunities page shows source health

The content opportunities page SHALL show one row per source with its state, last successful fetch, next scheduled fetch or the reason it is not scheduled, new items per day for the last 7 days, and the time of its latest new item. The view SHALL be read-only and SHALL NOT start any collection.

#### Scenario: Source not scheduled
- **WHEN** an active source has no persona that would use it
- **THEN** its row shows 「未被安排」 with the reason instead of a next fetch time

#### Scenario: Upstream stopped updating
- **WHEN** a source succeeded every poll but collected no new items for 5 days
- **THEN** its 7-day counts show zeros for those days and the latest new item time is 5 days ago
