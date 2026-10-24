# dedupe-material-entries Specification

## Purpose
TBD - created by archiving change dedupe-material-entries. Update Purpose after archive.
## Requirements
### Requirement: One entry per file

The library SHALL hold at most one active material entry per file content. Duplicate entries SHALL be retired, not deleted, and everything that used them SHALL keep working.

#### Scenario: Project view
- **WHEN** the user opens 素材库 → 项目 → 海底光缆
- **THEN** each file appears once

#### Scenario: Rights differ
- **WHEN** two entries for the same file have conflicting rights
- **THEN** they are not merged and are listed for the user

### Requirement: Current draft uses the kept entry

When the latest draft uses a retired entry, a new draft version SHALL be saved that uses the kept entry, with nothing else changed.

#### Scenario: Ship used twice
- **WHEN** shots 9 and 11 used two entries of the same ship video
- **THEN** the new draft uses one entry for both shots

### Requirement: No new duplicates

Adding a file whose content is already in the library SHALL reuse the existing entry.

#### Scenario: Same file dropped again
- **WHEN** the user drops a file that is already in the library
- **THEN** no new entry is created and the existing one is used

### Requirement: Same-folder duplicate files removed

Within one folder of the library drive, only one copy of identical bytes SHALL remain.

#### Scenario: Two identical files in one folder
- **WHEN** a project folder holds two files with the same bytes
- **THEN** one is removed and the remaining one is the file the platform uses

