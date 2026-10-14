## Why

AIContentStudio now has strong individual capabilities: Project/Identity/Brief/Evidence, Content Master, Channel Variant, native ProviderGenerationTask, Creative Execution/MCP, Capability Memory, Candidate/Review/Delivery and a persistent Workflow engine. The product is still difficult to use end-to-end because these capabilities are not controlled through one understandable creation loop.

The current Workflow implementation can persist node order, plugin, JSON config, mappings, conditions, failure policy, model profile and project/default versions. However the product exposes that mostly as “Advanced Automation,” and several legacy/builtin executors do not consume all user-visible tuning fields as an execution contract. Workflow therefore behaves more like an execution-order graph than a controllable creative recipe. Content Master, Workflow outputs, native media, Creative Execution and Capability Memory remain individually correct but require users to mentally connect them.

The next product goal is to make the existing Workflow truth the operational backbone of creation without making the raw graph the daily UI. Users need to see a Creation Recipe made of understandable stages, open each stage, tune the exact prompt/method/model/inputs/parameters/gates, preview what the executor will actually receive, run the stage, review the exact result, explicitly adopt it into Master/Variant/Material, and promote what worked into the current Project recipe, Persona/Account/Series default, or Capability Memory.

Feedback must make the workflow better over time, but never through hidden self-modification. Accepted explicit tunable-field overrides may produce deterministic improvement patches; accepted-with-edits content and rejection feedback are evidence, not automatically inferred config changes. Without a config diff, the user must explicitly author/select an allowed instruction or method change. Applying an improvement always creates a new immutable Workflow definition revision or a Capability Memory candidate after human confirmation.

## What Changes

- Define **Creation Recipe** as the product-facing projection of the existing immutable Workflow Definition revision. No second Recipe table or workflow truth is introduced.
- Make the Creation Recipe stage strip/control drawer a first-class Production surface; the raw graph/JSON editor remains an Advanced view of the same definition.
- Extend node/plugin descriptors with a typed **Stage Contract**: tunable config schema, user-facing controls, input contract, output contract, executor/method support and preview capability. UI controls are allowed only when the executor actually consumes and freezes them.
- Add a server-side **Effective Stage Resolver** that deterministically combines the saved Workflow node, exact Capability Memory/Installed Skill selection, model route, Identity/Brief/Creative Intent/Fact Boundary context, upstream accepted outputs and bounded one-run overrides. A pure preview exposes the same resolved config/prompt/method/model hashes that execution must use.
- Introduce project-native stage executors for modern production rather than overloading legacy Draft-oriented `builtin.generate`. First required stages cover Master proposal, native media generation integration, channel adaptation integration, professional Creative Execution preparation and existing checks/human gates.
- Add run-only stage overrides for allowed tunable fields. A run/rerun freezes the effective stage configuration; it does not mutate the saved Workflow.
- Add an additive WorkflowStepAttempt execution receipt/input snapshot so historical attempts can explain exactly which configuration, prompt/method/model and upstream inputs produced the output. Legacy attempts remain valid with absent receipt.
- Define Stage Result Review. AI content stages produce bounded immutable candidate proposals inside the exact WorkflowStepAttempt. The user may accept, reject, retry, or accept with bounded edits. Acceptance is the only bridge from a proposal into a new ContentMasterRevision/ChannelVariantRevision/MaterialRevision or CreativeExecution preparation.
- After committed acceptance, automatically continue the next eligible Stage under exact prepared request/claim gates, stopping at the next required review/blocker; never auto-adopt the next result, dispatch professional tools, approve or publish.
- Extend ProjectWorkflowOutput only for actual persisted accepted entities; raw proposal candidates remain attempt outputs and never masquerade as Master/Variant/Material.
- Record explicit stage feedback as append-only ProjectEvent records bound to exact Workflow/Run/StepAttempt/config/output hashes. No duplicate feedback state table is introduced.
- Add deterministic **“Save what worked”** actions:
  - promote the successful run override to a new Project Workflow Override revision;
  - save the tuned portable definition as a new Persona/Account/Series × modality default;
  - capture the stage method/prompt as a Capability Memory candidate.
