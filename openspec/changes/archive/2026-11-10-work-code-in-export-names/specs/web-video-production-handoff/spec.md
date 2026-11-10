## MODIFIED Requirements

### Requirement: Aspect ratio is visible in work titles and export file names
A video work's title SHALL be shown with its aspect ratio suffix taken from the current director draft, without changing the stored title. Export files SHALL be named `<short name>-<use>-<ratio>-作品N-任务M.<ext>`, with ratio from the file's pixel size and N the work's number, and the platform SHALL hand the edit task the exact names to use. Existing export files SHALL be renamed to this format with the platform's file records updated in the same step.

#### Scenario: Title
- **WHEN** the user opens work 97 anywhere its title is shown
- **THEN** the title reads 「决定AI量化生死的，其实是这4根数据支柱 · 16:9」

#### Scenario: New export
- **WHEN** an edit task M exports the 成片 and covers of landscape work N
- **THEN** the files are named …-成片-16x9-作品N-任务M.mp4, …-横封面-16x9-作品N-任务M.png, …-竖封面-3x4-作品N-任务M.png, …-横封面-4x3-作品N-任务M.png

#### Scenario: Two works in one project
- **WHEN** two works of the same project share a title and both export a 成片
- **THEN** their files differ by 作品N and sit side by side in the project's 导出/成片 folder

#### Scenario: Existing files
- **WHEN** the existing export files are renamed
- **THEN** each registered file still opens from its new place with the same content hash
