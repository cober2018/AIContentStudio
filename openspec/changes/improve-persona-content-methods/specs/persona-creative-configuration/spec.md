## ADDED Requirements

### Requirement: Persona method trials preserve model voice and unrelated configurations
The system SHALL offer a run-scoped trial of a versioned creative method/style selection using the existing configuration resolution. Shared methods and Persona style parameters SHALL remain separate. Trial selection and saving a method/style default MUST NOT change provider/model/profile bindings, routing policies, voice IDs, rates or other existing generation parameters, rights, another Persona, or product-domain configuration. Exact effective method and model identities SHALL be inspectable independently.

#### Scenario: Trial a new graphic method for technology
- **WHEN** the technology Persona chooses a trial visual/card-planning method
- **THEN** only the declared run-scoped method/style changes affect the new attempt, its original model policy remains in force, and lifestyle, product and existing runs remain unchanged

#### Scenario: A proposed method requires an unavailable provider
- **WHEN** a trial cannot execute with the user's preserved model/tool bindings
- **THEN** it reports the incompatibility and does not silently select a different provider or change configuration

### Requirement: Method default adoption applies a bounded explicit revision change
Adopting a successful trial as a Persona or Series modality default SHALL show the exact method/style/quality difference and target scope, use the latest configuration revision for conflict checking, and retain all unrelated fields. No-op changes SHALL avoid a write. Conflicts SHALL preserve the draft and require an explicit reconciliation. Mere acceptance of a work or feedback comment MUST NOT promote a default.

#### Scenario: Another entry updates a voice setting during method editing
- **WHEN** the saved identity revision changes before a method default is submitted
- **THEN** the stale write is rejected, the local method draft is retained and no old voice/model settings overwrite the newer configuration

#### Scenario: Accept a work without adopting its trial method
- **WHEN** a user accepts a trial output but has not chosen to save its method as a scoped default
- **THEN** the output and trial provenance are retained while the original default remains selected
