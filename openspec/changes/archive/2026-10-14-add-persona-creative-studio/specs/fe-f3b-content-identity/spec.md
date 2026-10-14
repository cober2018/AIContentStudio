## ADDED Requirements

### Requirement: Identity revisions may carry persona-native creative profiles

Persona/Account/Series profile JSON SHALL support bounded Text/Graphic/Audio/Video creative-profile fields without changing stable identity tables. Brand profile JSON MUST reject these creative-profile fields. Creative-profile inheritance/origin applies only across Persona → Account → Series per whole field, while Brand constraints remain separate Effective Context. IdentitySnapshot SHALL freeze the effective creative profile and origin with the existing checksum.

#### Scenario: Persona creative profile advances
- **WHEN** Persona saves a new Text creative profile revision
- **THEN** new explicitly rebound/created production may use it while existing IdentitySnapshots, Units, Runs and Masters remain unchanged

### Requirement: Persona is the normal creative configuration root

Identity UX and resolution SHALL treat Persona as the ordinary scope for creative defaults. Account/Series may explicitly override modality profiles. Owner/User MUST NOT be presented as the automatic writing/visual/audio style source shared across all Personas.

#### Scenario: Persona A learned style does not affect Persona B
- **WHEN** the owner uses two Personas and saves a creative method/profile for Persona A
- **THEN** Persona B's effective identity/ordinary method discovery does not inherit it merely because owner IDs match

### Requirement: Identity Workspace exposes typed creative configuration

Persona/Account/Series SHALL expose a `创作配置` surface with inherited origin, Auto/Custom/Composed mode, exact Studio Skill/Preset/Quality refs, method extensions, model policy, default recipe and readiness. Normal users SHALL NOT need to edit raw workflow/profile JSON to configure supported defaults.

#### Scenario: Account overrides only Graphic behavior
- **WHEN** an Account explicitly overrides the Graphic creative profile and leaves other modality fields absent
- **THEN** Graphic origin is Account while Text/Audio/Video continue inheriting their existing effective fields

#### Scenario: First Starter initialization selects its confirmed Persona
- **WHEN** the user explicitly initializes a Starter Persona from an empty identity tree and has not changed identity selection during the request
- **THEN** the refreshed tree selects that confirmed Persona, opens its typed creative configuration and reports success without a second initialization request

#### Scenario: Late initialization preserves a newer identity selection
- **WHEN** the user changes identity selection while a Starter initialization request is pending
- **THEN** the confirmed record may refresh the tree but its late callback does not replace the newer selection or discard that selection's creative draft

#### Scenario: Two Personas share Brand constraints without sharing creative defaults
- **WHEN** one Brand owns a technical Persona and a lifestyle Persona and defines Brand Voice or boundary constraints
- **THEN** both Personas apply those constraints, but neither Persona inherits a Studio Skill, Style Preset, Quality Profile, Recipe or creative method stack from Brand
