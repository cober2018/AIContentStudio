## ADDED Requirements

### Requirement: Persona method improvements are selective versioned adaptations
Easel-derived Persona method improvements SHALL be mapped to the existing research, text, graphic, audio and video method responsibilities with exact upstream revision/subfile provenance, adaptation notes, inputs, outputs, tunable fields and actual validation state. Changed method instructions/contracts/styles SHALL use new selectable versions; existing resource versions, saved defaults, frozen attempts and product bindings MUST NOT be silently replaced. An inspected upstream Skill MUST NOT be represented as locally installed or validated.

#### Scenario: Add a new visual-director method version
- **WHEN** a Persona trial uses an adapted design method
- **THEN** its local version and source references are recorded, old references continue to resolve the original version, and product workflows are not rebound

### Requirement: Method reasoning and registered execution have separate responsibilities
Skills SHALL specify creative reasoning and bounded outputs while registered platform tools/providers and the prepared CLI/MCP professional execution path retain execution authority. Graphic layout/rendering SHALL consume declared typed parameters, audio SHALL retain its exact TTS contract, and video SHALL retain manual web clip generation where applicable, Resolve main editing and optional AE packaging. Upstream install scripts, gateways, automatic publishing instructions and arbitrary rendering code MUST NOT become active by selecting a method.

#### Scenario: A visual plan requires a relationship diagram
- **WHEN** the plan chooses a diagram structure
- **THEN** the method produces a supported semantic plan and the declared renderer consumes validated parameters, or the unsupported structure is reported explicitly; free-form instructions are not claimed to have changed a deterministic renderer

### Requirement: Trial method controls are verified against actual requests
Persona trial stages SHALL preserve ordered independent method controls and the stage-level switch. Effective enabled methods SHALL appear once in the relevant execution instructions, disabled methods SHALL contribute no instructions through nested snapshots or fallback paths, and references SHALL be limited to the current stage's authorized context. Method disabling MUST NOT disable underlying fact, rights or output-schema checks. Receipts SHALL distinguish configured selection from actually executed methods.

#### Scenario: Disable one method inherited from a Persona
- **WHEN** a run disables that method while keeping another applicable method enabled
- **THEN** the full actual request contains only the enabled method's applicable instructions, preserves the disabled selection for reuse, and still enforces fact and output contracts
