## ADDED Requirements

### Requirement: Recipe media stages reuse existing native generation truth

A Creation Recipe media stage SHALL use existing ProviderGenerationTask/result acceptance and MaterialRevision truth. Its required Stage input snapshot, resolved configuration/provenance and execution receipt SHALL be frozen in the Workflow attempt under the common pre-dispatch claim contract; only additional non-authoritative display projections are optional. No duplicate media task/result entity is created.

#### Scenario: Image stage result
- **WHEN** a media stage produces provider candidates
- **THEN** the user accepts through the existing provider task contract and the resulting MaterialRevision remains unbound to Master until an explicit content save

### Requirement: Stage feedback may reference exact accepted material

Stage feedback MAY record an exact accepted/rejected MaterialRevision or ProviderGenerationTask result identity/hash for process improvement. Such feedback MUST NOT change material rights or publication eligibility.

#### Scenario: Record which provider result was chosen
- **WHEN** the user records feedback about an exact provider result or accepted MaterialRevision
- **THEN** the feedback preserves that identity/hash without changing material rights or publication eligibility
