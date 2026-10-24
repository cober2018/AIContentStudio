## MODIFIED Requirements

### Requirement: Immutable CreativeBrief revisions

The system SHALL persist CreativeBrief as append-only revisions owned by one ContentProject. Each committed revision SHALL include objective, primary audience, core message, angle, required evidence, content constraints, identity scope, modality scope, channel scope, CTA, references, checksum, author and creation time. Saving a Brief SHALL create a new revision; a prior revision MUST NOT be mutated. New CreativeBrief revisions MAY reference stable Brand/Persona/Account/Series IDs in identity scope. Those typed references SHALL be server-validated against ownership/hierarchy when saved. Historical Brief revisions MUST NOT be rewritten when identity hierarchy changes.

#### Scenario: Save next Brief revision
- **WHEN** an editor saves a valid Brief with `expected_revision` equal to the current revision
- **THEN** the backend creates revision N+1, returns its checksum, keeps revision N readable, and records `brief.revision_created`

#### Scenario: Reject stale Brief save
- **WHEN** another editor has already created a newer Brief revision
- **THEN** the stale save returns 409 and creates neither a new revision nor a project event

#### Scenario: Concurrent Brief saves
- **WHEN** two saves both target the same current revision and race at the database constraint
- **THEN** at most one new revision and its event commit; the other request returns 409 without a partial event

#### Scenario: Reload Brief
- **WHEN** the user reloads the project
- **THEN** the Brief tab shows the latest committed revision and its prior revisions from backend state

#### Scenario: Invalid identity scope
- **WHEN** a Brief revision references an identity outside the user's hierarchy
- **THEN** the save is rejected without changing prior Brief revisions

Opportunity conversion MAY create CreativeBrief revision 1 from the selected Assessment and explicit user overrides. When created, it SHALL become a normal immutable Brief revision.

#### Scenario: Prefilled Brief
- **WHEN** conversion creates Brief v1
- **THEN** recommendations are copied as editable project inputs and later Opportunity changes do not rewrite the Brief

CreativeBrief MAY include nullable structured product_context for product-driven creation. The context SHALL contain the selected product identity and relevant variant, sourced claims with confirmation status, permitted selling points and excluded claims, and price/offer/time snapshots only when used by the requested content. Sources and materials SHALL reference the existing source evidence and exact material revisions. Audience, Persona, channel, modality and CTA SHALL reuse the existing Brief fields. Product input SHALL NOT implicitly confirm facts or bind a Fact Boundary.

Non-empty product_context SHALL participate in Brief validation, serialization and checksum. Absent/null context SHALL preserve the legacy checksum calculation; existing revisions and checksums MUST NOT be rewritten. Product changes SHALL create a normal next revision under the existing concurrency rules. Preview and generation SHALL use the same frozen Brief/product, Persona, evidence and material inputs. Changes to the current product Brief SHALL invalidate dependent pending results through the shared stale-input mechanism without overwriting accepted or historical artifacts.

#### Scenario: Save and reload product inputs
- **WHEN** a user saves a valid product Brief and reloads the project
- **THEN** the same structured product facts, confirmation states and evidence/material references are returned with the committed revision and checksum

#### Scenario: Update product variant or price
- **WHEN** an editor changes a product variant or a price used in the content
- **THEN** a new Brief revision and checksum are created, dependent pending results are marked stale, and old revisions and accepted artifacts remain readable and unchanged

#### Scenario: Legacy project without a product
- **WHEN** an existing ordinary project is read or saves a Brief without product context
- **THEN** the existing ordinary Brief behavior and absent-context checksum algorithm remain valid without product backfill

#### Scenario: Preview and generation freeze the same product
- **WHEN** preview and generation are prepared from the same committed Brief revision
- **THEN** both consume the same product context and exact evidence/material references, and a later webpage or Brief change cannot silently alter the frozen run
