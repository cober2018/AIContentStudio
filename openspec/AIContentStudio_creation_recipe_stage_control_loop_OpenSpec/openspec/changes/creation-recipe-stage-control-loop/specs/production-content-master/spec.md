## ADDED Requirements

### Requirement: Workflow Stage proposal may be explicitly adopted as a Master revision

The Content Master service SHALL provide a trusted Workflow Stage adoption path for an exact authorized current WorkflowStepAttempt proposal candidate. It SHALL validate the final payload and refs through the normal modality adapter/context/rights/evidence rules and create a new immutable Master revision only after explicit user acceptance.

The adopted revision SHALL freeze exact Workflow/Run/node/attempt/plugin/definition checksum, stage resolution/config/prompt/proposal hashes and safe model/method provenance. It MAY include bounded user edits and SHALL record proposal hash versus accepted payload hash.

#### Scenario: Adopt an exact Text proposal
- **WHEN** a current Text stage proposal is selected and its run/context are still valid
- **THEN** a new text.master.v2 revision is appended and the prior Master remains unchanged

#### Scenario: Proposal source went stale
- **WHEN** Brief/Fact Boundary/Identity/current Master context changed after proposal generation
- **THEN** adoption fails with a stale/rebase reason and does not silently retarget the old proposal

### Requirement: Accepted stage Master becomes a verified workflow output

After Workflow Stage adoption creates a Master, the system MAY create ProjectWorkflowOutput kind `content_master_revision` only for that exact same-unit Run/node/attempt and new Master. A raw proposal/foreign Master ID MUST NOT create the association.

#### Scenario: Stage adoption output lineage
- **WHEN** Master adoption commits
- **THEN** project workflow output history can trace the accepted Master to the exact producing attempt without claiming the proposal itself was already authoritative
