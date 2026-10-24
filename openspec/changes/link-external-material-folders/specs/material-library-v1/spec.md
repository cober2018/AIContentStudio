## ADDED Requirements

### Requirement: Materials can be linked in place from user folders

The platform SHALL let a user register a folder, such as one on an external drive, as a material source, scan its media files, and link chosen files as Material revisions without copying their bytes. Each linked file SHALL carry the same kind, source, attribution and rights fields as an upload, and SHALL record its fingerprint, size and modified time. The platform MUST NOT write to, move or delete files in a source folder.

#### Scenario: Link footage from an external drive
- **WHEN** the user registers `/Volumes/Drive/素材`, scans it and links one video with rights set
- **THEN** a Material revision exists whose bytes remain on the drive, and no copy appears in the platform media folder

#### Scenario: Path escape
- **WHEN** a link request names a path outside the registered folder, including through `..` or a symbolic link
- **THEN** the request is rejected

### Requirement: Linked materials are verified on use

Every use of a linked file SHALL check that its source folder is present on the recorded volume and that the file is unchanged. A missing folder or file SHALL report `material_external_unavailable`; a changed file SHALL report `material_external_changed`. Work that needs the file MUST be blocked with that reason, never served other bytes. Linking a changed file again SHALL create a new revision of the same material with the previous revision as parent.

#### Scenario: Drive unplugged
- **WHEN** the drive holding a linked file is not mounted
- **THEN** the material shows as unavailable and stages or executions that need it are blocked until it returns

#### Scenario: File edited on the drive
- **WHEN** a linked file's bytes no longer match its recorded fingerprint
- **THEN** use is blocked as changed until the user links the new version as a new revision

### Requirement: Edit executions link external inputs

For linked materials, execution input materialization SHALL place a symbolic link to the drive file in the execution `inputs/` folder instead of a clone or copy, and SHALL re-verify the fingerprint at materialization and before an output is submitted.

#### Scenario: Linked footage in an edit
- **WHEN** an edit execution materializes a linked video
- **THEN** its input is a symbolic link to the drive file, no bytes are duplicated, and a later change to the file blocks output submission
