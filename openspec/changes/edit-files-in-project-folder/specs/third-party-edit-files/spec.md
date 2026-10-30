## ADDED Requirements

### Requirement: Edit work stays in the project folder

A third-party edit task SHALL work inside its project folder: temporary files in `工作/<work>/任务<N>/`, the 小样 in `导出/小样`, the 成片 in `导出/成片`. The platform SHALL NOT create task folders inside its own program directory.

#### Scenario: Open an edit task
- **WHEN** a third-party model opens the 小样 task for 儿童麸质饼干
- **THEN** it receives the original paths of the shot materials, its work folder under `20261027_儿童麸质饼干/工作/` and the export folder `导出/小样`

### Requirement: Results are registered in place

A submitted result SHALL be checked and registered at the path the model gives, without copying. Paths outside the project folder, symbolic links, or files changed after submission SHALL be refused.

#### Scenario: Return a 小样
- **WHEN** the model exports `导出/小样/儿童麸质饼干-小样.mp4` and submits that path
- **THEN** the page shows 小样待你看 playing that same file, and no other copy exists

#### Scenario: Path outside the project
- **WHEN** the model submits a file under its own temporary directory
- **THEN** the platform refuses with a plain message naming the allowed folders

### Requirement: Optional proxy media

A setting SHALL turn proxy media on or off, off by default. When on, large video materials get a reusable low-resolution proxy in `工作/代理/`, and the task receives both paths.

### Requirement: Temporary files are cleaned

When a newer 小样 is returned, unregistered files of earlier tasks of that work SHALL be removed; when the 成片 is approved, the work's `工作/` keeps only that task's files. Originals and `导出/` are never removed by cleanup.
