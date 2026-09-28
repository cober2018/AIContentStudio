## MODIFIED Requirements

### Requirement: Versioned Brand / Persona / Account / Series hierarchy

Opportunity Assessment MAY recommend valid stable identity hierarchy entities, but recommendation SHALL NOT mutate identity revisions or create IdentitySnapshot.

#### Scenario: Recommended Persona/Account/Series
- **WHEN** an Assessment saves identity recommendations
- **THEN** hierarchy ownership is validated and identity remains unchanged

### Requirement: Identity and Content Memory remain separate

Opportunity relevance/recommendation SHALL NOT be treated as verified learning or written automatically into Content Memory.

#### Scenario: Later performance
- **WHEN** converted content later performs well
- **THEN** F5A makes no automatic Identity/Memory mutation; later LearningCandidate flow owns that decision
