## MODIFIED Requirements

### Requirement: Immutable IdentitySnapshot

Every new ContentMasterRevision SHALL pin the exact IdentitySnapshot used for that production revision. Historical Master revisions MUST retain that snapshot even if Brand/Persona/Account/Series changes later. Candidate v4 SHALL freeze the same Master-pinned IdentitySnapshot ID/checksum rather than resolving current identity.

#### Scenario: Identity changes after Master save
- **WHEN** the identity hierarchy advances after a Master revision is saved
- **THEN** the old Master remains bound to its original snapshot and is projected stale against current production context

#### Scenario: V4 Candidate identity
- **WHEN** a v4 Candidate freezes a current Master
- **THEN** the Candidate identity section exactly matches the Master revision's pinned IdentitySnapshot
