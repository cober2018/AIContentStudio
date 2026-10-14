## ADDED Requirements

### Requirement: Persona-owned cross-platform editorial series

The system SHALL represent one editorial Series as a stable, versioned Persona-owned content initiative independent of any single delivery Account, while retaining historical Account-owned Series semantics.

#### Scenario: Create a series without an account

- **GIVEN** a Persona with valid creative and brand constraint context
- **WHEN** an owner creates an editorial Series without selecting a platform Account
- **THEN** the Series is persisted as the Persona's editorial Series, with a stable identity and revision
- **AND** content may be created under the Series before any delivery Account is configured

#### Scenario: Same editorial series serves different platforms

- **GIVEN** an AI technology Persona owns one editorial Series
- **WHEN** it binds a WeChat Account, a Zhihu Account and a Xiaohongshu Account with valid exact content forms
- **THEN** all target bindings reference the same editorial Series identity
- **AND** no cloned same-name Account Series is required

#### Scenario: Same channel with two distinct accounts

- **GIVEN** the Persona owns two Xiaohongshu Accounts
- **WHEN** a Series binds both Accounts for compatible forms
- **THEN** both targets remain individually addressable, editable and independently authorized

#### Scenario: Existing account-owned series remains stable

- **GIVEN** an older Series has a required Account owner and historical Units
- **WHEN** the new model is enabled
- **THEN** its historical identity, source snapshots, Unit links and legacy defaults retain their original meaning
- **AND** no automatic same-title merge, deletion or account rebinding occurs

### Requirement: Explicit Series distribution targets

The system SHALL persist an auditable, versioned Series-to-Account-to-Form association and validate Persona, platform and capability compatibility before it becomes an enabled target.

#### Scenario: Reject cross-persona target

- **WHEN** a Series owned by Persona A attempts to bind an Account owned by Persona B
- **THEN** the server rejects the binding
- **AND** no hidden owner-level creative fallback or implicit cross-persona distribution is created

#### Scenario: Disable or revoke binding

- **WHEN** a target association is disabled or an Account loses required authorization
- **THEN** new distribution/authorization is blocked appropriately
- **AND** historical freeze/Attempt/Receipt remains readable and unmodified

#### Scenario: Mapping does not mean authorization

- **WHEN** a user enables a Series target
- **THEN** the target becomes selectable for future Variant preparation
- **BUT** it has no permission to bypass Candidate review, explicit Delivery Authorization or account checks

### Requirement: Distinct source and target creative contexts

The system SHALL freeze source Persona/Series identity separately from per-target Account/form context; delivery-time profile adaptation MUST NOT rewrite an accepted Master.

#### Scenario: Account-free Master followed by multi-account Variants

- **WHEN** a Master is accepted using Persona and editorial Series without an Account
- **THEN** source identity and creative method evidence are frozen without an arbitrary Account
- **AND** later Variants can be prepared under different compatible target Accounts

#### Scenario: Account-specific profile changes

- **GIVEN** one source Master and two target Accounts with different style or compliance constraints
- **WHEN** Variants are prepared
- **THEN** their effective target contexts are resolved separately and pinned
- **AND** the original Master source identity/payload/hash does not change

### Requirement: Persona-native account and series management

The product SHALL provide one navigable Persona/Accounts/Series/Distribution management surface with full create/edit/read/compatibility flows and explicit inheritance source display.

#### Scenario: User manages all entities from identities

- **WHEN** a user opens `/identities`
- **THEN** they can manage Persona, multiple public channel Accounts, editorial Series and distribution targets without needing a new root navigation item

#### Scenario: Legacy account URL

- **WHEN** an existing bookmark opens `/accounts`
- **THEN** it reaches the canonical account management surface without losing a supported legacy deep link
