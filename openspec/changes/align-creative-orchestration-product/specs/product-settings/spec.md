## ADDED Requirements

### Requirement: Settings exposes local Creative Execution/MCP safely

Advanced Runtime MAY show safe status for the AIContentStudio local MCP endpoint, local execution work-root readiness and executor descriptors. Reading Settings MUST NOT reveal the local MCP bearer token, scan arbitrary directories, connect to professional tools or dispatch an execution.

#### Scenario: Open Creative Execution settings
- **WHEN** the admin opens Advanced Runtime
- **THEN** the UI can show configured/executable local status and setup guidance while secrets/professional-tool probes remain absent until an explicit action exists

### Requirement: Settings manages Capability Memory lifecycle without executing it

Settings or a dedicated subview SHALL let the authorized user list candidate/saved/pinned/archived/deprecated Capability Artifacts, inspect scope/provenance/revisions/usage, promote/pin/archive/deprecate and edit a new revision. First-version Settings MUST NOT execute arbitrary stored tool code.

The same surface MAY show locally installed Agent Skills for awareness, but it MUST label them as an external installed inventory distinct from Capability Memory. It MUST NOT import/export/install/enable/overwrite them through Capability Memory actions, and Capability promotion MUST NOT change `skills_enabled`.

#### Scenario: Promote captured recipe
- **WHEN** the user reviews a project-scoped candidate and chooses Save
- **THEN** it becomes discoverable at that scope without changing any Identity/Workflow/channel rule

#### Scenario: Distinguish installed skills from saved capabilities
- **WHEN** an installed Agent Skill and a CapabilityArtifact have the same display name
- **THEN** Settings shows separate source kinds and stable identities, and saving one does not modify or enable the other

### Requirement: Ordinary legacy configuration actions move into the product Settings surface

Connector configuration/explicit pulls, template/rule management and required local runtime operations that remain supported SHALL have product-oriented entries before the legacy Settings page loses daily-navigation status. Advanced compatibility tools MAY remain lazy, but ordinary users MUST NOT need a separate “legacy administrator” page for routine supported configuration.

#### Scenario: Manage a Connector
- **WHEN** the supported Connector action remains part of daily product use
- **THEN** it can be reached from Product Settings with existing authorization/side-effect labels and without loading the full legacy page by default
