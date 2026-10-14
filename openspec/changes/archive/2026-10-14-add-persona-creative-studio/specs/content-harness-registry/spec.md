## ADDED Requirements

### Requirement: Studio creative resources are version-pinned registry/catalog entries

The product SHALL expose version-pinned Studio built-in Skill, Style Preset and Quality Profile resources through a server-authoritative inventory. These declarative creative resources SHALL remain distinct from executable Node/Rule/Provider plugins, Installed Agent Skills and Capability Memory.

#### Scenario: Historical receipt references built-in Skill v1
- **WHEN** the product later ships built-in Skill v2
- **THEN** historical attempt receipts continue identifying v1 and new Workflow/Profile revisions may explicitly adopt v2

### Requirement: Deterministic creative tools remain registered executors

Graphic composition/QC, Audio QC and other deterministic creative actions SHALL execute only through explicit registered Tool/Rule/Provider contracts with exact key/version and typed schemas. Skill documentation MUST NOT be an arbitrary code-execution mechanism.

#### Scenario: Built-in Skill mentions a deterministic composer
- **WHEN** the Skill contract references `studio.graphic.layout-compose@1`
- **THEN** validation requires a matching registered implementation before the Skill is executable

### Requirement: Creative resource validation is persistent

The repository SHALL continuously validate resource references, schema bounds, tool keys, Persona blueprint/default-recipe references and executor-consumed tunables. Broken or drifting creative packages SHALL fail tests/validation instead of becoming partially executable.

#### Scenario: Blueprint references a missing resource version
- **WHEN** a Persona blueprint or default recipe references a missing Skill, Preset or Quality Profile version
- **THEN** persistent validation fails instead of making the broken package partially executable
