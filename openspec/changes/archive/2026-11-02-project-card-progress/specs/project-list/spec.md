## ADDED Requirements

### Requirement: Project cards show real progress

The project list SHALL return, per project, a progress summary of its active works from their video or article chain states, grouped into finished, waiting for the user, in progress and not started. Project cards SHALL show 「已完成」 when every work is finished, 「N 条等你看」 when any work waits for the user, otherwise 「制作中」, or 「未开始」 when none has started, plus a one-line breakdown; archived projects SHALL still show 「已归档」. The unused 「草稿」 label SHALL no longer appear.

#### Scenario: Mixed project
- **WHEN** a project has one finished video and one video whose 成片 waits for review
- **THEN** its card shows 「1 条等你看」 and the breakdown 「1 已定稿 · 1 成片待你看」