- Add bounded **Workflow Improvement Candidate** behavior using existing Capability Memory `recipe` / `prompt_skill` artifacts rather than a new improvement table. Improvement content freezes the base workflow checksum, node/plugin identity, allowed config patch, source feedback references and evidence hashes. It is never auto-applied.
- Add optional model-assisted tuning preview only after the deterministic feedback loop works. It may suggest changes only to Stage Contract tunable fields, records an LLMRun, and cannot change dependencies, plugin identity, evidence/rights gates, approval gates or side-effect policy.
- Make text, graphic and video creation share the same stage-control model:
  - text/master generation and revision;
  - image/video/audio material generation through existing ProviderGenerationTask;
  - video planning/Director Package and professional execution through existing Creative Execution;
  - Channel Variant adaptation through existing F6E truth;
  - final Candidate/Review/Delivery remain separate explicit gates.
- Preserve old Workflow definitions/runs, legacy Draft generation and advanced compatibility routes unchanged. New project Creation Recipes use project-native stage contracts; historical workflows are not silently upgraded.
- Before new business apply, verify/inherit the already completed prior R1/R2 corrections: approved schema/readiness/runbooks use `aco000000001` without JWT identity activation, and four permanent regression files contain 108 cases. Do not repeat them or silently close the prior align task 15.7 final review.

## Capabilities

### New Capabilities

- `creation-recipe-stage-control-loop`: product-facing recipe stages, typed stage contracts, effective-stage preview/execution identity, stage result review/adoption, explicit feedback and workflow-improvement promotion.

### Modified Capabilities

- `fe-f2-persistent-production-workflow`: Workflow Definition remains Recipe truth; add run-only overrides, frozen attempt receipts, stage-level review/control and promotion to project/default workflow revisions.
- `content-harness-registry`: node descriptors expose typed Stage Contracts and executors must consume/reject every exposed tuning field.
- `model-capability-routing`: stage model/profile selection and effective prompt/method preview are resolved server-side and frozen into execution receipts.
- `production-content-master`: accept exact Workflow Stage proposals into new Master revisions with frozen run/attempt/config/proposal provenance; never auto-mutate current Master.
- `capability-memory` (active align change dependency): reuse `recipe`/`prompt_skill` candidates for stage methods and workflow improvement; never become a second Workflow truth or auto-apply.
- `fe-f0-f1-project-experience`: Project Production presents Creation Recipe as the normal controllable creation journey and keeps raw automation advanced.
- `material-library-v1`: native media stage acceptance continues to use ProviderGenerationTask/MaterialRevision truth and exposes stage provenance without duplicating media.
- `fe-p1-frontend-bundle-performance`: typed stage controls and advanced graph remain lazily split; heavy modality editors and automation do not pollute unrelated routes.

## Impact

This change is intentionally built on the current implemented working tree for `align-creative-orchestration-product`; it does not rewrite that source package. Lifecycle order remains: reconcile/close the align change first when canonical synchronization is authorized, then synchronize this follow-up.

One additive migration is expected after the current `aco000000001` head to add bounded nullable `input_snapshot_json` and `execution_receipt_json` to `workflow_step_attempt`. No new Recipe/Feedback/Improvement business tables are planned. Stage feedback uses ProjectEvent; improvement candidates use Capability Memory; accepted entities use existing Master/Variant/Material/CreativeExecution truths.

No remote publication, professional-tool pilot, push, canonical sync/archive or destructive legacy deletion is authorized by this proposal.

2026-10-14 lifecycle clarification: the user now directs independent closeout of this Recipe change and Persona while preserving other active changes. Only this change’s ADDED delta requirements will synchronize; the previously implemented align dependency and its 15.7 gate remain separate and are not implicitly completed/archived. This supersedes the earlier lifecycle-order recommendation for these scoped local closeouts; it does not expand ACO implementation, push or publication authority.
