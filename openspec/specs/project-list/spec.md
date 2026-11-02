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

### Requirement: Project cards show real progress

The project list SHALL return, per project, a progress summary of its active works from their video or article chain states, grouped into finished, waiting for the user, in progress and not started. Project cards SHALL show 「已完成」 when every work is finished, 「N 条等你看」 when any work waits for the user, otherwise 「制作中」, or 「未开始」 when none has started, plus a one-line breakdown; archived projects SHALL still show 「已归档」. The unused 「草稿」 label SHALL no longer appear.

#### Scenario: Mixed project
- **WHEN** a project has one finished video and one video whose 成片 waits for review
- **THEN** its card shows 「1 条等你看」 and the breakdown 「1 已定稿 · 1 成片待你看」

