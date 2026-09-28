## MODIFIED Requirements

### Requirement: Product shell

`/home` and `/opportunities` SHALL be real persistent workspaces. Opportunity detail SHALL be addressable at `/opportunities/:id`.

#### Scenario: Open Home
- **WHEN** the user opens `/home`
- **THEN** backend Opportunity/Project/decision projections load with truthful loading/error/empty states

#### Scenario: Open Opportunities
- **WHEN** the user opens `/opportunities`
- **THEN** persisted Opportunity state loads without browser fixture substitution

### Requirement: Project workspace

A ContentProject SHALL expose origin Opportunity provenance when created by conversion. Existing Projects without Opportunity origin SHALL remain valid.

#### Scenario: Converted project
- **WHEN** a converted Project is opened
- **THEN** Project can navigate back to its origin Opportunity without copying Opportunity state into Project
