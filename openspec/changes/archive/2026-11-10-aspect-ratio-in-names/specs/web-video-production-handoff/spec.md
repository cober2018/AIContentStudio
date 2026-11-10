## ADDED Requirements

### Requirement: Aspect ratio is visible in work titles and export file names
A video work's title SHALL be shown with its aspect ratio suffix taken from the current director draft, without changing the stored title. Export files SHALL be named `<short name>-<use>-<ratio>-任务N.<ext>`, with ratio from the file's pixel size, and the platform SHALL hand the edit task the exact names to use. Existing export files SHALL be renamed to this format with the platform's file records updated in the same step.

#### Scenario: Title
- **WHEN** the user opens work 97 anywhere its title is shown
- **THEN** the title reads 「决定AI量化生死的，其实是这4根数据支柱 · 16:9」

#### Scenario: New export
- **WHEN** an edit task exports the 成片 and covers of a landscape work
- **THEN** the files are named …-成片-16x9-任务N.mp4, …-横封面-16x9-任务N.png, …-竖封面-3x4-任务N.png, …-横封面-4x3-任务N.png

#### Scenario: Existing files
- **WHEN** the existing export files are renamed
- **THEN** each registered file still opens from its new place with the same content hash
