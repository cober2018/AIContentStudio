## MODIFIED Requirements

### Requirement: Freeze Candidate is separate from Content Approval

Project Candidate freeze SHALL support legacy Draft-backed manifest v3 and new ContentMasterRevision-backed manifest v4. Freeze MUST verify the selected source belongs to the requested Project/Unit, is current for its source model, and satisfies the relevant readiness/render gates. Freeze still creates no Content Approval or DeliveryTarget.

#### Scenario: Freeze Master Candidate
- **WHEN** an authorized editor freezes the current ready ContentMasterRevision
- **THEN** immutable manifest v4/Candidate hash are created without approval or delivery authorization

#### Scenario: Unsupported Master render
- **WHEN** the modality cannot produce a verified render snapshot
- **THEN** freeze fails closed and creates no Candidate

### Requirement: Project Candidate manifest v3

Historical v3 Candidates SHALL remain readable and hash-stable. F6A SHALL NOT rewrite them as v4 or fabricate ContentMasterRevision links.

#### Scenario: Read v3 after F6A
- **WHEN** a historical v3 Candidate is opened
- **THEN** its original Draft/workflow/evidence/identity manifest is returned unchanged

### Requirement: Candidate-bound Content Approval

Content Approval SHALL accept current valid v4 Candidates under the same exact Candidate ID/hash rule used by project Candidates. Approval MUST recheck live rights/evidence revocation and MUST NOT mutate the source ContentMasterRevision.

#### Scenario: Approve v4
- **WHEN** a reviewer approves a valid current v4 Candidate
- **THEN** Review binds the exact Candidate/hash and the Master revision remains unchanged

### Requirement: Project v3 manual package compatibility

Project local packaging SHALL continue to support valid v3 Candidates and SHALL additionally support v4 modality-aware packages. A v4 package MUST use its own manifest/render/assets and MUST NOT fall back to v3/v1 packaging.

#### Scenario: Graphic v4 copy package
- **WHEN** an approved graphic v4 Candidate has a verified final render image
- **THEN** the local package contains the exact render bytes and manifest without requiring Draft

#### Scenario: Video v4 package unavailable
- **WHEN** the v4 Candidate lacks verified packageable video bytes
- **THEN** packaging fails closed without a legacy fallback

### Requirement: Unit review workspace

Preview/Changes/Checks SHALL render v4 Text/Graphic/Video according to modality. Text similarity is optional for text and MUST NOT be fabricated for Graphic/Video.

#### Scenario: V4 modality review
- **WHEN** a reviewer opens a v4 Candidate
- **THEN** Review shows modality-appropriate preview/diff/check information from the frozen manifest
