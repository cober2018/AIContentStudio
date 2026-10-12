## ADDED Requirements

### Requirement: External execution result is not a Candidate until explicitly incorporated

CreativeExecution `result_ready` or accepted MaterialRevision SHALL NOT appear as an approvable Content Candidate by itself. Review SHALL receive external-result provenance only after an authorized editor explicitly saves a new current Master/Variant that binds the accepted result and then freezes the normal v4/v5 Candidate.

#### Scenario: Review external MP4 before binding
- **WHEN** an external result is accepted to the material library but no new Video Master has been saved
- **THEN** `/review` does not offer Content Approval for that file as if it were a Candidate

### Requirement: Candidate manifests preserve accepted external execution provenance

When a Master/Variant uses a MaterialRevision accepted from CreativeExecution, the normal Candidate manifest SHALL freeze the exact revision/hash and safe external-execution source provenance already associated with the material/source revision. Review/Package MUST continue live rights/hash validation and MUST NOT need to call the external Agent/tool.

#### Scenario: Approved externally edited video
- **WHEN** a new Video Master binds an accepted external MP4 and freezes a v4 Candidate
- **THEN** Review/package can trace package→execution→accepted MaterialRevision while approval remains bound to the Candidate hash

### Requirement: Execution acceptance and Content Approval remain distinct decisions

The system MUST keep human acceptance of an external output (“this file may enter the library/use flow”), Content Approval (“this immutable Candidate is approved”), and Delivery Authorization/publication as separate decisions. No UI shortcut may collapse these audit facts into one state.

#### Scenario: Accept file but request content changes
- **WHEN** an editor accepts technically good image/audio/video bytes but later rejects the composed Candidate
- **THEN** the MaterialRevision remains valid historical material while Candidate Review records changes_requested
