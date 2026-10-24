## ADDED Requirements

### Requirement: Mapped aggregate sources
The system SHALL map aitech.kayoyo.top to persona2 and wonderlife.kayoyo.top to persona3, verifying actual reads before activation.

#### Scenario: Role separation
- **WHEN** aggregate sources are activated
- **THEN** each role receives its mapped candidates and true connection status

### Requirement: Durable snapshot and changes
The system SHALL complete paginated selected snapshot before using its first-page watermark, apply each changes page before saving its cursor, and preserve edits and removals.

#### Scenario: Interrupted sync
- **WHEN** synchronization stops during a page
- **THEN** recovery does not skip uncommitted data or treat partial bootstrap as complete

#### Scenario: Snapshot required
- **WHEN** the server returns409 snapshot_required
- **THEN** the current selected set is reconciled by a new snapshot without erasing historical versions

### Requirement: Catchup before daily selection
The system SHALL sync with the existing scanner at default15-minute intervals and conclude catchup before freezing evidence for an unstarted daily run. It MUST retain real failures and gaps.

#### Scenario: Restart after shutdown
- **WHEN** a saved cursor is valid
- **THEN** offline changes are consumed before daily selection and any unconfirmed interval is visible

#### Scenario: Upstream unavailable
- **WHEN** a read fails or budget ends
- **THEN** the last successful boundary and partial reason are preserved, without claiming zero missing records

### Requirement: Original evidence and role quality
The system MUST preserve aggregate and original provenance, frozen body and precise quotes, distinguish publication/update/event dates, and continue existing dual evaluation, merging, actor maximum2 and daily maximum5 including zero. Upstream scores and summaries MUST NOT replace evidence verification.

#### Scenario: Nested aggregator or missing body
- **WHEN** an upstream link points to another aggregator or no verifiable body is available
- **THEN** trace original identity where available, do not count aggregation hops as independent actors, and reject evidence without body

#### Scenario: Old item imported
- **WHEN** an old selected item enters local storage
- **THEN** its new collection time does not establish a new hot event

### Requirement: Withdrawals preserve history
The system SHALL exclude withdrawn items from new selection, mark affected current opportunities for review, and retain existing frozen projects with source-change visibility.

#### Scenario: Removal arrives
- **WHEN** changes withdraw an item
- **THEN** future selection stops using it and historical work is preserved

### Requirement: Reversible source mode
The system SHALL switch only personas2 and3 after successful aggregate verification, pause their old source collection and automatic discovery through a reversible mode, and preserve manual settings.

#### Scenario: Rollback
- **WHEN** prior mode is restored
- **THEN** eligible old sources resume under preserved user settings while other roles remain unchanged
