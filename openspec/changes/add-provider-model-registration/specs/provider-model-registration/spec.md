## ADDED Requirements

### Requirement: Provider registration shares versioned configuration
The system SHALL register providers and selected exact model IDs in the existing versioned SystemSetting configuration, preserve unrelated fields, and reject stale saves atomically with 409. It MUST NOT introduce another registry or durable business table.

#### Scenario: Concurrent provider save
- **WHEN** another editor has changed the configuration revision
- **THEN** registration rejects the stale write without changing credentials, profiles, default or purpose routes and preserves the client draft

### Requirement: Credentials are write-only in product APIs
Only authorized administrators SHALL change provider credentials. Read views MUST expose only configured/masked metadata, and neither logs, errors, plans, manifests nor repository documents SHALL contain plaintext credentials. Blank input SHALL preserve the secret; removal SHALL be explicit.

#### Scenario: Read registered provider
- **WHEN** an active user reads Settings after registration
- **THEN** the model catalog and non-secret configuration are visible without the original API key

### Requirement: Model discovery is explicit and bounded
The system SHALL fetch an authenticated bounded model list only on an authorized explicit discovery action against the registered endpoint. It MUST NOT generate content, infer media capabilities or register every returned model automatically. Exact model IDs SHALL also support manual registration.

#### Scenario: Discovery unavailable
- **WHEN** the provider rejects /models or returns an invalid response
- **THEN** the UI displays a safe reason, keeps existing configuration and allows manual IDs without claiming validation success

### Requirement: Private gateway access is narrowly authorized
HTTP/private gateway access SHALL require administrator confirmation of the exact trusted endpoint. Both discovery and execution MUST use the same bounded destination policy, prohibit redirects/credential-bearing URLs/unapproved targets and preserve unrelated SSRF and media download restrictions.

#### Scenario: CPA gateway registration
- **WHEN** the administrator explicitly registers the trusted LAN HTTP endpoint
- **THEN** only that endpoint is authorized and the UI discloses unencrypted credential transport

### Requirement: Default and purpose selections are executed truthfully
Model selection SHALL resolve supported explicit task/node selection, then saved purpose selection, then global default, then existing legacy fallback only when no new default exists. Invalid explicit choices MUST fail with a typed reason. Setting a default MUST preserve existing explicit routes and historical runs.

#### Scenario: Gemini default with rewrite override
- **WHEN** gemini-3.8-flash-high is saved as default and rewrite explicitly selects another registered model
- **THEN** default consumers use Gemini while rewrite uses its explicit model, with safe runtime provenance

#### Scenario: Workflow node persists the registered profile as its model source
- **WHEN** an AI workflow node stores `model_profile_id` without duplicated `provider` or `model` fields
- **THEN** the server resolves provider/model from that registered profile
- **AND** optional provider/model fields are treated as checked compatibility projections
- **AND** any mismatched projection fails closed

### Requirement: Discovery does not prove generation capabilities
Registered models SHALL retain distinct declared/configured/executable/verified states. Media execution MUST continue through actual capability adapters and configured plugins instead of chat branding.

#### Scenario: Chat model has no image adapter
- **WHEN** a registered CPA chat model is selected for an image task without a real image binding
- **THEN** the existing authorized plugin routing applies or the task is unavailable; the system does not claim native image support
