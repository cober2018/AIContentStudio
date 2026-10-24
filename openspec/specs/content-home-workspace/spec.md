# content-home-workspace Specification

## Purpose
Define the daily Home workspace as an owner-scoped read projection of authoritative opportunities, project progress, review and delivery decisions, identity readiness, and project activity. Preserve unknown/error semantics and route loading boundaries without creating duplicate task state or inventing publication schedules.
## Requirements
### Requirement: Home is a projection of authoritative business state

The system SHALL expose an owner-scoped Home read model composed from persisted ContentOpportunity records, ContentProject and Project Overview, ProjectEvent, Review projection, Delivery reconciliation, and identity-readiness facts. Home MUST NOT introduce HomeTask, DashboardState, TodayStatus, or another duplicate workflow state table.

#### Scenario: Load Home
- **WHEN** an owner opens `/home`
- **THEN** the system returns typed sections for opportunities, pending decisions, active projects, blocked/stale/unknown risks, and recent project activity with links to authoritative pages

#### Scenario: Respect ownership
- **WHEN** a user loads Home
- **THEN** no opportunity, project, review, delivery, identity, or event belonging to another owner appears in any section

### Requirement: Pending work uses existing state semantics

Home SHALL derive “待我处理” from existing typed facts including waiting_human/waiting_input, pending Content Approval, pending Delivery Authorization, unresolved unknown reconciliation, identity_unready, blocked, and stale. Its decision ordering MUST be unknown/reconciliation > blocker > stale > waiting human > approval pending > delivery authorization pending > identity readiness, with stable entity IDs breaking ties. Duplicate cards for the same code and entity reference SHALL be collapsed. Unknown and stale MUST NOT be flattened into success.

#### Scenario: Show human action
- **WHEN** an owned project has a workflow or unit waiting for human input
- **THEN** Home shows a pending card linking to the existing production action and labels it as human input

#### Scenario: Show review and delivery decisions
- **WHEN** an owned project has a current candidate awaiting approval, authorization, or unknown reconciliation
- **THEN** Home shows the corresponding decision card linking to `/review` and does not claim approval or delivery completion

#### Scenario: Show identity and production risks
- **WHEN** an active unit has `identity_unready`, blocked, or stale state
- **THEN** Home shows distinct risk cards and links to the existing project/matrix or production resolution path

#### Scenario: Decision precedence and deduplication
- **WHEN** the same entity yields multiple pending facts, including an unresolved unknown delivery result
- **THEN** Home orders unknown first and shows at most one card per stable code and entity reference without hiding distinct issues

Home MAY additionally surface LearningCandidate validation when a candidate is `ready_for_review`. Learning remains the authoritative source and Home MUST NOT create a duplicate learning task/state. Operational production/review risks retain higher precedence than learning validation.

#### Scenario: Learning validation pending
- **WHEN** an owned LearningCandidate is ready_for_review
- **THEN** Home shows a pending decision linking to `/learning` without changing candidate status

### Requirement: Active project and opportunity summaries

Home SHALL show active owned projects using their existing Overview stage, counts, next action, and updated time. Today's opportunities SHALL include actionable `new`, `watching`, and `qualified` items that are not expired, ordered by priority high > normal > low, then time sensitivity high > medium > low > timeless, then `relevant_until` ascending and `updated_at` descending, with stable ID tie-breaking. Expired opportunities remain visible in the Opportunity workspace but SHALL NOT be promoted into Today merely by editing them. Until a scheduling contract exists, Home MUST return `upcoming=[]` and `capabilities.schedule=false`; recent activity MUST NOT be labeled as planned publication.

#### Scenario: Show active project
- **WHEN** an owner has an active ContentProject
- **THEN** Home shows its deterministic Overview stage and next action with a link to the project tab that owns the action

#### Scenario: Show opportunity without side effect
- **WHEN** an owner has an opportunity eligible for triage
- **THEN** Home shows the opportunity summary and opens the opportunity workspace; merely opening Home does not change opportunity status or create a project

#### Scenario: Deterministic Today ordering
- **WHEN** actionable opportunities differ in priority, time sensitivity, expiry, or recency
- **THEN** Today uses the declared ordering, excludes converted/dismissed/archived/expired items, and does not use a hidden model rank

### Requirement: Home route preserves FE-P1 loading boundaries

The Home implementation SHALL load on its own route boundary and MUST NOT statically import ProductionDesigner, TipTap, XYFlow, or unrelated legacy pages. Its API response SHALL be bounded and SHALL not load full project histories for the initial view.

#### Scenario: Open Home directly
- **WHEN** a user opens or refreshes `/home`
- **THEN** the Home shell loads its projection and unrelated heavy editor modules are not part of the Home initial graph

#### Scenario: Core Home projection fails
- **WHEN** Opportunity, Project Overview, or FE-F4 review/delivery projection fails
- **THEN** Home returns an explicit request/section error, or a response with `incomplete=true` and `section_errors` identifying the missing section; the missing section MUST NOT be rendered as an empty success state

#### Scenario: Optional capability unavailable
- **WHEN** an optional non-core capability is unavailable but core projections succeed
- **THEN** Home MAY show available core sections with explicit capability-unavailable metadata, without inventing missing facts

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
