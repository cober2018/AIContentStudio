## ADDED Requirements

### Requirement: Graphic v2 Review exposes frozen multi-canvas content
Project-first Review SHALL present Graphic v2 Candidate canvases in frozen order with visible text-layer changes, exact final image bindings, structured diff and current rights/check results. Approval and local delivery SHALL remain bound to the exact Candidate hash; delivery MUST NOT edit or reorder approved cards.

#### Scenario: Approve a multi-card Candidate
- **WHEN** an approver opens a valid Graphic v2 Candidate with two rendered canvases
- **THEN** Review shows both in frozen order and the authorized local package contains the same ordered image bytes and hashes

#### Scenario: Rights revoked after freeze
- **WHEN** a rendered or embedded MaterialRevision loses required public-use rights
- **THEN** approval/package is blocked while the immutable Candidate remains historically readable
