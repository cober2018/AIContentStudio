## MODIFIED Requirements

### Requirement: Project and production load isolation
The `/projects` list, persistent project detail, and unit production page SHALL be distinct runtime load boundaries. The project list MUST NOT statically import project detail tabs or `ProductionDesigner`; the project detail MUST NOT statically import the production designer. TipTap and XYFlow MUST NOT be part of the initial JavaScript graph for `/projects` or another route that does not use them.

#### Scenario: Enter project detail
- **WHEN** a user enters `/projects/:projectId` from the project list
- **THEN** project-detail code loads and the existing tabs and actions remain available without loading the production designer

#### Scenario: Enter production
- **WHEN** a user enters `/projects/:projectId/units/:unitId/production`
- **THEN** the production designer loads on demand and retains its existing run, save, and error behavior

The `/projects` list, persistent project detail and unit Production page SHALL remain distinct runtime load boundaries. The common Production shell SHALL NOT statically import TipTap or other professional Text-editor-only dependencies. F6B MAY load TipTap only through the lazy Text Studio modality boundary. Graphic and Video Studio dynamic closures SHALL not statically depend on the Text editor. Existing legacy `/workspace` may continue loading its own TipTap editor only when that route is requested.

#### Scenario: Open Graphic Production unit
- **WHEN** a Graphic ContentUnit enters Production after F6B
- **THEN** common Production and Graphic Studio load without requesting the Text Studio TipTap chunk

#### Scenario: Open Text Production unit
- **WHEN** a Text ContentUnit enters its professional Text Studio
- **THEN** Text-editor dependencies load on demand after the common Production boundary and all existing Production controls remain functional

### Requirement: Reproducible initial JavaScript budget
The frontend build SHALL emit a Vite manifest and a deterministic budget check. The check MUST traverse the static import closure for the entry and `/projects` route, deduplicate assets, report emitted raw and gzip JS bytes, and fail if that initial closure is at least 500,000 raw bytes or if its required manifest mapping is missing. Dynamic imports MUST NOT be counted as initial route dependencies. The check SHALL report total emitted JS separately and MUST NOT treat the disappearance of a Vite chunk warning as proof of initial-load improvement.

#### Scenario: Budget passes on a measured build
- **WHEN** a production build emits a manifest with the entry and `/projects` route chunk and their static imports are below 500,000 raw bytes
- **THEN** the check passes and prints raw, gzip, and total-generated JS sizes alongside the FE-F4 baseline

#### Scenario: Initial route budget regresses
- **WHEN** the initial `/projects` static closure reaches or exceeds 500,000 raw bytes, or its manifest mapping is unavailable
- **THEN** the check fails rather than hiding the regression or guessing at a route chunk

The existing deterministic route budget SHALL remain authoritative for entry and `/projects`. F6B acceptance SHALL additionally inspect the Vite manifest/import graph and record measured raw/gzip baselines for common Production and Text Studio. It SHALL fail acceptance if TipTap becomes a static dependency of the common Production shell, Graphic/Video Studio, `/projects`, `/assets`, `/settings` or `/learning`. No permanent Text-editor byte ceiling SHALL be invented before a measured implementation baseline is reviewed.

#### Scenario: Text editor remains isolated
- **WHEN** the F6B production build is inspected
- **THEN** TipTap appears only in Text/legacy-editor dynamic dependency closures, existing hard route budgets still pass, and the new measured Text Studio baseline is recorded
