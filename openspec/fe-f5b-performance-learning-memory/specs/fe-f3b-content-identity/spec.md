## MODIFIED Requirements

### Requirement: Identity and Content Memory remain separate

Content Memory SHALL be backed by validated, versioned ContentMemory records scoped to owner/Brand/Persona/Account/Series. Memory remains a dynamic learned layer and MUST NOT silently mutate stable Identity revisions.

#### Scenario: Read validated memory
- **WHEN** the user opens an identity's Content Memory tab
- **THEN** applicable validated memory entries and revision provenance are shown with scope origin and limitations

#### Scenario: Promote Identity learning
- **WHEN** an accepted identity-category LearningCandidate is promoted to memory
- **THEN** ContentMemory changes but Brand/Persona/Account/Series revisions remain unchanged until a separate explicit identity save
