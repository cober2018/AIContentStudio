## MODIFIED Requirements

### Requirement: Product shell

The frontend SHALL offer nine primary workspaces with navigable routes and loading, error, and empty views. `/identities` SHALL be a persistent Content Identity workspace rather than a long-lived placeholder.

#### Scenario: Open identities
- **WHEN** the user opens `/identities`
- **THEN** the application loads backend Brand/Persona/Account/Series state and does not substitute browser fixture identity data

### Requirement: Content matrix editing

Content Unit identity selection SHALL support persisted Persona plus optional Account and Series context. New or explicitly rebound units SHALL receive a server-created IdentitySnapshot. Existing FE-F2 safe in-place-versus-replacement lifecycle semantics remain unchanged.

#### Scenario: Create account-bound unit
- **WHEN** a user creates a unit with Persona, Account and optional Series
- **THEN** the server validates the hierarchy, resolves the effective identity/workflow, pins an IdentitySnapshot, and reload preserves those choices

#### Scenario: Legacy unit
- **WHEN** an older unit has no IdentitySnapshot
- **THEN** the matrix/production entry truthfully marks identity as legacy/unknown until explicit rebind
