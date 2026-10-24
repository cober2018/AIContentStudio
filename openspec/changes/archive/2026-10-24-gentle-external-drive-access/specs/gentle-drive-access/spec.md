## ADDED Requirements

### Requirement: Drive presence is checked without writing

The platform SHALL detect whether the external library is usable with read-only checks. It SHALL write a probe file only immediately before an operation that writes to the drive.

#### Scenario: Page open for an hour
- **WHEN** the production page stays open and polls
- **THEN** no file is created or deleted on the drive

#### Scenario: Half-dropped drive
- **WHEN** the drive is mounted but its folders list as empty
- **THEN** the platform reports 「素材库未连接」

### Requirement: Each file is fully verified once

After a material file has been fully read and its hash matched, the platform SHALL record its path, size and modified time, and later saves and readiness checks SHALL NOT read the whole file again while those stay the same.

#### Scenario: Saving the master again
- **WHEN** a master referencing 20 verified files is saved
- **THEN** only the first bytes of each file are read

#### Scenario: File replaced
- **WHEN** a referenced file's size or modified time changes
- **THEN** it is fully read and verified again

### Requirement: Edit inputs are copied from the drive once

An edit task SHALL reuse an identical input already copied to the Mac by an earlier task of the same user instead of copying it from the drive again.

#### Scenario: Second edit task
- **WHEN** the 成片 task starts after the 小样 task used the same materials
- **THEN** its inputs are cloned from the Mac copies and the drive is not read
