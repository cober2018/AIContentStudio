## ADDED Requirements

### Requirement: External methods retain provenance and executor-specific adaptation
Selected third-party methods SHALL record upstream repository, pinned revision, applicable license, selected subfiles, modification summary, runtime requirements and actual validation state. Shared method instructions, Persona style parameters and AE/Resolve execution adapters SHALL remain distinguishable. Source inspection MUST NOT be represented as installation or execution validation.

#### Scenario: A Remotion shot is adapted to After Effects
- **WHEN** the user-selected shot is implemented through the existing AE MCP
- **THEN** the record identifies the original recipe and new adapter, and actual rendered comparison validates the supported effect rather than claiming arbitrary engine equivalence

### Requirement: Managed execution uses the prepared method manifest
The local Agent SHALL use the prepared stage manifest to load approved selected methods and return usage evidence through the existing execution workflow. Platform MCP SHALL retain its existing read/report boundary; method text MUST NOT implicitly authorize installation, provider dispatch, global settings changes or publication. External methods requiring unresolved commercial authorization SHALL remain unselected for commercial production.

#### Scenario: An upstream Skill asks to install its own runtime
- **WHEN** the selected adapted method is read for a prepared task
- **THEN** execution uses the declared existing adapter and does not run the upstream install/update instructions merely because they appear in the source file
