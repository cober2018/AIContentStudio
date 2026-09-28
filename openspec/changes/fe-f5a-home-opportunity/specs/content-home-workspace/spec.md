## ADDED Requirements

### Requirement: Home is a projection of authoritative business state

The system SHALL expose an owner-scoped Home read model composed from persisted ContentOpportunity records, ContentProject and Project Overview, ProjectEvent, Review projection, Delivery reconciliation, and identity-readiness facts. Home MUST NOT introduce HomeTask, DashboardState, TodayStatus, or another duplicate workflow state table.

#### Scenario: Load Home
- **WHEN** an owner opens `/home`
- **THEN** the system returns typed sections for opportunities, pending decisions, active projects, blocked/stale/unknown risks, and recent project activity with links to authoritative pages

#### Scenario: Respect ownership
- **WHEN** a user loads Home
- **THEN** no opportunity, project, review, delivery, identity, or event belonging to another owner appears in any section

### Requirement: Pending work uses existing state semantics

Home SHALL derive “待我处理” from existing typed facts including waiting_human/waiting_input, pending Content Approval, pending Delivery Authorization, unresolved unknown reconciliation, identity_unready, blocked, and stale. It MUST preserve priority between blocker, human input, review, authorization, and reconciliation without flattening unknown or stale into success.

#### Scenario: Show human action
- **WHEN** an owned project has a workflow or unit waiting for human input
- **THEN** Home shows a pending card linking to the existing production action and labels it as human input

#### Scenario: Show review and delivery decisions
- **WHEN** an owned project has a current candidate awaiting approval, authorization, or unknown reconciliation
- **THEN** Home shows the corresponding decision card linking to `/review` and does not claim approval or delivery completion

#### Scenario: Show identity and production risks
- **WHEN** an active unit has `identity_unready`, blocked, or stale state
- **THEN** Home shows distinct risk cards and links to the existing project/matrix or production resolution path

### Requirement: Active project and opportunity summaries

Home SHALL show active owned projects using their existing Overview stage, counts, next action, and updated time. It SHALL show qualified/new opportunities from the opportunity workspace without converting or mutating them. Until a scheduling contract exists, “近期计划” MUST be represented only by recent project activity/updated projects and MUST NOT be fabricated from timestamps as a plan.

#### Scenario: Show active project
- **WHEN** an owner has an active ContentProject
- **THEN** Home shows its deterministic Overview stage and next action with a link to the project tab that owns the action

#### Scenario: Show opportunity without side effect
- **WHEN** an owner has an opportunity eligible for triage
- **THEN** Home shows the opportunity summary and opens the opportunity workspace; merely opening Home does not change opportunity status or create a project

### Requirement: Home route preserves FE-P1 loading boundaries

The Home implementation SHALL load on its own route boundary and MUST NOT statically import ProductionDesigner, TipTap, XYFlow, or unrelated legacy pages. Its API response SHALL be bounded and SHALL not load full project histories for the initial view.

#### Scenario: Open Home directly
- **WHEN** a user opens or refreshes `/home`
- **THEN** the Home shell loads its projection and unrelated heavy editor modules are not part of the Home initial graph

#### Scenario: Home projection is partially unavailable
- **WHEN** one projection source is temporarily unavailable
- **THEN** Home displays a typed partial-data warning and preserves available sections without inventing missing success states
