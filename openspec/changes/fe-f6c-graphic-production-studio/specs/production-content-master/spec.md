## ADDED Requirements

### Requirement: Graphic v2 extends Production Core without reinterpreting v1
Production Core SHALL dispatch `graphic.master.v2` through its own schema adapter and explicit v1 fork while preserving historical `graphic.master.v1`, Text and Video behavior. It SHALL reuse append-only Master/ref/check storage and the existing v4 Candidate boundary.

#### Scenario: V2 Graphic Master save
- **WHEN** a valid Graphic v2 document and exact refs are submitted for the current Graphic Unit
- **THEN** a new revision is stored with current context and no existing v1 revision is rewritten

#### Scenario: Generic schema crossing
- **WHEN** a caller tries to save Graphic v2 over the current v1 Master through generic save
- **THEN** the server requires explicit upgrade and leaves history unchanged

### Requirement: Graphic v2 render coverage follows canonical canvas order
The existing input-bound final-render gate SHALL verify exact one-to-one canvas/output coverage and ordered package projection for Graphic v2, including live byte, MIME, hash and rights checks. Merely matching an unordered set of canvas IDs MUST NOT be sufficient to claim an ordered multi-card package.

#### Scenario: Out-of-order final outputs
- **WHEN** final image declarations contain all canvas IDs but in an order inconsistent with the canonical document
- **THEN** freeze/package rejects or deterministically reorders only when the frozen manifest itself records the canonical mapping; it MUST NOT silently publish a different sequence
