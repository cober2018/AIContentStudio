## MODIFIED Requirements

### Requirement: Stage attempts freeze exact execution receipts

Stage-contract WorkflowStepAttempt rows SHALL freeze bounded input snapshot and execution receipt including Workflow/node/plugin/config/method/model/prompt/upstream/output-contract hashes. Failed attempts SHALL also retain these snapshots. Historical legacy attempts without them remain valid/unknown.

The resolved stage and the frozen input snapshot SHALL be bounded at 512 KB canonical JSON, so a stage carrying an accepted Master, its methods and the project material catalog is not rejected. Execution receipts and stage outputs keep their own 128 KB bounds.

The receipt SHALL also bind the invocation fingerprint, expected preview hash and applicable routing-plan/adapter/runtime identities. Receipt/input are immutable from the pre-dispatch claim; the claimed attempt can seal its outcome/output once, but retries MUST NOT replace a historical receipt or sealed output.

#### Scenario: Compare two iterations
- **WHEN** two attempts used different temporary instructions
- **THEN** each historical attempt can explain its exact effective configuration and output without reading the current mutable step state

#### Scenario: Planning stage with a real Master
- **WHEN** a video work with an accepted Master of about 24 KB previews its script stage with four methods enabled
- **THEN** the preview is ready instead of failing with `stage_value_too_large`, and the input snapshot is frozen whole
