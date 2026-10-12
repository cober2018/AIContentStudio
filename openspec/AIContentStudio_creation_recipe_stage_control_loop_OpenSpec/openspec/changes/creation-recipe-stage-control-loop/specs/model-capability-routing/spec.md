## ADDED Requirements

### Requirement: Stage model selection is exact and previewable

A prompt-bearing Stage Contract SHALL resolve an exact executable model profile/provider/model using the existing model capability registry/routing. Preview SHALL return that exact identity and availability without making a model call. Execution MUST fail on route drift instead of silently falling back.

#### Scenario: Stage pins a model profile
- **WHEN** the stage explicitly selects a registered profile
- **THEN** preview and execution bind the same provider/model/profile identity or execution is blocked

### Requirement: Stage prompt receipt binds model execution

For model-backed stage execution, the successful LLMRun/input hash SHALL correspond to the effective Stage resolution and prompt hash recorded in the WorkflowStepAttempt receipt. Raw provider output/errors remain governed by existing redaction/retention policy.

#### Scenario: Review model provenance
- **WHEN** a proposal is later adopted into a Master
- **THEN** its provenance can trace to the exact attempt receipt and verified LLMRun/model identity used to produce the proposal
