## ADDED Requirements

### Requirement: Models and AI uses task-oriented local views

The Models & AI section SHALL offer clearly named local views for provider/model registration, purpose routing, and generation capabilities/plugins. It MUST preserve all six top-level Settings sections and MUST NOT change other sections or embed the complete legacy Settings workspace inside Models & AI.

#### Scenario: Open Models and AI
- **WHEN** the user opens Models & AI
- **THEN** provider/model registration is the initial view and purpose routing and generation capabilities/plugins are available through a compact local navigation
- **AND** only the selected local view is visible, with consistent panel hierarchy and no duplicate full-page legacy editor

#### Scenario: Select another Settings section
- **WHEN** the user opens Data Sources, Channels, Rules & Templates, Team & Permissions or Advanced Runtime
- **THEN** its existing behavior, editability and actions remain unchanged except for an unsaved-edits confirmation needed when leaving Models & AI

### Requirement: Models and AI displays readable configuration identities

Model labels SHALL use the safe registered model ID and provider name where available. Generated internal profile keys SHALL remain available in technical details instead of serving as ordinary model titles. Unknown legacy profiles MUST use existing provable labels without inventing metadata.

#### Scenario: Inspect a registered CPA model
- **WHEN** the same registered model is shown in the catalog, purpose selector or capability configuration
- **THEN** its readable model name and provider identify it consistently and its `registered.*` key is not the primary title

#### Scenario: Inspect a legacy profile without catalog metadata
- **WHEN** the profile has no matching registered catalog item
- **THEN** its actual bound model ID or existing profile key remains visible without a fabricated provider or model identity

### Requirement: Models and AI progressively discloses technical configuration

Provider registration SHALL show concise provider summaries and offer explicit edit/discovery actions. Purpose routing SHALL group the global default with labeled purpose-to-model selections. Capability/plugin configuration SHALL group declarations, bindings, fallback order and limits. Technical instructions, internal identifiers and detailed binding forms SHALL be collapsed by default while retaining access to all existing actions and validations.

#### Scenario: Configure a provider
- **WHEN** the user expands provider editing
- **THEN** existing endpoint, credential retention/clear, enablement and exact trusted-LAN controls remain available
- **AND** discovery still requires a saved eligible provider and does not run automatically

#### Scenario: Inspect purpose routing
- **WHEN** the user selects the purpose routing view
- **THEN** the current global default and existing purpose selections appear as aligned labeled rows with truthful inheritance descriptions

#### Scenario: Inspect technical details
- **WHEN** the user expands protocol/binding details or opens the legacy compatibility link
- **THEN** those existing details are accessible without adding a second visible default/route editor to the ordinary model view

### Requirement: Models and AI preserves local drafts and exact save scopes

Switching local model views SHALL preserve every unsaved provider, pending model, purpose selection, capability/plugin/policy edit and secret input in its existing state owner. Registration/purpose and capability saves MUST retain their existing envelopes, CAS revisions, permission checks and secret semantics; the page MUST NOT imply a multi-endpoint atomic save. Save actions SHALL describe the affected draft scope, including changes made in another local view, and show pending/success/failure state. Explicit reload/discard SHALL remain available; leaving Models & AI MUST NOT silently discard dirty state.

#### Scenario: Switch views while editing
- **WHEN** an admin edits provider/purpose or capability settings and switches between local views
- **THEN** all local edits remain intact and no save, discovery, generation or credential transmission occurs

#### Scenario: Save a draft with changes in a hidden view
- **WHEN** a registration/purpose save includes edits made in a different local view
- **THEN** the save scope and presence of those edits are clearly shown before the user invokes the existing save action

#### Scenario: Concurrent configuration conflict
- **WHEN** the existing server rejects a save with 409 after a shared configuration revision advances
- **THEN** the local draft remains available with an explicit conflict and reload/discard choice, without a silent overwrite or retry

#### Scenario: Leave a dirty model section
- **WHEN** the user attempts to leave Models & AI with unsaved changes
- **THEN** the UI either retains that draft or asks for explicit discard before unmounting it

#### Scenario: Read-only user or identity change
- **WHEN** a read-only user inspects the view or the active user identity changes
- **THEN** existing role gates, secret non-disclosure and identity-scoped draft/async cleanup remain effective

### Requirement: Models and AI distinguishes chat registration from media readiness

Configuration, executability and verification SHALL be displayed from their actual existing projections and limited to the relevant capability. A registered chat model or successful chat connection MUST NOT imply media support, and a missing media binding MUST NOT be presented as a failure of the entire provider connection. Static protocol guidance SHALL NOT claim a real provider test or capability outcome.

#### Scenario: Chat is registered but media is unconfigured
- **WHEN** a provider has registered chat models without an image/video binding
- **THEN** media is labeled unconfigured for that specific capability, without implying that provider chat connectivity failed or that media is verified

### Requirement: Models and AI retains responsive and lazy settings boundaries

The local navigation and configuration forms SHALL remain usable on desktop and narrow screens, with labeled controls, keyboard focus and text-based status. Provider guidance and legacy tools MUST NOT load in the initial model view. Existing workspace bundle budgets SHALL remain satisfied without new UI dependencies or global production/editor imports.

#### Scenario: Narrow screen configuration
- **WHEN** the model section is viewed on a narrow screen
- **THEN** local navigation adapts and forms/save controls remain usable without page-level horizontal overflow

#### Scenario: Initial Settings load
- **WHEN** the user loads the initial model view
- **THEN** it does not eagerly mount Provider guidance or the full legacy Settings workspace and unrelated workspace budget checks remain passing
