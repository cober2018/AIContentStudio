# product-settings Specification

## Purpose
Provide product-oriented Settings views over existing model, connector, channel, rule, template and authorization truth. Preserve safe serialization, truthful capability and role-derived editability without duplicating registries or implying unverified runtime support.
## Requirements
### Requirement: Settings uses product-oriented sections

The Settings workspace SHALL organize Models & AI, Data Sources, Channels, Rules & Templates, Team & Permissions, and Advanced Runtime/Security as distinct sections.

#### Scenario: Open Settings
- **WHEN** the user opens `/settings`
- **THEN** product concepts are visible without requiring ordinary users to understand raw provider/registry internals

### Requirement: Editability is truthful

Every settings item SHALL expose whether it is editable, read-only or unavailable based on real backend capability.

#### Scenario: Read-only channel registry
- **WHEN** a Channel Registry field has no durable mutator
- **THEN** Settings displays it read-only and does not render a fake Save action

#### Scenario: Disconnected Data Source Plugin
- **WHEN** Notion/Obsidian/media/API/SQL plugin descriptor is unavailable
- **THEN** Settings shows the registered reason and does not claim connection success

### Requirement: Model settings reuse existing persistence

Models, routes, LLM/image provider configuration and secret masking SHALL continue using existing SystemSetting/runtime configuration services.

#### Scenario: Secret display
- **WHEN** the user views a configured API key
- **THEN** only masked/configured metadata is returned and plaintext secrets are never serialized

### Requirement: Data Source settings mirror typed plugin registry

Data Source settings SHALL expose the FE-F2 typed plugin descriptors and existing Connector configuration without introducing a second plugin registry.

#### Scenario: Studio Source
- **WHEN** `studio.source` is listed
- **THEN** its actual executable/internal capabilities are shown from the descriptor

#### Scenario: Generic Connector exists
- **WHEN** an API Connector is configured
- **THEN** it is shown as connector configuration but MUST NOT automatically mark unrelated Data Source Plugin keys connected unless an explicit mapping contract exists

### Requirement: Channel settings mirror Channel Registry

Channel settings SHALL display channel/content-form/workflow/renderer/rule/discoverability/publisher metadata from the existing Channel Registry.

#### Scenario: Channel capability changes
- **WHEN** registry configuration changes
- **THEN** Settings reflects the new registry state without copying it into another table

### Requirement: Rules and templates remain distinct

Deterministic Rule descriptors SHALL be shown separately from PromptVersion, ChannelTemplateVersion and Discoverability profile/template resources.

#### Scenario: Inspect rule
- **WHEN** a deterministic rule is listed
- **THEN** it is labeled Rule with key/version and not represented as a Prompt

### Requirement: Team reflects current auth reality

Team & Permissions SHALL show existing users/roles and current development-header auth mode without claiming production organization, invite, SSO or tenant administration that is not implemented.

#### Scenario: Open Team
- **WHEN** the user opens Team settings
- **THEN** current users/roles and auth-mode limitations are explicit

### Requirement: Existing authorization remains enforced

Admin-only Settings/Connector/Template mutations SHALL remain admin-only; safe read views follow current authenticated-user contracts.

#### Scenario: Non-admin mutation
- **WHEN** a non-admin invokes an admin-only settings mutation
- **THEN** the existing authorization denial remains effective

### Requirement: Settings projections enforce safe serialization and caller capability

Product settings SHALL use explicit field allowlists and preserve each underlying API's current role gates. Secret values, credential-bearing URLs, raw connector configs, local paths and raw infrastructure diagnostics MUST NOT escape through a safe read projection. Editability SHALL be derived from both durable mutation support and the caller's role; unauthorized sections SHALL be unavailable with a safe reason rather than trigger unsafe inventory reads.

#### Scenario: Viewer inspects product settings
- **WHEN** a viewer opens the safe product Settings API
- **THEN** only permitted safe metadata is returned, admin-only details stay unavailable, and editability does not imply viewer mutation rights

#### Scenario: Credentials in configuration
- **WHEN** raw provider or Connector configuration includes an API key or credentials in URL/query/config
- **THEN** safe projection omits those values and never exposes them in errors or nested metadata

### Requirement: Settings actions preserve exact version and side-effect contracts

Inventory SHALL expose only per-type/per-status supported template actions, bootstrap Rule descriptors before first evaluation, and distinguish configured channel references from verified executor capability. Models edits SHALL preserve the complete loaded profile/route snapshot and blank-secret retention without resubmitting masks. Network probes/pulls and image-save local CLI writes SHALL require explicit labeled actions and MUST NOT occur during read-only inventory.

#### Scenario: Cold-start rules and published prompts
- **WHEN** inventory loads before any draft evaluation
- **THEN** deterministic fallback rules are present and published Prompt entries do not advertise unsupported clone/edit/archive actions

#### Scenario: Preserve model profiles
- **WHEN** an admin edits one profile in a loaded configuration
- **THEN** other profiles/routes remain unchanged and displayed secret masks are not sent as credentials

#### Scenario: Inspect data sources
- **WHEN** a caller only reads data-source inventory
- **THEN** no Connector pull/probe runs and editor/admin pull permission remains distinct from admin-only configuration permission

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

### Requirement: Capability inventory separates configuration from verification
Product Settings SHALL project existing typed Plugin, Connector, Channel and model truth with bounded CapabilityRegistration/Verification safe metadata. It SHALL distinguish discovered, configured, executable, verified and unavailable for exact kind/key/version/scope and explain missing or invalid verification. A read MUST NOT probe networks or imply an editable action without durable mutation support and caller permission.

