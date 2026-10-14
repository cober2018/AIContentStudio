## ADDED Requirements

### Requirement: Workflow Stage proposal may be explicitly adopted as a Master revision

The Content Master service SHALL provide a trusted Workflow Stage adoption path for an exact authorized current WorkflowStepAttempt proposal candidate. It SHALL validate the final payload and refs through the normal modality adapter/context/rights/evidence rules and create a new immutable Master revision only after explicit user acceptance.

The adopted revision SHALL freeze exact Workflow/Run/node/attempt/plugin/definition checksum, stage resolution/config/prompt/proposal hashes and safe model/method provenance. It MAY include bounded user edits and SHALL record proposal hash versus accepted payload hash.

The trusted adoption transaction SHALL enforce current source/attempt and relevant context-head/Master revision CAS at commit, and atomically persist the Master/refs, required accepted-output association and acceptance ProjectEvent. Existing standalone save behavior stays unchanged; the adoption path cannot commit Master first and associate/record feedback in a later transaction. An adoption key binds the exact proposal/receipt, final canonical payload/refs, decision and expected heads. Authorized identical committed retries return the original revision/association/feedback before fresh currentness checks; changed fingerprints conflict and concurrent duplicate adoption produces one revision only.

#### Scenario: Adopt an exact Text proposal
- **WHEN** a current Text stage proposal is selected and its run/context are still valid
- **THEN** a new text.master.v2 revision is appended and the prior Master remains unchanged

#### Scenario: Proposal source went stale
- **WHEN** Brief/Fact Boundary/Identity/current Master context changed after proposal generation
- **THEN** adoption fails with a stale/rebase reason and does not silently retarget the old proposal

#### Scenario: Atomic acceptance rollback
- **WHEN** association, feedback, refs or context-head validation fails during adoption
- **THEN** no new Master revision or partial accepted record is committed

#### Scenario: Replay an accepted proposal decision
- **WHEN** the identical authorized adoption is retried after that save changed the current Master
- **THEN** the original accepted result is returned without appending another Master or feedback event

### Requirement: Accepted stage Master becomes a verified workflow output

Workflow Stage adoption SHALL create ProjectWorkflowOutput kind `content_master_revision` in the same transaction, only for the exact same-unit Run/node/attempt and new Master. An adoption-specific association path SHALL verify original immutable proposal/output/receipt hashes, accepted Master provenance and exact acceptance decision. It MUST NOT require rewriting Step/Attempt proposal output to add the Master ID created later. The legacy produced-entity association path remains unchanged. A raw proposal/foreign Master ID MUST NOT create the association.

#### Scenario: Stage adoption output lineage
- **WHEN** Master adoption commits
- **THEN** project workflow output history can trace the accepted Master to the exact producing attempt without claiming the proposal itself was already authoritative

#### Scenario: Master ID did not exist during generation
- **WHEN** a later adoption creates the authoritative Master from a sealed proposal attempt
- **THEN** the trusted acceptance association verifies that lineage while the original Step/Attempt proposal output/hash/receipt remain unchanged
