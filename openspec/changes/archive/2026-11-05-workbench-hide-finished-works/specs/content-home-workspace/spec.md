## ADDED Requirements

### Requirement: Finished and dropped works leave the pending list

The workbench pending list SHALL leave out every item of a work whose 成片 has been approved, whatever its source (edit tasks, master checks or the older review flow). For a video work still in progress it SHALL list only the work's current edit task, not edit tasks replaced by a later one. Archived works SHALL stay out of the list as before.

#### Scenario: Approved film
- **WHEN** a work's 成片 was approved while older edit tasks of it are still result_ready and its master check reports incomplete
- **THEN** the pending list shows nothing for that work

#### Scenario: Replaced 小样
- **WHEN** a video work in progress has task 44 result_ready and a newer current task 45
- **THEN** the pending list shows task 45 only

#### Scenario: Dropped work
- **WHEN** the user archives a work they no longer make
- **THEN** none of its items appear in the pending list and its content stays viewable
