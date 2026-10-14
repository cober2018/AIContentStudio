# fe-p1-frontend-bundle-performance Specification

## Purpose
Define the durable frontend route-loading, project/production isolation, recoverable failure, and measured initial-JavaScript budget contracts introduced by FE-P1 without changing product business behavior.
## Requirements
### Requirement: Route-scoped frontend loading
The frontend SHALL load page-specific JavaScript only when its route is entered. All existing primary and legacy routes, redirects, and demo fallbacks MUST retain their prior navigation and business behavior.

#### Scenario: Open project list directly
- **WHEN** a user opens or refreshes `/projects`
- **THEN** the application displays the persistent project list without requesting unrelated legacy page modules or the production designer

#### Scenario: Navigate to a legacy page
- **WHEN** a user navigates from `/projects` to `/workspace` or `/workflows`
- **THEN** the requested legacy page loads on demand and remains functional at its existing URL

#### Scenario: Preserve project route fallback
- **WHEN** a user opens a numeric project or production URL, or a supported nonnumeric demo project URL
- **THEN** the same persistent or demo page selection occurs as before the change

### Requirement: Project and production load isolation
The `/projects` list, persistent project detail, and unit production page SHALL be distinct runtime load boundaries. The project list MUST NOT statically import project detail tabs or `ProductionDesigner`; the project detail MUST NOT statically import the production designer. TipTap and XYFlow MUST NOT be part of the initial JavaScript graph for `/projects` or another route that does not use them.

#### Scenario: Enter project detail
- **WHEN** a user enters `/projects/:projectId` from the project list
- **THEN** project-detail code loads and the existing tabs and actions remain available without loading the production designer

#### Scenario: Enter production
- **WHEN** a user enters `/projects/:projectId/units/:unitId/production`
- **THEN** the production designer loads on demand and retains its existing run, save, and error behavior

### Requirement: Lazy route loading and failure states
Lazy routes SHALL show an accessible loading state while their code is fetched. A failed chunk load MUST show a recoverable error state with an explicit retry/reload action; it MUST NOT leave an empty page or permanently disable shell navigation.

#### Scenario: Page code is still loading
- **WHEN** navigation reaches a route whose JavaScript has not arrived
- **THEN** the route region announces loading while the navigation shell remains available

#### Scenario: Chunk request fails
- **WHEN** a lazy route chunk cannot be fetched
- **THEN** the user sees an error explanation and a way to retry or reload, and can navigate to another route

### Requirement: Reproducible initial JavaScript budget
The frontend build SHALL emit a Vite manifest and a deterministic budget check. The check MUST traverse the static import closure for the entry and `/projects` route, deduplicate assets, report emitted raw and gzip JS bytes, and fail if that initial closure is at least 500,000 raw bytes or if its required manifest mapping is missing. Dynamic imports MUST NOT be counted as initial route dependencies. The check SHALL report total emitted JS separately and MUST NOT treat the disappearance of a Vite chunk warning as proof of initial-load improvement.

#### Scenario: Budget passes on a measured build
- **WHEN** a production build emits a manifest with the entry and `/projects` route chunk and their static imports are below 500,000 raw bytes
- **THEN** the check passes and prints raw, gzip, and total-generated JS sizes alongside the FE-F4 baseline

#### Scenario: Initial route budget regresses
- **WHEN** the initial `/projects` static closure reaches or exceeds 500,000 raw bytes, or its manifest mapping is unavailable
- **THEN** the check fails rather than hiding the regression or guessing at a route chunk

### Requirement: Route behavior verification
The change SHALL be accepted only after a successful frontend type-check/build, bundle-budget check, and direct-navigation plus route-transition smoke verification of landing, project list/detail/production, review, identity, and heavy legacy routes. The verification MUST include refresh, numeric-versus-demo project fallback, loading, and chunk-failure recovery.

#### Scenario: Existing routes remain reachable
- **WHEN** the FE-P1 implementation is reviewed for acceptance
- **THEN** the verification record identifies each sampled direct URL and transition result, and any unverified browser behavior is reported as unverified rather than passed

### Requirement: Creation Recipe normal controls remain lightweight and advanced tooling stays lazy

The stage strip/control drawer and lightweight typed controls SHALL be available in normal Production without eagerly loading raw graph automation, TipTap, heavy Graphic/Video editors, Capability Memory management or professional-execution panels until opened.

#### Scenario: Open Production stage list
- **WHEN** the user views the recipe and a simple Text stage
- **THEN** Advanced canvas, heavy unrelated modality editors and professional execution UI remain outside the initial closure

#### Scenario: Open Advanced
- **WHEN** the user explicitly opens graph/mapping automation
- **THEN** the existing WorkflowMiniCanvas/NodeInspector bundle loads lazily without changing recipe state

### Requirement: Persona creative configuration remains progressively loaded

Identity summary and lightweight creative readiness MAY load with Identity Workspace, while full Skill references, composed-method pickers, Graphic contact sheets, Audio previews and Production editors SHALL load only when the relevant tab/stage opens. Unrelated routes MUST NOT eagerly import heavy production/media/editor modules.

#### Scenario: Open Identity list
- **WHEN** the user opens `/identities` without opening Creative Configuration
- **THEN** heavy Graphic/Audio/Production bundles are not part of the initial closure
