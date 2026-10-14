## ADDED Requirements

### Requirement: Brand constraints and Persona creative root remain separate

Brand SHALL supply Brand Voice, content boundaries, compliance/risk constraints and common factual policy, while Creative Profile defaults SHALL resolve from Persona → Account → Series only; Brand mutations that attempt `*_creative_profile` SHALL be rejected.

#### Scenario: Two Personas share one Brand but not creative defaults
- **GIVEN** an AI technology Persona and a lifestyle Persona share one Brand
- **WHEN** both create content
- **THEN** applicable brand constraints are respected
- **BUT** neither Persona acquires the other's Skills, Styles, Recipes or creative memories

#### Scenario: No account is required for new editorial Series
- **WHEN** an owner creates a Persona-owned editorial Series for content planning
- **THEN** no Account is required at Series creation or source Master planning
- **AND** legacy Account-Series rules continue to apply only in the legacy context

### Requirement: Explicit origin and destination identity in frozen records

The system SHALL record whether an Account selected for a Unit is an origin creative context or a target delivery account; historical IdentitySnapshot data SHALL remain interpretable under its original semantics.

#### Scenario: Target account differs from origin
- **WHEN** a modern Candidate is adapted for a destination Account different from a Unit's origin Account
- **THEN** provenance includes both source and target contexts
- **AND** the destination Account is not represented as the origin or vice versa
