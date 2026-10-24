## ADDED Requirements

### Requirement: Resource list detail and explicit use pages
The shared library SHALL expose URL-preserved classification, search, status, type, rights and real pagination. Resource overview, exact revisions, usage, explicit project reuse and management SHALL have distinct views while retaining existing resource/id and generation task links. Tools SHALL load only when explicitly selected and navigation MUST NOT generate, accept, freeze, attach or archive resources.

#### Scenario: Return from a resource
- **WHEN** a user opens a resource or explicit tool and returns
- **THEN** list filters and pagination remain available without a resource mutation

#### Scenario: Exact project reuse
- **WHEN** an authorized editor selects an owned project for a material revision or frozen FactPack
- **THEN** the workspace names the project and preserves the existing exact-version, checksum, revision and explicit-confirmation gates

#### Scenario: Read failure or invalid link
- **WHEN** a selected resource or list cannot be read or its identifier is invalid
- **THEN** the UI shows that uncertainty rather than a prior resource or a successful empty result

### Requirement: Resource management remains explicit
Default resource and collection overview SHALL keep current rights limitations visible while placing edit, revoke, archive and collection-member mutations behind explicit views. Existing user permission, archived state, collection snapshot/version conflict and source-specific rights semantics SHALL be retained.

#### Scenario: Collection member is not fact approval
- **WHEN** a source or FactPack is organized into a knowledge collection
- **THEN** this does not grant public or model-use rights or bind a project fact boundary

#### Scenario: Conflicting collection revision
- **WHEN** a collection edit encounters a newer revision
- **THEN** the user's input is not automatically retried against the new version and an explicit reread is required
