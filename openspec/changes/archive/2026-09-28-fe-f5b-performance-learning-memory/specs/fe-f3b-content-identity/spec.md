## MODIFIED Requirements

### Requirement: Identity and Content Memory remain separate

FE-F3B SHALL NOT automatically convert performance observations into identity or Content Memory mutations.

#### Scenario: Historical Memory tab before F5
- **WHEN** the user opens Content Memory in the pre-F5 FE-F3B baseline
- **THEN** the UI may show truthful linked historical content and explicitly marks automated learning/strategy promotion as not yet implemented

Opportunity relevance/recommendation SHALL NOT be treated as verified learning or written automatically into Content Memory.

#### Scenario: Later performance
- **WHEN** converted content later performs well
- **THEN** F5A makes no automatic Identity/Memory mutation; later LearningCandidate flow owns that decision

Content Memory SHALL be backed by validated, versioned ContentMemory records scoped to owner/Brand/Persona/Account/Series. Memory remains a dynamic learned layer and MUST NOT silently mutate stable Identity revisions.

#### Scenario: Read validated memory
- **WHEN** the user opens an identity's Content Memory tab
- **THEN** applicable validated memory entries and revision provenance are shown with scope origin and limitations

#### Scenario: Promote Identity learning
- **WHEN** an accepted identity-category LearningCandidate is promoted to memory
- **THEN** ContentMemory changes but Brand/Persona/Account/Series revisions remain unchanged until a separate explicit identity save
