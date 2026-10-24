## ADDED Requirements

### Requirement: Two craft skills reachable through the platform MCP

The platform SHALL provide two independent craft skills, ae-motion and resolve-edit, each with an index of entries. The creative MCP SHALL return a skill's index and any single entry on request. Local agent skill files SHALL point to the MCP instead of copying the content.

#### Scenario: Read an index
- **WHEN** an agent asks the MCP for the ae-motion index
- **THEN** it receives the list of jobs with the template or technique file for each

#### Scenario: Read one entry
- **WHEN** an agent asks for one entry of resolve-edit
- **THEN** it receives only that file

### Requirement: AE template library

Each AE template version SHALL have a manifest describing its use, replaceable fields, duration range, aspect ratios, fonts and the `.aep` path and hash. A template SHALL be offered for automatic use only after two renders with different content are recorded as checked. A changed template SHALL be a new version.

#### Scenario: Draft template
- **WHEN** a template has fewer than two recorded checks
- **THEN** it is listed as draft and not used automatically

#### Scenario: New version
- **WHEN** a template is changed
- **THEN** a new version folder is created and the old version still renders

### Requirement: Render a template into candidate material

The MCP SHALL render a template version with given content through the local `aerender` into a new candidate material revision of the unit's project, recording template id, version and content hash. It SHALL NOT bind the material to a shot or accept anything.

#### Scenario: Render a number card
- **WHEN** an agent renders number-card v1 with a number and a caption for U80
- **THEN** a new candidate video material exists with the template id, version and content hash recorded, and no shot changes

#### Scenario: Missing font or AE
- **WHEN** a required font or `aerender` is missing
- **THEN** the render stops with that reason and nothing is created
