## ADDED Requirements

### Requirement: Workflow Definition is Creation Recipe truth

The existing immutable Workflow Definition revision SHALL remain the only persisted process/recipe truth. Production MAY present a stage-oriented Creation Recipe view, but it MUST preserve the same Workflow ID/version/checksum, node/plugin config, mappings, dependencies and historical Run pinning.

#### Scenario: Switch from stage view to Advanced
- **WHEN** the user opens Advanced graph mode from a Creation Recipe
- **THEN** both views edit the same unsaved definition and one explicit save creates one normal Workflow revision

### Requirement: Stage-contract attempts freeze resolved inputs and receipts

WorkflowStepAttempt SHALL support bounded nullable resolved input snapshot and execution receipt for Stage Contract nodes. The receipt SHALL freeze exact definition/node/plugin/config/override/method/model/prompt/upstream/output-contract identities. Legacy attempts remain readable with these fields absent.

Explicit Stage run/rerun SHALL present an expected preview resolution hash and invocation idempotency key; automatic successors SHALL prepare/record a pure server resolution after acceptance and pass that exact expected hash to the same gate. The engine SHALL atomically claim the existing Step/Attempt and commit its exact immutable receipt/input before external dispatch, rejecting drift or competing request fingerprints. Identical retries reuse the original claim; possible-dispatch/unknown never becomes automatic resubmission. Sealed outputs and frozen receipts are not overwritten.

#### Scenario: Failed tuned attempt
- **WHEN** a tuned stage fails after resolution
- **THEN** the immutable failed attempt still records the exact resolved configuration/input receipt needed for later feedback

#### Scenario: Concurrent or response-loss stage retry
- **WHEN** two identical requests claim the same current stage invocation or the first response is lost
- **THEN** they share one durable invocation claim and no duplicate external dispatch or history overwrite occurs

### Requirement: Run-only stage overrides do not mutate saved definitions

Project-scoped Run/rerun MAY accept bounded node overrides only for fields declared tunable by the exact Stage Contract. The override SHALL be execution-local, hash-bound and persisted in the attempt receipt. It MUST NOT alter the pinned Workflow revision or scoped defaults.

#### Scenario: Rerun only one stage with a different model
- **WHEN** the selected Stage Contract allows model profile override
- **THEN** the new attempt uses and records that exact profile while the saved Project Workflow remains unchanged

### Requirement: Stage result review is distinct from Run execution

The Workflow UI SHALL expose immutable attempt candidates/results for review and explicit domain adoption. Running or succeeding a node MUST NOT automatically make its proposed content the current Master/Variant unless that node's existing authoritative domain contract explicitly creates that entity and the user completed its required acceptance.

Generation success SHALL NOT satisfy mandatory human review or Run completion. Dependencies that declare accepted content SHALL resolve exact accepted entity/hash/decision associations rather than raw successful proposal output. Accepted-with-edits input changes SHALL mark affected downstream results stale under existing rerun/stale mechanisms. After committed acceptance, dependency-ready stages SHALL automatically continue in deterministic visual-order tie-break order until required human review or a safety/failure/stale/unknown/unavailable blocker. Replay/recovery reuses existing invocation claims; no automatic adoption, professional dispatch, Candidate approval or publication is authorized. Legacy pinned workflows retain their original semantics; new contracts use new explicitly selected plugin versions.

#### Scenario: Successful Master proposal node
- **WHEN** the node attempt succeeds with proposal candidates
- **THEN** the attempt records success/output but current Content Master remains unchanged, required review stays unresolved and accepted-content dependencies do not advance until explicit adoption

#### Scenario: Human edits change the accepted upstream content
- **WHEN** a dependent result consumed an older accepted payload hash and explicit acceptance produces different content
- **THEN** its relevant downstream result/check is marked stale even if the original proposal hash did not change

### Requirement: Feedback promotion creates new Workflow versions

Applying an accepted run override/improvement to a Project or scoped default SHALL use the existing immutable Workflow save/default portability contracts and CAS. Historical runs/attempts retain their prior definition.

#### Scenario: Save successful override as Persona default
- **WHEN** portability succeeds and the binding revision is current
- **THEN** a new Persona × modality default Workflow version is created and existing Units remain pinned
