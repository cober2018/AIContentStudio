## ADDED Requirements

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
