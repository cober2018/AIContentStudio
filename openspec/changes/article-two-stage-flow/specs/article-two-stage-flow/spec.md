## ADDED Requirements

### Requirement: Article workflow has two AI stages

New article workflows SHALL have the stages 写作方案 and 成稿, followed by an automatic 质量检查. Existing runs SHALL keep their stages.

#### Scenario: New article
- **WHEN** a new article workflow is created from a starter definition
- **THEN** its stages are 写作方案, 成稿 and 质量检查

### Requirement: 写作方案 returns complete plans

写作方案 SHALL return two or three candidates. Each has an angle, the facts it uses (from the confirmed boundary), the unknowns it keeps open, and an outline. The user picks one.

#### Scenario: Pick a plan
- **WHEN** the user opens 写作方案 results
- **THEN** each candidate shows angle, facts, unknowns and outline, and accepting one makes it the input of 成稿

### Requirement: 成稿 returns the full article once

成稿 SHALL return the complete article: title, opening and body in one answer, with up to two alternative titles. It follows the chosen plan and the fact rules. The user confirms it once.

#### Scenario: Confirm the article
- **WHEN** the user accepts a 成稿 candidate
- **THEN** it becomes the article master, and no further writing stage is required

### Requirement: Quality check runs by itself

After 成稿 is accepted, the quality check SHALL run without a user action. It SHALL ask the user to act only when a check fails.

#### Scenario: Checks pass
- **WHEN** all checks pass
- **THEN** the step shows as done and the user can go on to channel versions

#### Scenario: Check fails
- **WHEN** a check fails
- **THEN** the step shows 需要处理 with the failed checks
