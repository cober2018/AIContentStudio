## ADDED Requirements

### Requirement: Task-first home hierarchy
Home SHALL prioritize pending decisions, continuing work and actionable opportunity summaries, with bounded previews and explicit access to complete records. Activity and identity details SHALL have their own addressable views. Duplicate project summaries SHALL not occupy multiple equal-weight sections on the default page.

#### Scenario: Open daily workspace
- **WHEN** an owner opens Home
- **THEN** authoritative decisions and next actions are visible first and existing project, opportunity and identity destinations remain reachable

### Requirement: Preserve projection uncertainty and current workflow links
The simplified Home SHALL retain unknown-first precedence, deduplication, current creative recipe routing, per-section errors and unavailable-data distinctions. It SHALL NOT infer automatic-analysis unavailability from a legacy capability flag when persisted assessments exist.

#### Scenario: Partial projection
- **WHEN** Home returns incomplete or section_errors
- **THEN** the error remains visible and absent sections are not displayed as successful empty queues

#### Scenario: Continue current work
- **WHEN** a current project has a newer recipe next action
- **THEN** the simplified page uses existing action precedence instead of opening an unrelated generic editor
