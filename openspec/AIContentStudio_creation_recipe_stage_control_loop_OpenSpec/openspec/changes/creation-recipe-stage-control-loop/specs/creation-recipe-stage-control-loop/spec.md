## ADDED Requirements

### Requirement: Creation Recipe is the user-facing Workflow truth

The product SHALL present the selected effective immutable Workflow Definition revision as a Creation Recipe made of understandable stages. It MUST NOT create a second recipe persistence root or duplicate Workflow currentness. Every stage maps to one exact Workflow node/plugin/version and derives execution state from existing Run/Step/Attempt truth.

#### Scenario: Open a normal production unit
- **WHEN** a user opens an active Content Unit
- **THEN** Production shows the effective Creation Recipe, its inherited/default/project source and actionable stages without requiring the raw graph

### Requirement: Stage controls are typed and executor-backed

A stage shown in the normal Creation Recipe UI SHALL have a versioned Stage Contract declaring exactly which fields are tunable, how they are rendered, what inputs/outputs are expected and whether preview/override/candidates/human acceptance are supported. A visible tunable control MUST affect the server-resolved execution contract; unsupported or unconsumed fields MUST be rejected.

#### Scenario: Change a stage prompt
- **WHEN** the user edits a declared stage instruction field
- **THEN** the effective-config/prompt hash changes and the subsequent attempt receipt proves that exact instruction was used

#### Scenario: Cosmetic unsupported field
- **WHEN** a client submits a field not declared or consumed by the Stage Contract
- **THEN** validation fails instead of saving a setting that execution ignores

### Requirement: Effective Stage preview and execution share one resolver

The server SHALL deterministically resolve the saved node, allowed temporary override, exact method/skill/capability revision, model profile/provider/model, pinned Identity/Brief/Creative Intent/Fact Boundary context and declared upstream outputs into one canonical ResolvedStageExecution. Preview MUST make no external call. Actual execution MUST use the same resolution identity or fail stale/conflict.

#### Scenario: Model route changes after preview
- **WHEN** the selected model/profile becomes unavailable or resolves differently before run
- **THEN** execution fails visibly instead of silently using another model

### Requirement: Effective prompt is inspectable in layers

For a prompt-bearing stage, preview SHALL expose bounded safe prompt layers for method/base instruction, Identity, stage instruction, Brief, Creative Intent, evidence constraints, upstream output and current-task override, plus an effective prompt hash. Secrets and raw credential-bearing diagnostics MUST be absent.

#### Scenario: User reviews what AI will receive
- **WHEN** a stage is ready for model execution
- **THEN** the user can inspect the effective instruction layers and exact model/method identity before running

### Requirement: Run-only tuning is frozen but non-authoritative

The user MAY apply a temporary stage override only to Stage Contract tunable fields for one run/rerun. The override MUST be frozen in the resulting attempt receipt and MUST NOT mutate the saved Workflow Definition or scoped defaults. Plugin/dependency/gate/rights/approval/side-effect fields are not overridable.

#### Scenario: Try a different tone once
- **WHEN** the user changes only the stage instruction for a rerun
- **THEN** a new attempt freezes the override while later ordinary runs continue using the saved Recipe until the user explicitly promotes it

### Requirement: Stage attempts freeze exact execution receipts

Stage-contract WorkflowStepAttempt rows SHALL freeze bounded input snapshot and execution receipt including Workflow/node/plugin/config/method/model/prompt/upstream/output-contract hashes. Failed attempts SHALL also retain these snapshots. Historical legacy attempts without them remain valid/unknown.

#### Scenario: Compare two iterations
- **WHEN** two attempts used different temporary instructions
- **THEN** each historical attempt can explain its exact effective configuration and output without reading the current mutable step state

### Requirement: Project-native Master stages produce proposals, not Masters

The modern Content Master Creation Recipe SHALL use a project-native stage executor rather than silently changing legacy Draft-oriented generation semantics. A Master proposal stage SHALL return one or more bounded canonical modality-specific proposal candidates and MUST NOT persist ContentMasterRevision automatically.

#### Scenario: Generate three article drafts
- **WHEN** the Text stage is configured for three candidates
- **THEN** the attempt contains three hashed proposals and current Master remains unchanged until one is explicitly adopted

### Requirement: Explicit stage adoption creates authoritative content

An authorized user MAY accept one exact current stage proposal, optionally with bounded edits. Adoption SHALL validate exact Run/Attempt/candidate hashes and current project context, then create the normal authoritative Master/Variant/Material result through the existing domain service. Proposal review MUST NOT freeze Candidate, Approval or Delivery.

#### Scenario: Accept with edits
- **WHEN** the user edits an AI proposal before acceptance
- **THEN** the resulting Master revision records both the original proposal hash and final accepted hash plus exact stage provenance

### Requirement: Stage feedback is append-only evidence

Every explicit stage accept/accept-with-edits/reject/rerun decision SHALL record a bounded append-only ProjectEvent bound to exact Workflow/Run/Attempt/config/prompt/output hashes. Feedback MUST NOT change Workflow, Capability Memory, Identity, facts or defaults by itself.

#### Scenario: Reject a result
- **WHEN** the user rejects a proposal and records a short reason
- **THEN** the feedback remains tied to that exact attempt while the saved Recipe remains unchanged

### Requirement: Successful tuning can be promoted explicitly

The product SHALL offer a diff-based “Save what worked” action for accepted attempts that used temporary tuning. The user MAY explicitly create a new Project Workflow Override revision, a portable scoped default Workflow version, or a Capability Memory candidate. No promotion silently rebinds existing Units/Runs.

#### Scenario: Keep the improved Project prompt
- **WHEN** a run-only instruction produces an accepted result and the user chooses Save to Project
- **THEN** the server shows/applies the allowlisted node patch and creates a new immutable Project Workflow revision through existing CAS rules

### Requirement: Workflow improvement uses Capability Memory, not hidden workflow mutation

Reusable stage improvements SHALL be represented as non-authoritative Capability Memory `recipe`/`prompt_skill` candidates with frozen workflow/node/config/feedback provenance. Applying one requires explicit selection and creates a new Workflow revision. Usage/popularity cannot auto-apply it.

#### Scenario: Reuse a successful video-director method
- **WHEN** a saved recipe is applicable to another Video Unit
- **THEN** it is offered with exact scope/revision and only affects that Unit after the user explicitly applies or uses it

### Requirement: Text, Graphic and Video share the same control loop

Text, Graphic and Video Creation Recipes SHALL use the same stage-control/preview/run/review/feedback/promotion model while delegating authoritative outputs to their existing Master/Material/Variant/CreativeExecution domains.

#### Scenario: Professional video stage
- **WHEN** a Video recipe reaches professional execution
- **THEN** the stage prepares/projects existing CreativeExecution state and does not create a second external-execution truth or auto-dispatch a professional tool
