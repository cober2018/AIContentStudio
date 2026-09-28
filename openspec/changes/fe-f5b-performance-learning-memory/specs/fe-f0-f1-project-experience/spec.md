## MODIFIED Requirements

### Requirement: Product shell
The frontend SHALL offer nine primary workspaces with navigable routes and loading, error, and empty views. Existing frontend pages SHALL remain reachable, using legacy aliases when a path is repurposed for a primary workspace. `/identities` SHALL load a persistent Content Identity workspace rather than a long-lived placeholder. `/review` SHALL load a persistent, project-first Review & Distribution workspace rather than a placeholder; `/review-publish` SHALL remain available for legacy Topic workflows.

#### Scenario: Browse primary navigation
- **WHEN** the user opens the application shell
- **THEN** nine primary workspaces are visible and each link resolves to a page or scoped placeholder

#### Scenario: Open identities
- **WHEN** the user opens `/identities`
- **THEN** the application loads backend Brand/Persona/Account/Series state and does not substitute browser fixture identity data

#### Scenario: Open project review
- **WHEN** the user opens `/review`
- **THEN** the workspace loads authorized ContentProjects and ContentUnits from backend state, not browser fixtures or a placeholder

`/home` and `/opportunities` SHALL be real persistent workspaces. Opportunity detail SHALL be addressable at `/opportunities/:id`.

#### Scenario: Open Home
- **WHEN** the user opens `/home`
- **THEN** backend Opportunity/Project/decision projections load with truthful loading/error/empty states

#### Scenario: Open Opportunities
- **WHEN** the user opens `/opportunities`
- **THEN** persisted Opportunity state loads without browser fixture substitution

`/learning` SHALL be a real persistent workspace rather than a placeholder and SHALL preserve FE-P1 lazy route boundaries.

#### Scenario: Open Learning
- **WHEN** the user opens `/learning`
- **THEN** Historical Recovery, Long-term Analysis, Learning Candidates and Content Memory views load from backend state without browser fixture substitution
