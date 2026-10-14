# fe-f0-f1-project-experience Specification

## Purpose
Define the nine-workspace product shell and project experience, including persistent Content Units, identity selection, the real Identity Workspace, and a separate browser-only demo. Workflow execution and production persistence are governed by the corresponding FE-F2 and FE-F3B specifications.
## Requirements
### Requirement: Product shell
The frontend SHALL offer nine primary workspaces with navigable routes and loading, error, and empty views. Existing frontend pages SHALL remain reachable, using legacy aliases when a path is repurposed for a primary workspace. `/identities` SHALL load a persistent Content Identity workspace rather than a long-lived placeholder. `/review` SHALL load a persistent, project-first Review & Distribution workspace rather than a placeholder; `/review-publish` SHALL remain available for legacy Topic workflows.

#### Scenario: Browse primary navigation
- **WHEN** the user opens the application shell
- **THEN** nine primary workspaces are visible and each link resolves to a page or scoped placeholder

#### Scenario: Open identities
- **WHEN** the user opens `/identities`
- **THEN** the application loads backend Brand/Persona/Account/Series state and does not substitute browser fixture identity data

#### Scenario: Open project review
- **WHEN** the user opens `/review`
- **THEN** the workspace loads authorized ContentProjects and ContentUnits from backend state, not browser fixtures or a placeholder

`/home` and `/opportunities` SHALL be real persistent workspaces. Opportunity detail SHALL be addressable at `/opportunities/:id`.

#### Scenario: Open Home
- **WHEN** the user opens `/home`
- **THEN** backend Opportunity/Project/decision projections load with truthful loading/error/empty states

#### Scenario: Open Opportunities
- **WHEN** the user opens `/opportunities`
- **THEN** persisted Opportunity state loads without browser fixture substitution

`/learning` SHALL be a real persistent workspace rather than a placeholder and SHALL preserve FE-P1 lazy route boundaries.

#### Scenario: Open Learning
- **WHEN** the user opens `/learning`
- **THEN** Historical Recovery, Long-term Analysis, Learning Candidates and Content Memory views load from backend state without browser fixture substitution

`/assets` SHALL be a real persistent System Assets & Knowledge workspace rather than a placeholder. `/settings` SHALL remain a primary workspace and SHALL expose the product-oriented Settings sections while preserving existing configuration behavior.

#### Scenario: Open Assets
- **WHEN** the user opens `/assets`
- **THEN** backend system-library data loads with truthful loading/error/empty states

#### Scenario: Open Settings
- **WHEN** the user opens `/settings`
- **THEN** Models, Data Sources, Channels, Rules, Team and Advanced sections load from real backend state

### Requirement: Project workspace

The frontend SHALL present ContentProject as the business root and provide overview, brief, evidence, assets, matrix, versions, and activity tabs with URL-addressable tab state. For persisted projects, all seven tabs SHALL load real backend state; Brief, Evidence, Versions, and Activity MUST NOT remain persistent placeholder panels.

#### Scenario: Open a persisted project tab
- **WHEN** the user opens any of the seven tabs for a backend-persisted ContentProject
- **THEN** the tab loads the corresponding real project data or a truthful empty state from the backend and can be opened directly by URL

#### Scenario: Reload project tab
- **WHEN** the user reloads a project URL on Brief, Evidence, Assets, Matrix, Versions or Activity
- **THEN** saved project state remains visible without depending on browser-only fixture data

A ContentProject SHALL expose origin Opportunity provenance when created by conversion. Existing Projects without Opportunity origin SHALL remain valid.

#### Scenario: Converted project
- **WHEN** a converted Project is opened
- **THEN** Project can navigate back to its origin Opportunity without copying Opportunity state into Project

### Requirement: Content matrix editing
The frontend SHALL let the user add, edit, and delete Content Units through the backend project API. A Content Unit MUST show stable content Persona/Role identity, optional Account/Series, modality, channel, pinned workflow reference, IdentitySnapshot state, and status. On creation, the user SHALL be able to select the effective Persona/Account/Series × Modality default Workflow Template Version or an explicit project override. Browser-only FE-F0-F1 fixture data MUST remain clearly separate from real persisted projects and MUST NOT be imported without an explicit action.

#### Scenario: Edit a unit
- **WHEN** the user changes a unit's identity, modality, channel, workflow, or title and saves
- **THEN** the matrix displays the new values without changing unrelated units, and the values remain after reload

#### Scenario: Edit before execution history
- **WHEN** a unit has no Run, DataSnapshot, or generated output, even if it has a saved project workflow override, and the user explicitly rebinds identity, modality, or workflow
- **THEN** the unit MAY be edited in place; an incompatible old override is detached and the selected or current hierarchical default is pinned explicitly with a new IdentitySnapshot

#### Scenario: Replace after execution history
- **WHEN** a unit with Run, DataSnapshot, or generated output explicitly rebinds identity, modality, or workflow
- **THEN** a new unit receives the selected identity, IdentitySnapshot and workflow, the old unit is archived, and its runs and outputs remain readable under the old ID but cannot be mutated or re-executed

