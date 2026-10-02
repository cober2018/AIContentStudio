## ADDED Requirements

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
