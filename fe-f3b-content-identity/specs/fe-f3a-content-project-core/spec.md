## MODIFIED Requirements

### Requirement: Aggregated project Versions view

The project Versions read model SHALL include real IdentitySnapshot records associated with project ContentUnits/Runs when present. It MUST NOT create synthetic snapshots for legacy units.

#### Scenario: IdentitySnapshot version item
- **WHEN** a project unit pins an IdentitySnapshot
- **THEN** Versions returns the snapshot ID/checksum and unit association as an immutable historical item

#### Scenario: Legacy identity version item
- **WHEN** a unit has no snapshot
- **THEN** Versions reports a legacy/unknown identity state without fabricating Brand/Persona/Account/Series revisions

### Requirement: Derived project Overview

The deterministic Overview SHALL include typed identity-readiness risk for active production units that require current identity context but do not have a usable IdentitySnapshot. Archived legacy units SHALL not block current project readiness.

#### Scenario: Identity not ready
- **WHEN** an active FE-F3B unit lacks a usable identity snapshot
- **THEN** Overview includes an `identity_unready` risk and a deterministic next action

### Requirement: Immutable CreativeBrief revisions

New CreativeBrief revisions MAY reference stable Brand/Persona/Account/Series IDs in identity scope. Those references SHALL be server-validated against ownership/hierarchy when saved. Historical Brief revisions MUST NOT be rewritten when identity hierarchy changes.

#### Scenario: Invalid identity scope
- **WHEN** a Brief revision references an identity outside the user's hierarchy
- **THEN** the save is rejected without changing prior Brief revisions
