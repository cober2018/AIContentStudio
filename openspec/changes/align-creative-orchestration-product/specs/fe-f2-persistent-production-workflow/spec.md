## ADDED Requirements

### Requirement: Production UI is content-first without changing Workflow truth

The default per-unit Production experience SHALL prioritize current Content Master, creative intent, exact assets, Channel Variants, native generation and Creative Execution. Workflow design, Node Inspector and detailed Run controls SHALL remain available through an explicit Advanced/Automation surface and SHALL retain all existing definition/run/version semantics.

#### Scenario: Open a normal content unit
- **WHEN** the user enters Production to continue writing/designing/directing
- **THEN** current content and next creative/execution actions are primary; hiding the workflow canvas does not create or alter a WorkflowRun

### Requirement: Creative Execution is not a WorkflowRun substitute

CreativeExecution MAY reference Project/Unit and source lineage but SHALL remain a separate professional-execution state machine. A CreativeExecution MUST NOT be fabricated as a WorkflowRun or make existing Workflow outputs current. Workflow nodes MAY later prepare/observe an execution only through explicit typed integration.

#### Scenario: Codex performs an external edit
- **WHEN** a CreativeExecution is completed outside the workflow engine
- **THEN** its state/result remain queryable without inventing WorkflowRun/StepAttempt lineage
