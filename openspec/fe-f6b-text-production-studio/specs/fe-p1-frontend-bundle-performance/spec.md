## MODIFIED Requirements

### Requirement: Project and production load isolation

The `/projects` list, persistent project detail and unit Production page SHALL remain distinct runtime load boundaries. The common Production shell SHALL NOT statically import TipTap or other professional Text-editor-only dependencies. F6B MAY load TipTap only through the lazy Text Studio modality boundary. Graphic and Video Studio dynamic closures SHALL not statically depend on the Text editor. Existing legacy `/workspace` may continue loading its own TipTap editor only when that route is requested.

#### Scenario: Open Graphic Production unit
- **WHEN** a Graphic ContentUnit enters Production after F6B
- **THEN** common Production and Graphic Studio load without requesting the Text Studio TipTap chunk

#### Scenario: Open Text Production unit
- **WHEN** a Text ContentUnit enters its professional Text Studio
- **THEN** Text-editor dependencies load on demand after the common Production boundary and all existing Production controls remain functional

### Requirement: Reproducible initial JavaScript budget

The existing deterministic route budget SHALL remain authoritative for entry and `/projects`. F6B acceptance SHALL additionally inspect the Vite manifest/import graph and record measured raw/gzip baselines for common Production and Text Studio. It SHALL fail acceptance if TipTap becomes a static dependency of the common Production shell, Graphic/Video Studio, `/projects`, `/assets`, `/settings` or `/learning`. No permanent Text-editor byte ceiling SHALL be invented before a measured implementation baseline is reviewed.

#### Scenario: Text editor remains isolated
- **WHEN** the F6B production build is inspected
- **THEN** TipTap appears only in Text/legacy-editor dynamic dependency closures, existing hard route budgets still pass, and the new measured Text Studio baseline is recorded
