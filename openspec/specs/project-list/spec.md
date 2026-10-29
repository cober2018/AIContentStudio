# project-list Specification

## Purpose
TBD - created by archiving change projects-default-active. Update Purpose after archive.
## Requirements
### Requirement: Project list shows active projects by default

The content project list SHALL show only projects that are not archived when no status filter is chosen. The user SHALL still be able to show all projects or only archived ones.

#### Scenario: Open the list
- **WHEN** the user opens 内容项目 without choosing a status
- **THEN** archived projects are not listed and the status filter shows 进行中

#### Scenario: Show everything
- **WHEN** the user chooses 全部状态
- **THEN** archived projects are listed too, and the choice survives a page refresh

