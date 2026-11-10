## ADDED Requirements

### Requirement: Approving a video stop survives a briefly busy database
When the user approves a 小样 or 成片 (or sends notes) and the database is briefly busy with another writer, the platform SHALL retry the decision for up to about 30 seconds instead of failing at the first lock timeout. If it still cannot be written, the platform SHALL clear the 正在通过 marker and return a plain message asking the user to click again. The page SHALL show that message next to the button and SHALL make the button clickable again; it SHALL NOT stay on 正在通过….

#### Scenario: Another task holds the database for a few seconds
- **WHEN** the user clicks 成片通过 while a background job is writing for 10 seconds
- **THEN** the approval waits, goes through, and the work shows 已定稿

#### Scenario: The database stays busy
- **WHEN** the database stays busy past the retry window
- **THEN** the page shows 「数据库正忙，这次没通过，请再点一次」, the button is clickable, and the work is still 成片待你看

### Requirement: Background jobs do not hold the write lock for long
Background jobs SHALL commit their database writes in short steps and SHALL NOT keep a write transaction open across slow work (network calls, model calls, file hashing). A lock wait that times out SHALL be logged with the waiting operation. The maintenance sweep SHALL skip a cycle when the database is busy instead of logging a failure.

#### Scenario: Search promotion resumes after a restart
- **WHEN** two search-promotion projects resume right after the API restarts
- **THEN** the user's approval and the maintenance sweep still get to write within a few seconds
