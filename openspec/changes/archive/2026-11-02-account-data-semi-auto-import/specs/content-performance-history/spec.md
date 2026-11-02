## ADDED Requirements

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