#### Scenario: Delete a unit
- **WHEN** the user deletes a unit without execution history
- **THEN** the unit is physically removed, including a saved override binding if present
- **WHEN** the unit has execution history
- **THEN** it is archived from the active matrix without deleting its history

#### Scenario: Browser demo data exists
- **WHEN** local FE-F0-F1 demo data exists and the user opens the real project list
- **THEN** no local item is silently written to or substituted for a backend project

#### Scenario: Choose identity default for a new unit
- **WHEN** the user creates a Content Unit with a Persona, optional Account/Series, and modality that have an effective current default Workflow Template Version
- **THEN** that version and its source scope are offered for selection and the saved unit pins the selected version without changing existing units

#### Scenario: Legacy unit
- **WHEN** an older unit has no IdentitySnapshot
- **THEN** the matrix and production entry mark identity as legacy/unknown until explicit rebind

### Requirement: Project assets

The frontend SHALL expose Project Shared Assets through a modal or drawer instead of permanently occupying the Production canvas. For persisted projects, the same project asset pool SHALL include explicit project uploads, system MaterialRevision references, and verified workflow-generated material revisions with source/provenance/rights distinctions.

#### Scenario: Open unified shared assets
- **WHEN** the user opens Project Shared Assets from a persisted project or Production Workspace
- **THEN** one dismissible asset browser shows project-upload, system-reference and workflow-generated items from backend state without duplicating the underlying material bytes

### Requirement: Production entry and status semantics
The frontend SHALL navigate from a selected Content Unit to a project-scoped Production Workspace shell. Blocked, stale, unknown, ready, and waiting_human MUST have distinct labels and visual treatments. Blocked, stale, and unknown in Production and Review SHALL derive from the same persisted facts. An unknown delivery result MUST show reconciliation-needed and MUST NOT appear as success or offer generic retry.

#### Scenario: Abnormal project
- **WHEN** the user opens the abnormal fixture
- **THEN** blocked, stale, and unknown units are visibly distinguishable and their meanings are explained

#### Scenario: Unknown delivery in review
- **WHEN** the selected unit has an unresolved unknown DeliveryAttempt
- **THEN** the Review workspace shows reconciliation-needed without a generic retry action

### Requirement: Daily Persona → Series → content → targets journey

The primary product journey SHALL let users begin from a Persona and editorial Series, enter the existing Project/Creation Recipe creation chain without requiring a destination Account, and later select one or more explicit channel Accounts for Variant review and handoff.

#### Scenario: Technology creator multi-target end-to-end
- **WHEN** the AI technology Persona creates an article Master in a Persona-owned Series
- **AND** selects valid WeChat, Zhihu and Xiaohongshu target Accounts
- **THEN** the product can prepare separate platform forms, validate them, obtain review and create the corresponding independently traced handoff/authorized draft outcomes

#### Scenario: Lifestyle Persona is isolated
- **WHEN** the lifestyle Persona creates another Unit with its own editorial Series
- **THEN** its skills/styles/voice/target selections are derived from that Persona's explicit configuration
- **AND** no configuration from the technology Persona is implicitly inherited

### Requirement: Creation Recipe is the normal Production control surface

A user continuing a Project SHALL be able to understand and control the next creation stage without opening raw workflow JSON/canvas. Production SHALL expose the effective recipe, next actionable stage, current content/result and blockers, while Advanced mode preserves full graph editing.

#### Scenario: Continue active Project
- **WHEN** Home/Project opens a unit with an incomplete recipe
- **THEN** the user can jump to the exact next actionable stage and inspect/tune it

### Requirement: Stage tuning has explicit save scopes

The UI SHALL distinguish:
- this run only;
- save to this Project recipe;
- save as scoped default;
- save as reusable method.

It MUST explain which future work will be affected before the user confirms.

#### Scenario: Temporary experiment
- **WHEN** the user selects “仅本次”
- **THEN** no Workflow/Capability/default revision is created even if the result is later accepted

### Requirement: A selected Persona makes Production immediately actionable

When a Project/Unit uses a starter or configured Persona, Production SHALL show its effective default Creation Recipe, creative readiness and next actionable stage without requiring the user to author a Workflow, Skill or Prompt first.

#### Scenario: Start a Text Unit from starter Persona
- **WHEN** the user creates a Text Unit with one of the two starter Personas and required provider capability is ready
- **THEN** the default Persona recipe is runnable immediately in normal Production mode

### Requirement: Creative configuration scope is understandable

The UI SHALL distinguish Persona default, Account override, Series override, Project Workflow configuration and one-run override. Saving a current result/method SHALL clearly state which future content will be affected.

#### Scenario: Save a working adjustment to Project scope
- **WHEN** the user saves a successful one-run adjustment into the current Project Workflow
- **THEN** the UI identifies Project scope and the affected future content rather than presenting it as a Persona-wide default
