## ADDED Requirements

### Requirement: Accepted provider media remains an exact library revision
Provider search/generation/TTS/renderer output SHALL enter the existing Material/MaterialRevision truth only after explicit acceptance and byte, MIME, hash, provenance and rights/license validation. Unknown or revoked public-use rights MUST block public-ready project reuse; Project Shared Assets SHALL reference the exact revision without duplicating bytes or assigning false ownership.

#### Scenario: Unknown license
- **WHEN** a provider result has valid bytes but no proven public-use right
- **THEN** the revision remains not-public-ready and cannot satisfy Candidate or package media gates

#### Scenario: Cross-unit Project use
- **WHEN** a generated MaterialRevision is accepted and explicitly attached to a Project
- **THEN** authorized Units in that Project may reference the same revision subject to live rights, while the generating run/provenance remains inspectable
