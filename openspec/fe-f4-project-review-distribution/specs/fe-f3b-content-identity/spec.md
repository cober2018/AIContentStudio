## MODIFIED Requirements

### Requirement: Immutable IdentitySnapshot
Project Candidate SHALL freeze the exact IdentitySnapshot ID/checksum used by its ContentUnit/WorkflowRun; approval/delivery shall not resolve latest identity.

### Requirement: Production identity context
Review SHALL show frozen Candidate identity and mark legacy candidates without IdentitySnapshot as legacy/unknown.