#### Scenario: Configured but unverified Publisher
- **WHEN** a Publisher implementation and account configuration exist without valid scoped real-account verification
- **THEN** Settings displays the safe configuration and an unavailable remote action reason, not a verified badge

#### Scenario: Verification expired or config changed
- **WHEN** stored evidence expires or its config fingerprint differs from the active runtime
- **THEN** Settings shows the scope as no longer verified without deleting the historical evidence

### Requirement: Explicit capability actions retain role and redaction gates
Capability probe and verification actions SHALL be separately labeled, authorized and audited; remote side-effect verification SHALL require explicit account/action confirmation. Safe API projections MUST exclude nested provider secrets and credential-bearing errors as well as existing Settings secret fields.

#### Scenario: Viewer clicks verify
- **WHEN** a viewer invokes a capability verification action
- **THEN** authorization rejects it without a provider call or verification record

#### Scenario: Provider returns sensitive diagnostic
- **WHEN** a probe error contains a signed URL or token in a nested response
- **THEN** the Settings response and persisted audit expose only an allowlisted reason code

### Requirement: Settings configures model capabilities plugins and routing
Models & AI SHALL expose manual capability declarations, per-capability protocol/model/connection bindings, plugin executor/model bindings, ordered defaults, automatic fallback authorization and per-request limits. Declared, configured, executable and verified states SHALL remain distinct with safe unavailable reasons.

#### Scenario: Configure plugin fallback
- **WHEN** an admin configures a chat model and a separate image plugin default
- **THEN** the persisted settings show both identities and a no-network plan preview explains image routing through that plugin

### Requirement: Routing edits preserve existing authorization and safe configuration
All capability/plugin/route/limit mutations SHALL remain admin-only, preserve unrelated loaded profiles/routes, use expected revisions, retain blank secrets without resubmitting masks, and expose only safe allowlisted metadata. Inventory and plan preview MUST NOT install plugins, probe suppliers or generate media.

#### Scenario: Viewer opens capability settings
- **WHEN** a viewer inspects model capabilities
- **THEN** safe metadata is shown without plaintext credentials or mutation rights and no supplier request occurs

### Requirement: Settings distinguishes local CLI readiness from verification
When a local MiniMax CLI provider is installed and registered, Settings SHALL show its fixed capability families and separately report loaded, executable and verified state. Reading Settings or building a plan MUST NOT read the CLI credential file or invoke a paid generation request.

#### Scenario: Local MiniMax CLI is installed
- **WHEN** an administrator opens model capability settings
- **THEN** the UI can show the bounded MiniMax CLI adapter and its supported operation families, while account, quota and real-output verification remain explicitly separate

#### Scenario: Read settings after enabling image capability
- **WHEN** an admin reads the saved capability configuration
- **THEN** no image is generated and declared support does not become verified automatically

### Requirement: Settings separates Studio built-ins external Skills and learned methods

Product Settings SHALL present Studio Built-in Skills/Style Presets/Quality Profiles as read-only product resources, Installed Agent Skills as external inventory and Capability Memory as user-managed reusable methods. Equal names do not imply the same source or executability.

#### Scenario: Inspect creative inventories
- **WHEN** the user opens the creative capability inventory
- **THEN** source kind, exact version/revision, executable/read-only state and provenance are visible without installing/enabling/importing anything

### Requirement: Provider configuration remains infrastructure not Persona style

Global provider/model/capability settings SHALL remain execution infrastructure. Persona-specific creative style/method defaults belong in Identity Workspace and MUST NOT be stored as global user/provider settings.

#### Scenario: Save Persona style separately from provider settings
- **WHEN** a user changes a Persona's creative style or method defaults
- **THEN** the change is saved through Identity Workspace without writing creative style into global provider/model settings

### Requirement: Image and Audio settings share one multimedia configuration surface

Models & AI settings SHALL expose one multimedia generation configuration surface for Image and Audio, with modality-specific sections driven by adapter-declared capabilities. The normal view SHALL show common controls, selected preset/binding summary and candidate count where supported. An explicit Advanced Settings action SHALL show exact provider/model/profile, image references/aspect/size or audio voice ID/rate/other supported fields. Unsupported fields SHALL be hidden or visibly unavailable. Settings SHALL not expose credentials or create per-user voice ownership records.

#### Scenario: Configure image candidates and an audio voice together
- **WHEN** the user configures a four-candidate image request and a Persona audio voice
- **THEN** each modality shows only its supported controls, preserves separate exact bindings and exposes one preview/receipt model without merging the image and audio payloads

#### Scenario: Large voice inventory remains usable
- **WHEN** the local voice catalog has hundreds of entries
- **THEN** the settings page provides search/filter/favorite/preview and Advanced Settings rather than an unbounded dropdown

### Requirement: Form completion and field polishing have independent model routes
Settings SHALL expose form_autofill and field_polish as independent text-model purposes within existing Models and AI usage routing. It MUST reuse provider registration, masked credentials and configuration revision handling, and display default inheritance and actual execution provenance.

#### Scenario: Different models for completion and polish
- **WHEN** the user saves distinct registered models for the two purposes
- **THEN** future requests use the corresponding model and report its actual provider, model and configuration version without altering historical runs

#### Scenario: Explicit model becomes unavailable
- **WHEN** a selected model is disabled or no longer executable
- **THEN** assistance reports the configuration problem rather than claiming an undisclosed substitute was the selected model

#### Scenario: Routes are not explicitly assigned
- **WHEN** either purpose has no explicit selection
- **THEN** the settings and assistance show inheritance of the existing global default, and saving the configuration alone does not trigger inference
