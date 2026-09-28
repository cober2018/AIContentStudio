## MODIFIED Requirements

### Requirement: Versioned Brand / Persona / Account / Series hierarchy

The system SHALL persist Brand → Persona → Account → Series as explicit stable entities. Existing ContentPersona SHALL remain the Persona stable entity. Brand, Persona, Account and Series profile changes SHALL be stored as append-only revisions.

#### Scenario: Create hierarchy
- **WHEN** an authorized editor creates Brand, Persona, Account and Series children
- **THEN** every child is persisted under its actual parent and reload returns the same hierarchy

#### Scenario: Reject mismatched hierarchy
- **WHEN** a request combines a Series, Account or Persona that are not in the same persisted hierarchy
- **THEN** the operation is rejected without mutating any identity or project record

#### Scenario: Save next revision
- **WHEN** an editor saves a profile using the current expected revision
- **THEN** revision N+1 is created and all earlier revisions remain immutable and readable

#### Scenario: Stale revision
- **WHEN** another revision has already committed
- **THEN** a stale save returns 409 and does not partially update current identity state

Opportunity Assessment MAY recommend valid stable identity hierarchy entities, but recommendation SHALL NOT mutate identity revisions or create IdentitySnapshot.

#### Scenario: Recommended Persona/Account/Series
- **WHEN** an Assessment saves identity recommendations
- **THEN** hierarchy ownership is validated and identity remains unchanged

### Requirement: Identity and Content Memory remain separate

FE-F3B SHALL NOT automatically convert performance observations into identity or Content Memory mutations.

#### Scenario: Memory tab before F5
- **WHEN** the user opens Content Memory in FE-F3B
- **THEN** the UI may show truthful linked historical content and explicitly marks automated learning/strategy promotion as not yet implemented

Opportunity relevance/recommendation SHALL NOT be treated as verified learning or written automatically into Content Memory.

#### Scenario: Later performance
- **WHEN** converted content later performs well
- **THEN** F5A makes no automatic Identity/Memory mutation; later LearningCandidate flow owns that decision
